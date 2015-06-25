# bli

Sample sensor.txt
```
#ip,hostname,prefix,spooltmp
127.0.0.1,localhost,,
172.16.29.42,,,

192.168.8.180,testhost1,,
#192.168.8.181,testhost2,,
```

Sample app output:
```
IP Address      : Hostname             : Status
-----------------------------------------------
172.16.29.42	:		       : timed out
192.168.8.180   : testhost1            : timed out
127.0.0.1       : localhost            : Unhealthy (2 running, 0 stopped, 1 crashed, 2 crash logs)

```
