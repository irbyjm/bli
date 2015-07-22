#!/usr/bin/env python
import os
import sys
import paramiko
import subprocess

# definitions
bli_path = "/".join(sys.argv[0].split("/")[0:-1])
policies = ["phys"]

# defaults
sensor_file = "sensor.csv"
ssh_user    = "broadmin"
prefix      = "/opt/bro"
spooltmp    = "/data/bro/spool/tmp"
policy_type = "phys"

def print_usage():
	print "Usage: bli.py [OPTION]"
	print "Options:"
	print "  {0:20s} print downstream health".format("status")
	print "  {0:20s} print downstream config".format("config")
	print "  {0:20s} clear crash logs".format("clear_logs")
	print "  {0:20s} check policy".format("check_policy")
	print "  {0:20s} give this help list".format("-?, --help")

def menu():
	print "\n", "-"*30
	print "|{0:^28s}|".format("Brommand Line Interface")
	print "-"*30
	print "|{0:28s}|".format(" (1) Get status")
	print "|{0:28s}|".format(" (2) Print status")
	print "|{0:28s}|".format(" (3) Clear crash logs")
	print "|{0:28s}|".format(" (4) Check policy")
	print "|{0:28s}|".format(" (9) Print configuration")
	print "|{0:28s}|".format(" (0) Quit")
	print "-"*30

def get_sensors(sensors):
	sensor_list = open(os.path.join(bli_path, sensor_file), "r")

	for sensor in sensor_list:
		populate_sensors(sensor, sensors)

def populate_sensors(sensor, sensors):
	if sensor:
		line = sensor.split(",")

		if line[0][0] != "#":
			line[-1] = line[-1].strip()
			sensors[line[0]] = {}
			sensors[line[0]]['crashlogs']   = 0
			sensors[line[0]]['policy_file'] = {}
			sensors[line[0]]['hostname']    = line[1]
			sensors[line[0]]['ssh_user']    = line[2] if line[2] else ssh_user
			sensors[line[0]]['prefix']      = line[3] if line[3] else prefix
			sensors[line[0]]['spooltmp']    = line[4] if line[4] else spooltmp
			sensors[line[0]]['policy_type'] = line[5] if line[5] else policy_type

def print_config(sensors):
	print "\n{0:15s} : {1:20s} : {2:10s} : {3:20s} : {4:20s} : {5}".format("IP Address", "Hostname", "User", "Prefix", "SpoolTmp", "Policy")
	print "-"*120

	for sensor in sorted(sensors):
		print "{0:15s} : {1:20s} : {2:10s} : {3:20s} : {4:20s} : {5}".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['ssh_user'], sensors[sensor]['prefix'], sensors[sensor]['spooltmp'], sensors[sensor]['policy_type'])

def get_status(sensors):
	for sensor in sensors:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		try:
			ssh.connect(
				sensor,
				username = sensors[sensor]['ssh_user'],
				key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
				timeout = 10
			)
			lines = running = stopped = crashed = warnings = fnf_prefix = fnf_spool = 0

			(stdin, stdout, stderr) = ssh.exec_command("ls " + sensors[sensor]['spooltmp'] + "|grep crash |wc -l")
			for line in stderr.readlines():
				if "No such file" in line:
					fnf_spool = 1
			if not fnf_spool:
				sensors[sensor]['crashlogs'] = int(stdout.readline().strip())

			(stdin, stdout, stderr) = ssh.exec_command(os.path.join(sensors[sensor]['prefix'], "bin", "broctl") + " status 2>&1")
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

			(stdin, stdout, stderr) = ssh.exec_command("find " +  os.path.join(sensors[sensor]['prefix'], "share", "bro", "site", "*") + " -exec md5sum '{}' \;")
			for line in stdout.readlines():
				line = line.strip().split()
				line[1] = line[1].split(os.path.join(sensors[sensor]['prefix'], "share", "bro", "site/"))
				sensors[sensor]['policy_file'][line[1][-1]] = line[0]

			if not fnf_prefix and not fnf_spool:
				if running == lines:
					sensors[sensor]['status'] = "OK (" + str(warnings) + " warnings, " + str(sensors[sensor]['crashlogs']) + " crash logs)"
				else:
					sensors[sensor]['status'] = "Unhealthy (" + str(running) + " running, " + str(stopped) + " stopped, " + str(crashed) + " crashed, " + str(warnings) + " warnings, " + str(sensors[sensor]['crashlogs']) + " crash logs)"
			elif fnf_prefix and not fnf_spool:
				sensors[sensor]['status'] = "Error (broctl not found; validate prefix setting)"
			elif fnf_spool and not fnf_prefix:
				sensors[sensor]['status'] = "Error (Bro spool not found; validate spooltmp setting)"
			elif fnf_prefix and fnf_spool:
				sensors[sensor]['status'] = "Error (broctl and spool not found; validate path settings)"
			ssh.close()
		except Exception as e:
			sensors[sensor]['status'] = "Error (" + str(e) + ")"

	print "\nStatus loaded..."
	return 1

def print_status(sensors):
	print "\n{0:15s} : {1:20s} : {2}".format("IP Address", "Hostname", "Status")
	print "-"*120

	for sensor in sorted(sensors):
		print "{0:15s} : {1:20s} : {2}".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['status'])

def clear_logs(sensors):
	cleared = 0

	for sensor in sensors:
		if sensors[sensor]['crashlogs'] > 0:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

			try:
				ssh.connect(
					sensor,
					username = sensors[sensor]['ssh_user'],
					key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
					timeout = 10
				)
				(stdin, stdout, stderr) = ssh.exec_command("rm -rf " + sensors[sensor]['spooltmp'] + "/*crash")
				ssh.close()
				cleared += 1
				print "\nLogs cleared from", sensor, "..."
			except Exception as e:
				sensors[sensor]['status'] = "Error (" + str(e) + ")"

	if cleared == 0:
		print "\nNo log(s) cleared..."

def check_policy(sensors):
	policy = {}
	for pol in policies:
		policy[pol] = {}
		stdout = subprocess.Popen(
			["find", os.path.join(bli_path, "deploy", pol, "site"), "-exec", "md5sum", "{}", ";"],
			stdout = subprocess.PIPE,
			stderr = subprocess.STDOUT,
			universal_newlines = True
			).stdout

		for line in stdout.readlines():
			line = line.strip().split()
			if len(line) == 2:
				line[1] = line[1].split(os.path.join(bli_path, "deploy", pol, "site/"))[1]
				policy[pol][line[1]] = line[0]

		print "\n{0:15s} : {1:20s} : {2:6s} : {3:8s} : {4}".format("IP Address", "Hostname", "Policy", "Issue", "File")
		print "-"*120

		for sensor in sorted(sensors):
			if "Error" not in sensors[sensor]['status']:
				print "{0:15s} : {1:20s} : {2:6s} : {3:8s} :".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['policy_type'], "")
				for policy_file in policy[sensors[sensor]['policy_type']]:
					if policy_file in sensors[sensor]['policy_file']:
						if policy[sensors[sensor]['policy_type']][policy_file] != sensors[sensor]['policy_file'][policy_file]:
							print "{0:15s} : {1:20s} : {2:7s}: {3:8s} : {4} ".format("", "", "", "modified", policy_file)
					else:
						print "{0:15s} : {1:20s} : {2:7s} : {3:8s} : {4} ".format("", "", "", "missing", policy_file)

def main():
	loaded = decision = None
	sensors = {}
	get_sensors(sensors)

	if len(sys.argv) == 1:
		while decision != 0:
			menu()

			try:
				decision = input("\naction> ")
			except Exception as e:
				decision = None

			if decision == 1:
				loaded = get_status(sensors)
				raw_input("\n<Press Enter to continue>")
			elif decision == 9:
				print_config(sensors)
				raw_input("\n<Press Enter to continue>")
			elif decision == 0:
				print "\nExiting..."
			else:
				if loaded:
					if decision == 2:
						print_status(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 3:
						clear_logs(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 4:
						check_policy(sensors)
						raw_input("\n<Press Enter to continue>")
				else:
					print "\nStatus not yet loaded (get status)"

	elif len(sys.argv) == 2:
		if sys.argv[1] == "status":
			get_status(sensors)
			print_status(sensors)
		elif sys.argv[1] == "config":
			print_config(sensors)
		elif sys.argv[1] == "clear_logs":
			get_status(sensors)
			clear_logs(sensors)
		elif sys.argv[1] == "check_policy":
			get_status(sensors)
			check_policy(sensors)
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
