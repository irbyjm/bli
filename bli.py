#!/usr/bin/env python
import os
import sys
import paramiko
import subprocess

# definitions
bli_path = "/".join(sys.argv[0].split("/")[0:-1])
policies = ["phys-int", "phys-dist", "virt-hub", "virt-post", "devel"]

# defaults
sensor_file = "sensor.csv"
ssh_user    = "broadmin"
prefix      = "/opt/bro"
spooltmp    = "/data/bro/spool/tmp"
policy_type = "virt-post"

def print_usage():
	print "Usage: bli.py [OPTION]"
	print "Options:"
	print "  {0:20s} print downstream health".format("status")
	print "  {0:20s} print downstream config".format("config")
	print "  {0:20s} print downstream info (version, et al.)".format("info")
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
	print "|{0:28s}|".format(" (8) Print information")
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
			sensors[line[0]] 		= {}
			sensors[line[0]]['crash_logs']  = 0
			sensors[line[0]]['policy_file'] = {}
			sensors[line[0]]['version']	= {}
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
			lines = running = stopped = crashed = warnings = 0
			fnf_prefix = fnf_spool = False

			(stdin, stdout, stderr) = ssh.exec_command("ls " + sensors[sensor]['spooltmp'] + "|grep crash |wc -l")
			for line in stderr.readlines():
				if "No such file" in line:
					fnf_spool = True
			if fnf_spool == False:
				sensors[sensor]['crash_logs'] = int(stdout.readline().strip())

			(stdin, stdout, stderr) = ssh.exec_command(os.path.join(sensors[sensor]['prefix'], "bin", "broctl") + " status 2>&1")
			for line in stdout.readlines():
				if "warning" in line:
					warnings += 1
				if "No such file" in line:
					fnf_prefix = True
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
				line = line.strip().split(' ', 1)
				line[1] = line[1].split(os.path.join(sensors[sensor]['prefix'], "share", "bro", "site/"))
				sensors[sensor]['policy_file'][line[1][-1]] = line[0]

			(stdin, stdout, stderr) = ssh.exec_command(os.path.join(sensors[sensor]['prefix'], "bin", "bro") + " --version 2>&1; " + os.path.join(sensors[sensor]['prefix'], "bin", "broctl") + " help |grep -i version 2>&1")
			sensors[sensor]['version']['bro'] = stdout.readline().strip().split(' ')[-1]
			sensors[sensor]['version']['broctl'] = stdout.readline().strip().split(' ')[-1]

			if fnf_prefix == False and fnf_spool == False:
				if running == lines:
					sensors[sensor]['status'] = "ok (" + str(warnings) + " warnings, " + str(sensors[sensor]['crash_logs']) + " crash logs)"
				else:
					sensors[sensor]['status'] = "unhealthy (" + str(running) + " running, " + str(stopped) + " stopped, " + str(crashed) + " crashed, " + str(warnings) + " warnings, " + str(sensors[sensor]['crash_logs']) + " crash logs)"
			elif fnf_prefix == True and fnf_spool == False:
				sensors[sensor]['status'] = "error (broctl not found; validate prefix setting)"
			elif fnf_spool == True and fnf_prefix == False:
				sensors[sensor]['status'] = "error (Bro spool not found; validate spooltmp setting)"
			elif fnf_prefix == True and fnf_spool == True:
				sensors[sensor]['status'] = "error (broctl and spool not found; validate path settings)"
			ssh.close()
		except Exception as e:
			if "invalid literal for int()" in str(e):
				sensors[sensor]['status'] = "warning (password expired)"
			else:
				sensors[sensor]['status'] = "error (" + str(e) + ")"

	print "\nStatus loaded..."
	return True

def print_status(sensors):
	print "\n{0:15s} : {1:20s} : {2}".format("IP Address", "Hostname", "Status")
	print "-"*120

	for sensor in sorted(sensors):
		print "{0:15s} : {1:20s} : {2}".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['status'])

def clear_logs(sensors):
	cleared = 0
	purge = False

	for sensor in sorted(sensors):
		decision = None
		if sensors[sensor]['crash_logs'] > 0:
			if purge != True:
				decision = raw_input("\nClear logs from "+sensor+"? ([y]es] / [n]o / [a]ll) ")
				if decision == "a":
					purge = True

			if purge == True or decision == "y":
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
					print "\nLogs cleared from", sensor + "..."
				except Exception as e:
					sensors[sensor]['status'] = "error (" + str(e) + ")"
			elif decision == "n":
				print "\nSkipping", sensor+"..."

	if cleared == 0:
		print "\nNo logs cleared."

def check_policy(sensors):
	stdout = subprocess.Popen(
		["find", os.path.join(bli_path, "deploy")],
		stdout = subprocess.PIPE,
		stderr = subprocess.STDOUT,
		universal_newlines = True
		).stdout

	dnf = False
	for line in stdout.readlines():
		if "No such file" in line:
			dnf = True

	if dnf == False:
		policy = {}
		for pol in policies:
			policy[pol] = {}
			policy[pol]['error'] = False
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
				else:
					if "No such file" in ' '.join(line):
						policy[pol]['error'] = True

		print "\n{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4}".format("IP Address", "Hostname", "Policy", "Issue", "File/Details")
		print "-"*120

		for sensor in sorted(sensors):
			first_print = True
			if "error" not in sensors[sensor]['status'] and "warning " not in sensors[sensor]['status']:
				print "{0:15s} : {1:20s} : {2:9s} :".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['policy_type']),

				if policy[sensors[sensor]['policy_type']]['error'] == False:
					if sensors[sensor]['policy_type'] in policies:
						for policy_file in policy[sensors[sensor]['policy_type']]:
							if policy_file in sensors[sensor]['policy_file']:
								if policy[sensors[sensor]['policy_type']][policy_file] != sensors[sensor]['policy_file'][policy_file]:
									if first_print == False:
										print "{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4} ".format("", "", "", "modified", policy_file)
									else:
										print "{0:8s} : {1}".format("modified", policy_file)
										first_print = False
							else:
								if policy_file != "error":
									if first_print == False:
										print "{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4} ".format("", "", "", "missing", policy_file)
									else:
										print "{0:8s} : {1}".format("missing", policy_file)
										first_print = False
						for external_file in sensors[sensor]['policy_file']:
							if external_file not in policy[sensors[sensor]['policy_type']]:
								if first_print == False:
									print "{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4} ".format("", "", "", "extra", external_file)
								else:
									print "{0:8s} : {1}".format("extra", external_file)
									first_print = False

					else:
						print "{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4} ".format("", "", "", "error", "policy '"+sensors[sensor]['policy_type']+"' not defined in bli configuration")
						first_print = False
				else:
					print "{0:8s} : {1} ".format("warning", "deployment information for policy '"+sensors[sensor]['policy_type']+"' does not exist")
					first_print = False
			else:
				print "{0:15s} : {1:20s} : {2:9s} : {3:8s} : {4}".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['policy_type'], "--", "--")
				first_print = False

			if first_print == True:
				print "{0:8s} : {1}".format("ok", "")
	else:
		print "\nPolicy validation unavailable due to lack of deployment data"

def print_info(sensors):
	print "\n{0:15s} : {1:20s} : {2:11s} : {3:10s}".format("IP Address", "Hostname", "Bro Version", "Broctl Version")
	print "-"*120

	for sensor in sorted(sensors):
		if "error" not in sensors[sensor]['status'] and "warning " not in sensors[sensor]['status']:
			print "{0:15s} : {1:20s} : {2:11s} : {3:10s}".format(sensor, sensors[sensor]['hostname'], sensors[sensor]['version']['bro'], sensors[sensor]['version']['broctl'])
		else:
			print "{0:15s} : {1:20s} : {2:11s} : {3:10s}".format(sensor, sensors[sensor]['hostname'], "--", "--")

def main():
	loaded = decision = None
	sensors = {}
	get_sensors(sensors)

	if len(sys.argv) == 1:
		while decision != 0:
			menu()

			try:
				decision = int(raw_input("\naction> "))
			except Exception as e:
				decision = None

			if decision == 1:
				if loaded == True:
					repull = raw_input("\nPurge current sensor data? ([y]es] / [n]o)")
					if repull == "y":
						get_sensors(sensors)
						get_status(sensors)
				else:
					loaded = get_status(sensors)
				raw_input("\n<Press Enter to continue>")
			elif decision == 9:
				print_config(sensors)
				raw_input("\n<Press Enter to continue>")
			elif decision == 0:
				print "\nExiting..."
			else:
				if loaded == True:
					if decision == 2:
						print_status(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 3:
						clear_logs(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 4:
						check_policy(sensors)
						raw_input("\n<Press Enter to continue>")
					elif decision == 8:
						print_info(sensors)
						raw_input("\n<Press Enter to continue>")
				else:
					print "\nStatus not yet loaded (get status)"

	elif len(sys.argv) == 2:
		if sys.argv[1] == "status":
			get_status(sensors)
			print_status(sensors)
		elif sys.argv[1] == "config":
			print_config(sensors)
		elif sys.argv[1] == "info":
			get_status(sensors)
			print_info(sensors)
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
