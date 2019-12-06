# AI-Chatting-Filter

## Requirements

### 1. python3.7 / pip3 and some dependencies
> for Debian Linux (ubuntu)
```shell
sudo apt update
sudo apt-get install python3.7

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
sudo update-alternatives --config python3
python3 -V

sudo apt-get install -y python-apt
sudo apt-get install -y python3-pip
sudo apt-get install -y python-dev python3.7-dev python-levenshtein
```

> for Redhat Linux (centos)
```shell
sudo yum update
sudo yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make libffi-devel

sudo yum -y install epel-release
sudo yum -y install python-pip
sudo pip install wget

wget https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tgz
tar -zxvf Python-3.7.5.tgz
cd Python-3.7.5
./configure prefix=/usr/local/python3
sudo make install

sudo ln -s /usr/local/python3/bin/python3.7 /usr/bin/python3
sudo ln -s /usr/local/python3/bin/pip3.7 /usr/bin/pip3
python3 -V

sudo yum -y install python-devel python3-devel python-Levenshtein
```


### 2. postgresql 10.11.x
> for Debian Linux (ubuntu)
```shell
sudo apt-get install postgresql-10
sudo apt-get install postgresql-contrib libpq-dev
sudo su - postgres
psql
\conninfo
\password postgres
CREATE DATABASE ai-db-name;
\q
```

> for Redhat Linux (centos)
```shell
sudo rpm -Uvh https://yum.postgresql.org/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm
sudo yum -y install postgresql10-server postgresql10
sudo yum -y install postgresql-contrib postgresql-libs
sudo /usr/pgsql-10/bin/postgresql-10-setup initdb

systemctl start postgresql-10.service
systemctl enable postgresql-10.service

sudo passwd postgres
sudo su - postgres -c "psql"
\conninfo
\password postgres
CREATE DATABASE ai-db-name;
\q
```


### 3. redis server
> for Debian Linux (ubuntu)
```shell
sudo apt install redis-server
sudo nano /etc/redis/redis.conf  // change supervised no > supervised systemd
sudo systemctl restart redis.service
sudo systemctl status redis
```

> for Redhat Linux (centos)
```shell
sudo yum -y install epel-release yum-utils
sudo yum -y install http://rpms.remirepo.net/enterprise/remi-release-7.rpm
sudo yum-config-manager --enable remi
sudo yum -y install redis
sudo systemctl start redis
sudo systemctl enable redis
sudo systemctl status redis
```


### 4. nginx
depending <https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html> do the section of "Configure nginx for your site"

> for Debian Linux (ubuntu)
```shell
sudo apt-get install nginx
sudo /etc/init.d/nginx start
```

> for Redhat Linux (centos)
```shell
sudo yum -y install nginx
sudo systemctl start nginx

sudo firewall-cmd --permanent --zone=public --add-service=http 
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```


### 5. virtualenv
> for Debian Linux (ubuntu)
```shell
sudo apt-get install python-virtualenv
sudo apt-get install python3.7-venv
```

> for Redhat Linux (centos)
```shell
sudo yum -y install python-virtualenv
```


### 6. tensorflow 2.0+
> make sure the system is matched one of below
Ubuntu 16.04 or later
Windows 7 or later
macOS 10.12.6 (Sierra) or later (no GPU support)
Raspbian 9.0 or later

> make sure pip version > 19.0.


### 7. wsgi
> for Debian Linux (ubuntu)
```shell
sudo pip install uwsgi
```

> for Redhat Linux (centos)
```shell
sudo pip install uwsgi
```


## Installation Steps

### 0. prepare the configs
> first thing is make project folder and clone the project of ai chat filter
```shell
mkdir /[mysite]
cd /[mysite]
git clone ...
```

> copy and chang all the path in nginx.conf file then make symbolic link
```shell
cp nginx.conf.example nginx.conf
nano nginx.conf
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/sites-enabled/
or
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/conf.d/
```

> copy setting.ini and chagne config you need
```shell
cp setting.ini.example setting.ini
nano setting.ini
```

### 1. build up virtual environment
```shell
cd /[mysite]
python3 -m venv venv
chmod -R 777 venv
source venv/bin/activate
python -V
pip -V
```

### 2. install tensorflow 2.0 - lastest
```shell
pip install tf-nightly
pip install tensorflow_datasets
```

### 3. install python librarys
```shell
pip install -r requirement.txt

pip install psycopg2-binary

python manage.py migrate

python manage.py loaddata service/seed/initial.json

python manage.py createsuperuser

python manage.py collectstatic

```

# for linux setting
```shell
sudo apt install supervisor
```
setting supervisor <https://channels.readthedocs.io/en/latest/deploying.html>
create the supervisor configuration file (often located in /etc/supervisor/conf.d/)

```file
[fcgi-program:asgi]
# TCP socket used by Nginx backend upstream
socket=tcp://localhost:8000

# Directory where your site's project files are located
directory=/my/app/path

# Each process needs to have a separate socket file, so we use process_num
# Make sure to update "mysite.asgi" to match your project name
command=daphne -u /run/daphne/daphne%(process_num)d.sock --fd 0 --access-log - --proxy-headers mysite.asgi:application

# Number of processes to startup, roughly the number of CPUs you have
numprocs=4

# Give each process a unique name so they can be told apart
process_name=asgi%(process_num)d

# Automatically start and recover processes
autostart=true
autorestart=true

# Choose where you want your log to go
stdout_logfile=/your/log/asgi.log
redirect_stderr=true
```

```shell
sudo supervisord -c /etc/supervisor/supervisord.conf
sudo supervisorctl reread
sudo supervisorctl update
```
