# bli (Brommand Line Interface)
_Disclaimer: I have no afilliation with The Bro Project (http://www.bro.org)._

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
```
#ip,hostname,ssh_user,prefix,spooltmp,policy
127.0.0.1,localhost,,,,
192.168.8.168,testhost1,root,/usr/local/bro,,virt
192.168.8.169,testhost2,root,/usr/local/bro,,
#192.168.8.155,testhost4,root,/usr/local/bro,,
192.168.8.180,testhost3,,,,
```

Sample `config` output:
```
IP Address      : Hostname             : User       : Prefix               : SpoolTmp             : Policy
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : broadmin   : /opt/bro             : /data/bro/spool/tmp  : phys
192.168.8.168   : testhost1            : root       : /usr/local/bro       : /data/bro/spool/tmp  : virt
192.168.8.169   : testhost2            : root       : /usr/local/bro       : /data/bro/spool/tmp  : phys
192.168.8.180   : testhost3            : broadmin   : /opt/bro             : /data/bro/spool/tmp  : phys
```

Sample `status` output:
```
IP Address      : Hostname             : Status
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : Error ([Errno 111] Connection refused)
192.168.8.168   : testhost1            : OK (0 warnings, 29 crash logs)
192.168.8.169   : testhost2            : OK (0 warnings, 14 crash logs)
192.168.8.180   : testhost3            : Unhealthy (21 running, 0 stopped, 1 crashed, 383 crash logs)
```

Sample `info` output:
```
IP Address      : Hostname             : Bro Version : Broctl Version
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : --          : --
192.168.8.168   : testhost1            : 2.3         : 1.3
192.168.8.169   : testhost2            : 2.4         : 1.4
192.168.8.180   : testhost3            : 2.4-87      : 1.4-28
```

Sample `check_policy` output:
```
IP Address      : Hostname             : Policy : Issue      : File/Details
------------------------------------------------------------------------------------------------------------------------
127.0.0.1       : localhost            : phys   : --         : --
192.168.8.168   : testhost1            : virt   :            :
                :                      :        : error	     : deployment information for policy 'virt' does not exist
192.168.8.169   : testhost2            : phys   :            :
192.168.8.180   : testhost3            : phys   :            :
                :                      :        : modified   : testbro/intel/bro_intel.tsv
                :                      :        : missing    : local.bro.example
```
