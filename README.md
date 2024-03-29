What is this?
=============

A simple wsgi script that can become an HTTP server to serve static files! Why you say? Well I at work had this problem, and it went like so : we had a least 6 different development environments ( dev/stage/pre-pro/personal machines/the usual) and needed many times to sync data such as images to those machines. Most of the time the problems were at demo time. But there was not an easy way for us to be synced with the live production server... Yes a glaring omission for a cron job but sometimes as dev we do not have access to prod-servers. What to do? Well first you point your statics urls to the prod servers, that only goes so far and not always what you want. Next up is find a way to synchronize things.


#### Edge Server

In short this replicates the abilities of an edge server, demand content if it's not on the server it will ask it's configured friendly servers if they have the file and if so will download it from them.

#### Configuration


an example of configuration : 

```
[ServerConfig]
block_size = 2048
root_dir = /tmp/
friends = http://example.com/,http://example.ca/
host_ip = 0.0.0.0
host_port = 8051
thread_num = 10
```

start the server with :

```
nohup python annelia/annelia.py  -c /path/to/conf &
```

NOTE : Do Not configure a server as it's own friend! 


#### Missing

* Caching
* Timeouts to prevent a ping-pong effect of servers that are identical

#### Caveat

Do not at this time setup two of these as Friendlies as they might get into an endless loop of asking each other for the file.
