# bli

Sample sensor.txt
```
#IP Address     Hostname
127.0.0.1       localhost
192.168.8.180   testhost1
#192.168.8.181  testhost2
```

Sample app output:
```
IP Address      : Hostname             : Status
-----------------------------------------------
192.168.8.180   : testhost1            : timed out
127.0.0.1       : localhost            : Unhealthy (2 running, 0 stopped, 1 crashed, 2 crash logs)

```
