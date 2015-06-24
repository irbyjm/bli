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
	if line.strip():
		temp = line.split()
		if temp[0][0] != "#":
			sensors[temp[0]] = {}
			if len(temp) == 2:
				sensors[temp[0]]['hostname'] = temp[1]
			else:
				sensors[temp[0]]['hostname'] = ""
			sensors[temp[0]]['crashlogs'] = 0

def menu():
	print 
	print "-"*30
	print "|{:^28s}|".format("Brommand Line Interface")
	print "-"*30
	print "|{:28s}|".format(" (0) Get status")
	print "|{:28s}|".format(" (1) Print status")
	print "|{:28s}|".format(" (2) Clear crash logs")
	print "|{:28s}|".format(" (9) Quit")
	print "-"*30

def getstatus(sensors):
        for ip in sensors:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                        ssh.connect(
                                ip,
                                username = sshuser,
                                key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
                                timeout = 10
                        )
			(stdin, stdout, stderr) = ssh.exec_command("ls " + spooltmp + "|grep crash |wc -l")
			sensors[ip]['crashlogs'] = int(stdout.readline().strip())
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
				sensors[ip]['status'] = "OK, " + str(sensors[ip]['crashlogs']) + " crash logs"
			else:
				sensors[ip]['status'] = "Unhealthy (" + str(running) + " running, " + str(stopped) + " stopped, " + str(crashed) + " crashed, " + str(sensors[ip]['crashlogs']) + " crash logs)"
			ssh.close()
                except Exception as e:
                        sensors[ip]['status'] = e
	print "\nStatus loaded..."
	raw_input("<Press Enter to continue> ")
	return 1

def clearlogs(sensors):
	cleared = 0
        for ip in sensors:
		if sensors[ip]['crashlogs'] > 0:
	                ssh = paramiko.SSHClient()
	                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	                try:
	                        ssh.connect(
	                                ip,
	                                username = sshuser,
	                                key_filename = os.path.expanduser(os.path.join("~", ".ssh", "id_rsa.pub")),
	                                timeout = 10
	                        )
	                        (stdin, stdout, stderr) = ssh.exec_command("rm -rf " + spooltmp + "/*crash")
	                        ssh.close()
				cleared += 1
				print "\nLogs cleared from", ip, "..."
	                except Exception as e:
	                        sensors[hostname]['status'] = e
	if cleared == 0:
		print "\nNo log(s) cleared..."
	raw_input("<Press Enter to continue> ")

def printstatus(sensors):
	print "\n{:15s} : {:20s} : {}".format("IP Address", "Hostname", "Status")
	print "-"*47
	for ip in sensors:
		print "{:15s} : {:20s} : {}".format(ip, sensors[ip]['hostname'], sensors[ip]['status'])
	raw_input("<Press Enter to continue> ")

def getsensors(sensors):
	sensor_list = open(sensor_file, "r")
	for line in sensor_list:
		populate_sensors(line, sensors)

def main():
	sensors = {}
	getsensors(sensors)
	loaded = decision = 0
	while decision != 9:
		menu()
		try:
			decision = input("\naction> ")
		except Exception as e:
			decision = 666
	
		if decision == 0:
			loaded = getstatus(sensors)
		elif decision == 9:
			print "\nExiting..."
		else:
			if loaded:
				if decision == 1:
					printstatus(sensors)
				elif decision == 2:
					clearlogs(sensors)
			else:
				print "\nStatus not yet loaded (get status)"
				raw_input("<Press Enter to continue> ")

######
main()
