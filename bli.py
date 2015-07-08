#!/usr/bin/env python
import os
import sys
import paramiko
#import logging

# defaults
sensor_file = "sensor.csv"
sshuser = "broadmin"
prefix = "/opt/bro"
spooltmp = "/data/bro/spool/tmp"
policy = "phys"
#logging.basicConfig()

def print_usage():
	print "Usage: bli.py [OPTION]"
	print "Options:"
	print "  {0:20s} print downstream health".format("status")
	print "  {0:20s} clear crash logs".format("clear_logs")
	print "  {0:20s} compare policy".format("compare_policy")
	print "  {0:20s} give this help list".format("-?, --help")

def menu():
	print
	print "-"*30
	print "|{0:^28s}|".format("Brommand Line Interface")
	print "-"*30
	print "|{0:28s}|".format(" (0) Get status")
	print "|{0:28s}|".format(" (1) Print status")
	print "|{0:28s}|".format(" (2) Clear crash logs")
	print "|{0:28s}|".format(" (9) Quit")
	print "-"*30

def get_sensors(sensors):
	sensor_list = open(sensor_file, "r")

	for line in sensor_list:
		populate_sensors(line, sensors)

def populate_sensors(line, sensors):
	if line:
		temp = line.split(",")

		if temp[0][0] != "#":
			temp[-1] = temp[-1].strip()
			sensors[temp[0]] = {}
			sensors[temp[0]]['hostname'] = temp[1]
			sensors[temp[0]]['crashlogs'] = 0
			sensors[temp[0]]['policyfile'] = {}

			if temp[2]:
				sensors[temp[0]]['sshuser'] = temp[2]
			else:
				sensors[temp[0]]['sshuser'] = sshuser

			if temp[3]:
				sensors[temp[0]]['prefix'] = temp[3]
			else:
				sensors[temp[0]]['prefix'] = prefix

			if temp[4]:
				sensors[temp[0]]['spooltmp'] = temp[4]
			else:
				sensors[temp[0]]['spooltmp'] = spooltmp

			if temp[5]:
				sensors[temp[0]]['policy'] = temp[5]
			else:
				sensors[temp[0]]['policy'] = policy

def get_status(sensors):
	for ip in sensors:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		try:
			ssh.connect(
				ip,
				username = sensors[ip]['sshuser'],
				key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
				timeout = 10
			)
			lines = running = stopped = crashed = warnings = fnf_prefix = fnf_spool = 0

			(stdin, stdout, stderr) = ssh.exec_command("ls " + sensors[ip]['spooltmp'] + "|grep crash |wc -l")
			for line in stderr.readlines():
				if "No such file" in line:
					fnf_spool = 1
			if not fnf_spool:
				sensors[ip]['crashlogs'] = int(stdout.readline().strip())

			(stdin, stdout, stderr) = ssh.exec_command(os.path.join(sensors[ip]['prefix'], "bin", "broctl") + " status 2>&1")
			for line in stdout.readlines():
				if "warning" in line:
					warnings += 1
				if "No such file" in line:
					fnf_prefix = 1
				if "manager" in line or "proxy" in line or "worker" in line or "standalone" in line:
					lines += 1
					if "running" in line:
						running += 1
					elif "stopped" in line:
						stopped += 1
					elif "crashed" in line:
						crashed += 1

			(stdin, stdout, stderr) = ssh.exec_command("find " + os.path.join(sensors[ip]['prefix'], "share/bro/site/* -exec md5sum '{}' \;"))
			for line in stdout.readlines():
				line = line.strip().split()
				line[1] = line[1].split("/")
				sensors[ip]['policyfile'][line[1][-1]] = line[0]

			if not fnf_prefix and not fnf_spool:
				if running == lines:
					sensors[ip]['status'] = "OK (" + 	str(warnings) + " warnings, " + 	str(sensors[ip]['crashlogs']) + " crash logs)"
				else:
					sensors[ip]['status'] = "Unhealthy (" + 	str(running) + " running, " + str(stopped) + " stopped, " + str(crashed) + " crashed, " + str(warnings) + " warnings, " + str(sensors[ip]['crashlogs']) + " crash logs)"
			elif fnf_prefix and not fnf_spool:
				sensors[ip]['status'] = "Error (broctl not found; validate prefix setting)"
			elif fnf_spool and not fnf_prefix:
				sensors[ip]['status'] = "Error (Bro spool not found; validate spooltmp setting)"
			elif fnf_prefix and fnf_spool:
				sensors[ip]['status'] = "Error (broctl and spool not found; validate path settings)"
			ssh.close()
		except Exception as e:
			sensors[ip]['status'] = e

	print "\nStatus loaded..."
	return 1

def print_status(sensors):
	print "\n{0:15s} : {1:20s} : {2:10s} : {3:20s} : {4:20s} : {5:6s} : {6}".format("IP Address", "Hostname", "User", "Prefix", "SpoolTmp", "Policy", "Status")
	print "-"*120

	for ip in sensors:
		print "{0:15s} : {1:20s} : {2:10s} : {3:20s} : {4:20s} : {5:6s} : {6}".format(ip, sensors[ip]['hostname'], sensors[ip]['sshuser'], sensors[ip]['prefix'], sensors[ip]['spooltmp'], sensors[ip]['policy'], sensors[ip]['status'])

def clear_logs(sensors):
	cleared = 0

	for ip in sensors:
		if sensors[ip]['crashlogs'] > 0:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

			try:
				ssh.connect(
					ip,
					username = sensors[ip]['sshuser'],
					key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
					timeout = 10
				)
				(stdin, stdout, stderr) = ssh.exec_command("rm -rf " + sensors[ip]['spooltmp'] + "/*crash")
				ssh.close()
				cleared += 1
				print "\nLogs cleared from", ip, "..."
			except Exception as e:
				sensors[ip]['status'] = e

	if cleared == 0:
		print "\nNo log(s) cleared..."

def compare_policy(sensors):
	print "\n[policy comparison not implemented]"

def main():
	sensors = {}
	get_sensors(sensors)
	loaded = decision = 0

	if len(sys.argv) == 1:
		while decision != 9:
			menu()

			try:
				decision = input("\naction> ")
			except Exception as e:
				decision = 666

			if decision == 0:
				loaded = get_status(sensors)
				raw_input("\n<Press Enter to continue>")
			elif decision == 9:
				print "\nExiting..."
			else:
				if loaded:
					if decision == 1:
						print_status(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 2:
						clear_logs(sensors)
						raw_input("\n<Press Enter to continue>")
				else:
					print "\nStatus not yet loaded (get status)"

	elif len(sys.argv) == 2:
		if sys.argv[1] == "status":
			get_status(sensors)
			print_status(sensors)
		elif sys.argv[1] == "clear_logs":
			get_status(sensors)
			clear_logs(sensors)
		elif sys.argv[1] == "compare_policy":
			get_status(sensors)
			compare_policy(sensors)
		elif sys.argv[1] == "-?" or sys.argv[1] == "--help":
			print_usage()
		else:
			print sys.argv[0] + ": invalid option:", sys.argv[1]
			print "Try '" + sys.argv[0] + " --help' for more information."

	else:
		print sys.argv[0] + ": too many arguments"
		print "Try '" + sys.argv[0] + " --help' for more information."

######
main()
