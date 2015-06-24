#!/usr/bin/env python
# Brommand Line Interface (20150623 : irbyjm)
# "Quick-and-dirty" manager for remote Bro instances

import paramiko
import os

sshuser = "irbyjm"
sensor_file = "sensor.txt"
prefix = "/home/irbyjm/bro"
broctl = os.path.join(prefix, "bin", "broctl")
spooltmp = "/home/irbyjm/bro/spool/tmp"

def populate_sensors(line, sensors):
	temp = line.split()
	if temp[0][0] != "#":
		sensors[temp[1]] = {}
		sensors[temp[1]]['ip'] = temp[0]

def menu():
	print "-----------------------------"
	print "Brommand Line Interface (BLI)\n"
	print "(0) Get status"
	print "(1) Print status"
	print "(9) Quit"

def getstatus(sensors):
        for hostname in sensors:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                        ssh.connect(
                                sensors[hostname]['ip'],
                                username = sshuser,
                                key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
                                timeout = 10
                        )
			(stdin, stdout, stderr) = ssh.exec_command("ls " + spooltmp + "|grep crash |wc -l")
			sensors[hostname]['crashlogs'] = stdout.readline().strip()
                        (stdin, stdout, stderr) = ssh.exec_command(broctl + " status")
			lines = running = stopped = crashed = 0
			for line in stdout.readlines():
				if "manager" in line or "proxy" in line or "worker" in line:
					lines += 1
					if "running" in line:
						running += 1
					elif "stopped" in line:
						stopped += 1
					elif "crashed" in line:
						crashed += 1
			if running == lines:
				sensors[hostname]['status'] = "BrOK, " + sensors[hostname]['crashlogs'] + " crash logs"
			else:
				sensors[hostname]['status'] = "Unhealthy (" + str(running) + " running, " + str(stopped) + " stopped, " + str(crashed) + " crashed, " + sensors[hostname]['crashlogs'] + " crash logs)"
			ssh.close()
                except Exception as e:
                        sensors[hostname]['status'] = e
	print "\nStatus loaded..."
	print raw_input("<Press Enter to continue>")
	return 1

def printstatus(sensors):
	print "\n{:20s} : {:15s} : {}".format("Hostname", "IP Address", "Status")
	for sensor in sensors:
		print "{:20s} : {:15s} : {}".format(sensor, sensors[sensor]['ip'], sensors[sensor]['status'])
	raw_input("<Press Enter to continue>")

def getsensors(sensors):
	sensor_list = open(sensor_file, "r")
	for line in sensor_list:
		populate_sensors(line, sensors)

def main():
	sensors = {}
	getsensors(sensors)
	loaded = 0
	decision = 0
	while decision != 9:
		menu()
		decision = input("action> ")
		if decision == 0:
			loaded = getstatus(sensors)
		elif decision == 1:
			if loaded:
				printstatus(sensors)
			else:
				print "\nStatus not yet loaded (get status)"
				raw_input("<Press Enter to continue>")
		elif decision == 9:
			print "Exiting..."

######
main()
