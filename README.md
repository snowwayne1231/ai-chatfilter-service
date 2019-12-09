# AI-Chatting-Filter

## Requirements

### 1. python3.7 / pip3 and some dependencies
> for Debian Linux (ubuntu)
```Shell
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
```Shell
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
```Shell
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
```Shell
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

> finally make sure pg_hba.conf is trust all localhost
```Shell
postgres=# show_hba_file;
```


### 3. redis server
> for Debian Linux (ubuntu)
```Shell
sudo apt install redis-server
sudo nano /etc/redis/redis.conf  // change supervised no > supervised systemd
sudo systemctl restart redis.service
sudo systemctl status redis
```

> for Redhat Linux (centos)
```Shell
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
```Shell
sudo apt-get install nginx
sudo /etc/init.d/nginx start
```

> for Redhat Linux (centos)
```Shell
sudo yum -y install nginx
sudo systemctl start nginx

sudo firewall-cmd --permanent --zone=public --add-service=http 
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```


### 5. virtualenv
> for Debian Linux (ubuntu)
```Shell
sudo apt-get install python-virtualenv
sudo apt-get install python3.7-venv
```

> for Redhat Linux (centos)
```Shell
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
```Shell
sudo pip install uwsgi
```

> for Redhat Linux (centos)
```Shell
sudo pip install uwsgi
```


## Installation Steps

### 0. prepare the configs
> first thing is make project folder and clone the project of ai chat filter
> for example the project name is "ai":
```Shell
mkdir /ai
cd /ai
git clone ...
```

> copy and chang all the path in nginx.conf file
```Shell
cp nginx.conf.example nginx.conf
nano nginx.conf
```
file example project name is "ai":
```EditorConfig
# Django media
location /media {
    alias /path/to/mysite/media;
}
```
change all "/path/to/mysite/" to "/ai/ai-chatfilter-service/"
```EditorConfig
# Django media
location /media {
    alias /ai/ai-chatfilter-service/media;
}
```
change server name you own
```EditorConfig
server_name 172.16.20.120;
```

>  make symbolic link
```Shell
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/sites-enabled/
or
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/conf.d/
```

> copy setting.ini and chagne config you need
```Shell
cp setting.ini.example setting.ini
nano setting.ini
```
change "ALLOWED_HOSTS" and "DATABASE"
```EditorConfig
ALLOWED_HOSTS = 127.0.0.1, 172.16.20.120

[DATABASE]
DATABASE_NAME = DB_NAME
DATABASE_USER = DB_USER_NAME
DATABASE_PASSWORD = DB_PASSWORD
```


### 1. build up virtual environment
> for example the project name is "ai":
```Shell
cd /ai
python3 -m venv venv
chmod -R 777 venv
source venv/bin/activate
python -V
pip -V
```

### 2. install tensorflow 2.0 - lastest
> before doing this you've make sure you already got "venv" environment
> install what python's need in "venv"
```Shell
pip install tf-nightly
pip install tensorflow_datasets
```

### 3. install python librarys
```Shell
pip install -r requirement.txt

pip install psycopg2-binary
```

### 4. do django framework initialize
> build up the data and static files
```Shell
python manage.py migrate

python manage.py loaddata service/seed/initial.json

python manage.py createsuperuser

python manage.py collectstatic
```

### 5. trainning ai
> if you need some help then type -h have a look on helper and see how to use train
```Shell
python manage.py train -h

python manage.py train -i ai/assets/..
```


# for linux product deploy using supervisor
setting supervisor <http://supervisord.org/configuration.html>
> for Debian Linux (ubuntu)
```Shell
sudo apt install supervisor

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

```

> for Redhat Linux (centos)
```Shell
sudo yum -y install supervisor

sudo systemctl start supervisord
sudo systemctl enable supervisord
sudo systemctl status supervisord
```

> copy and change config
```Shell
cp supervisor.conf.example supervisor.conf
nano superviosr.conf
```

```EditorConfig

```


> make logs dir in project
> for example the project name is "ai":
```Shell
mkdir /ai/logs
chmod -R 777 /ai/logs
```