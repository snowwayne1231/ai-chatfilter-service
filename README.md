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
```

> for Redhat Linux (centos)
```Shell
sudo rpm -Uvh https://yum.postgresql.org/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm
sudo yum -y install postgresql10-server postgresql10
sudo yum -y install postgresql-contrib postgresql-libs
sudo /usr/pgsql-10/bin/postgresql-10-setup initdb

systemctl start postgresql-10.service
systemctl enable postgresql-10.service
```

> create a new database and setting db users
```Shell
sudo su - postgres -c "psql"
\conninfo
\password postgres
CREATE DATABASE [name of database];
\q
```

> finally make sure pg_hba.conf is trust all localhost
```SQL
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
> for Debian Linux (ubuntu)
```Shell
sudo apt-get install nginx
sudo /etc/init.d/nginx start
```

> for Redhat Linux (centos)
```Shell
sudo yum -y install nginx
sudo systemctl start nginx
```

> for both linux sysyem, allow 80 and 443 port in firewall
```Shell
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
> make sure the system is matched one of below:
+ Ubuntu 16.04 or later
+ Windows 7 or later
+ macOS 10.12.6 (Sierra) or later (no GPU support)
+ Raspbian 9.0 or later

> make sure pip version > 19.0.x


### 7. wsgi
> for both Linux system
```Shell
sudo pip install uwsgi
```


## Installation Steps


### 0. prepare the project
> first thing is make project folder and clone the project of ai-chat-filter.
**for example the project name is "ai"**:

+ 0.1. Clone the project
```Shell
mkdir /ai
cd /ai
git clone ...
cd /ai/ai-chatfilter-service
```
+ 0.2. Setting nginx config
> copy and chang all the path in nginx.conf file
```Shell
cp nginx.conf.example nginx.conf
nano nginx.conf
```
```nginx
location /static {
    alias /path/to/mysite/static;
}
```
> change all `/path/to/mysite/` to `/ai/ai-chatfilter-service/`
```nginx
location /static {
    alias /ai/ai-chatfilter-service/static;
}
```
> change server name you own or if you want pass any request change to `_`
```EditorConfig
server_name 0.0.0.0;
```
>  make symbolic link to niginx configs
```Shell
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/sites-enabled/
or
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/conf.d/
```

+ 0.3. Setting Project config
> copy setting.ini and chagne config you need
```Shell
cp setting.ini.example setting.ini
nano setting.ini
```
> change "ALLOWED_HOSTS" and "DATABASE"
```EditorConfig
ALLOWED_HOSTS = 127.0.0.1, 172.16.20.120
[DATABASE]
DATABASE_NAME = DB_NAME
DATABASE_USER = DB_USER_NAME
DATABASE_PASSWORD = DB_PASSWORD
```

+ 0.4. Create logs directory in project
```Shell
mkdir /ai/logs
chmod -R 777 /ai/logs
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
> should be seen the python version at least with 3.7.5 and pip is 19+


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
pip install websocket
pip install websocket-client
pip install zhconv
```


### 4. do django framework initialize
> build up the database instruction
```Shell
python manage.py migrate
python manage.py loaddata service/seed/initial.json
python manage.py loaddata ai/json/knowledge.json
```
> create django admin superuser with following the guiding steps to finish
```Shell
python manage.py createsuperuser
```
> collect and copy the static file in project to improve performance
```Shell
python manage.py collectstatic
```


### 5. training ai
> before you train you may need to check your vocabulary dictionary
```Shell
python manage.py knowledge -i ai/assets/chinese/dict_revised_2015_20190712_1.xls
python manage.py knowledge -i ai/assets/chinese/dict_revised_2015_20190712_2.xls
python manage.py knowledge -i ai/assets/chinese/dict_revised_2015_20190712_3.xls
python manage.py knowledge
```
> if you need some help then type `python manage.py train -h` have a look on helper and see how to use train
```Shell
python manage.py train -i ai/assets/.. -f 0.90
```
> after upon that command, you should start an AI training now, Stop anytime when you want by key in Ctrl+C


### 6. firewall setting
> open tcp port for chatting socket
```Shell
sudo firewall-cmd --permanent --zone=public --add-port=8025/tcp
```


## For linux product deploy using supervisor
setting supervisor <http://supervisord.org/configuration.html>
> for Debian Linux (ubuntu)
```Shell
sudo apt install supervisor
```

> for Redhat Linux (centos)
```Shell
sudo yum -y install supervisor

sudo systemctl start supervisord
sudo systemctl enable supervisord
sudo systemctl status supervisord
```

> copy and edit config
```Shell
cp supervisor.conf.example supervisor.conf
nano superviosr.conf
```
+ > change all `/ai/ai-chatfilter-service` to your project's service folder
```EditorConfig
directory=/ai/ai-chatfilter-service
```
+ > change all `/ai/venv/bin/python` to your virtual environment python
```EditorConfig
command=/ai/venv/bin/python tcpsocket/main.py -p 8025
```
+ > change all `/ai/logs/` to your logs folder
```EditorConfig
stdout_logfile=/ai/logs/tcpsocket.log
```

> symbolic link to supervisor config
```Shell
sudo ln -s /path/to/mysite/supervisor.conf /etc/supervisord.d/ai-chatfilter-service.ini
```

> reload supervisor
```Shell
sudo supervisorctl reload
sudo supervisorctl reread
sudo supervisorctl update
```

> reload nginx
```Shell
sudo systemctl reload nginx
sudo systemctl restart nginx
```


## Others

> Check the SELinux and add policy to nginx or just disable it
```Shell
sestatus
```

*SELinux might block the socket connection between nginx and supervisord*



## Testing

### 1. website
> Test the django web site is working, type domain:port on browser for example: `http://172.16.20.120:81/` you should see the screen with 404 not found page but has content like below
```
Using the URLconf defined in service.urls, Django tried these URL patterns, in this order:

chat/
admin/
auth/
auth/
The empty path didn't match any of these.
```

> that means the website is working fine and next we change url to `http://172.16.20.120:81/chat/`, try typeing something to test websockets

### 2. tcp socket
> use tcpsocket client to test chatting binary packages.
```Shell
cd /ai/ai-chatfilter-service
python tcpsocket/client.py -h 127.0.0.1 -p 8025
```
> you will see
```
Please choose package type:
1.hearting
2.login
3.login response
4.chatting
5.chat response
Enter number:
```
*everything was fine!!*


## Maintaining
> dump and restore blockword data
```Shell
python manage.py clear blockedsentence
python manage.py clear goodsentence
python manage.py dumpdata service > service/seed/initial.json

python manage.py loaddata service/seed/initial.json
```

