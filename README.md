# bli

Sample sensor.txt
```
#ip,hostname,sshuser,prefix,spooltmp
#127.0.0.1,localhost,,,
192.168.8.168,testhost1,root,/usr/local/bro,
192.168.8.169,testhost2,root,/usr/local/bro,
192.168.8.155,testhost4,root,/usr/local/bro,
192.168.8.180,testhost3,,,
```

Sample app output:
```
IP Address      : Hostname             : User       : Prefix               : SpoolTmp             : Status
------------------------------------------------------------------------------------------------------------------------
192.168.8.155   : testhost4            : root       : /usr/local/bro       : /data/bro/spool/tmp  : OK (0 warnings, 51 crash logs)
192.168.8.180   : testhost3            : broadmin   : /opt/bro             : /data/bro/spool/tmp  : Unhealthy (21 running, 0 stopped, 1 crashed, 383 crash logs)
192.168.8.169   : testhost2            : root       : /usr/local/bro       : /data/bro/spool/tmp  : OK (0 warnings, 14 crash logs)
192.168.8.168   : testhost1            : root       : /usr/local/bro       : /data/bro/spool/tmp  : OK (0 warnings, 29 crash logs)
```
