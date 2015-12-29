# Brommand Line Interface
_Disclaimer: I have no afilliation with The Bro Project (http://www.bro.org)._

## Features
- Validation of downstream monitor health
- Centralized view of monitor versioning
- Monitoring of deployments for policy changes

## Install
Sample directory structure
```
        <bli root>
   /	    |		    \
bli.py	sensor.csv	./deploy
					/      \
				 ./phys   ./virt
			     /	   	    \
			  ./site       ./site
			   /		     \
			local.bro	 local.bro
			...			 ...
```

Sample `sensor.csv`:
```bash
#ip,hostname,ssh_user,prefix,spooltmp,policy
127.0.0.1,localhost,,,,devel
192.168.8.168,testhost1,root,/usr/local/bro,,virt-hub
192.168.8.169,testhost2,root,/usr/local/bro,,phys-int
#192.168.8.155,testhost4,root,/usr/local/bro,,
192.168.8.180,testhost3,,,,phys-dist
```

## Getting Started
```
------------------------------
|  Brommand Line Interface   |
------------------------------
| (1) Get status             |
| (2) Print status           |
| (3) Clear crash logs       |
| (4) Check policy           |
| (8) Print information      |
| (9) Print configuration    |
| (0) Quit                   |
------------------------------
```

```
Usage: bli.py [OPTION]
Options:
  status               print downstream health
  config               print downstream config
  info                 print downstream info (version, et al.)
  clear_logs           clear crash logs
  check_policy         check policy
  -?, --help           give this help list
```

## Usage
Sample `config` (Print configuration) output:
```
IP Address      : Hostname             : User       : Prefix               : SpoolTmp             : Policy
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : broadmin   : /opt/bro             : /data/bro/spool/tmp  : devel
192.168.8.168   : testhost1            : root       : /usr/local/bro       : /data/bro/spool/tmp  : virt-hub
192.168.8.169   : testhost2            : root       : /usr/local/bro       : /data/bro/spool/tmp  : phys-int
192.168.8.180   : testhost3            : broadmin   : /opt/bro             : /data/bro/spool/tmp  : phys-dist
```

Sample `status` (Print status) output:
```
IP Address      : Hostname             : Status
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : error ([Errno 111] Connection refused)
192.168.8.168   : testhost1            : ok (0 warnings, 29 crash logs)
192.168.8.169   : testhost2            : ok (0 warnings, 14 crash logs)
192.168.8.180   : testhost3            : unhealthy (21 running, 0 stopped, 1 crashed, 383 crash logs)
```

Sample `info` (Print information) output:
```
IP Address      : Hostname             : Bro Version : Broctl Version
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : --          : --
192.168.8.168   : testhost1            : 2.3         : 1.3
192.168.8.169   : testhost2            : 2.4         : 1.4
192.168.8.180   : testhost3            : 2.4-87      : 1.4-28
```

Sample `check_policy` (Check policy) output:
```
IP Address      : Hostname             : Policy    : Issue      : File/Details
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : devel     : --         : --
192.168.8.168   : testhost1            : virt-hub  : warning    : deployment information for policy 'virt' does not exist
192.168.8.169   : testhost2            : phys-int  : ok         :
192.168.8.180   : testhost3            : phys-dist : modified   : testbro/intel/bro_intel.tsv
                :                      :           : missing    : local.bro.example
```
