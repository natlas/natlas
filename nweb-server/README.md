# nweb-server

Installing Elasticsearch
------------------------

NWeb now defaults to using elasticsearch for the backend. The installation of elasticsearch isn't something I wanted to try to automate, so download the latest here and then follow the instructions below:

https://www.elastic.co/downloads/elasticsearch

```
$ sudo apt-get install default-jre
$ sudo dpkg -i elasticsearch-XXXXXX.deb
$ sudo /etc/init.d/elasticsearch start
```


The Setup
------------------

Most people will be able to just do:

```
$ git clone https://github.com/pierce403/nweb.git
$ cd nweb/nweb-server/
$ ./setup-server.sh
```

If you run the setup script as root, it will automatically attempt to install the necessary prerequisites for you. If you run it without permissions, it will tell you what it was able to determine about setup. The following packages are necessary:

- apt-get install python3.6
- apt-get install python3-pip
- pip3 install virtualenv


The Config
------------------
Once this process is done, the server should be almost ready to go. But before we begin, we need to setup some instance-specific configuration options. The application does this via environment variables, which you can set however you want. Since this is the server, I encourage the use of a systemd unit and an EnvironmentFile. You can see the various options to configure in `config.py`. I'm not going to list them in detail here because they will probably change and create conflicting information in the documentation.


Setting the Scope
------------------
By default, we generate a `config/scope.txt` and a `config/blacklist.txt` that include loopback addresses in them. You'll want to modify this to include the scope of your targets. Each line in either file should be either a single IP address or a CIDR range. For example, to scan your local network you might add `10.0.0.0/8` to `config/scope.txt`. But maybe you know there's a specific system that will crash if you scan it, so you want to add `10.1.13.7` to `config/blacklist.txt`. This will ensure that your agents won't be tasked to scan that host.

Initializing the Database
------------------
There's one more thing we need to do, and that's initialize the metadata database with the correct schema. This is done using the flask-migrate plugin, and can be done like so:

```
$ cd nweb/nweb-server
$ source venv/bin/activate
$ export FLASK_APP=nweb-server.py
$ flask db upgrade
$ deactivate
```

Starting the Server
------------------

Starting the server is easy and can pretty much be handled entirely by the `run-server.sh` script. Simply navigate to the nweb-server folder (where this readme is) and `./run-server.sh`. This will start the flask application in your terminal, listening on localhost on port 5000. If you really want, you could change this to listen on a specific IP address on another port, but it is encouraged that you add nginx in front of your flask application.

Furthermore, you might think it's mighty inconvenient that the flask application is running in your terminal and now you can't close the terminal without shutting down the server. You can remediate this with a systemd unit (an example one will be provided), or by simply launching the server inside a `screen` session.


NGINX as a Reverse Proxy
------------------
As mentioned above, it is not really advisable to run the flask application directly on the internet (or even on your local network). The flask application is just that, an application. It doesn't account for things like SSL certificates, and modifying application logic to add in potential routes for things like Let's Encrypt should be avoided. Luckily, it's very easy to setup a reverse proxy so that all of this stuff can be handled by a proper web server and leave your application to do exactly what it's supposed to do.

To install nginx, you can simply `apt-get install nginx` as root. Once it's installed, let's make a copy of the default site config:

```
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/nweb
```

Now open up `/etc/nginx/sites-available/nweb` in your favorite text editor and add this:

```
server {
        listen 80;
        listen [::]:80;
        server_name <host>;
        # The below location block is for Let's Encrypt, feel free to delete if you're not using LE.
        location ~ /.well-known { 
            allow all;
        }
        return 301 https://$host$request_uri;
}

server {
        listen 443 ssl;
        listen [::]:443 ssl;
        server_name <host>;

        ssl_certificate /etc/ssl/certs/<cert>.cert;
        ssl_certificate_key /etc/ssl/private/<key>.key;
        ssl_session_timeout 10m;
        ssl_session_cache shared:SSL:10m;
        ssl_session_tickets off;
        ssl_stapling on;
        ssl_stapling_verify on;
        ssl_protocols TLSv1.2;
        ssl_prefer_server_ciphers on;
        ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
        ssl_ecdh_curve secp384r1;
        ssl_dhparam /etc/nginx/dhparam.pem;

        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Robots-Tag none;
        add_header Strict-Transport-Security "max-age=31536000";

        location / {
                proxy_set_header Host $host;
                proxy_set_header REMOTE_ADDR $remote_addr;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_pass http://127.0.0.1:5000;
        }
}
```

If you're not planning on using TLS, well, you should reconsider. Go ahead and modify the lines that say `server_name <host>` and change `<host>` to whatever hostname your server will be listening on. Then, in the second server block, you'll want to set the `ssl_certificate` and `ssl_certificate_key` values to point to the correct SSL certificate and key. The final `location /` block is where the reverse proxying actually happens, specifically line `proxy_pass http://127.0.0.1:5000;`. 


Example Systemd Unit
------------------
Below is an example systemd unit you can use to get nweb-server running in systemd.

```
[Unit]
Description=Scan collection and search tool
After=network.target
 
[Service]
Type=simple
User=nweb
WorkingDirectory=/opt/nweb/nweb-server
EnvironmentFile=/opt/nweb/nweb-server/nweb.env
ExecStart=/bin/bash /opt/nweb/nweb-server/run-server.sh
Restart=always

[Install]
WantedBy=multi-user.target
```