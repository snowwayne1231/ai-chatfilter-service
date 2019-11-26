# AI-Chatting-Filter

## Requirements

> 1. python3.7 / pip3
```shell
sudo apt update
sudo apt-get install python3.7
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
sudo update-alternatives --config python3
python3 -V
sudo apt-get install python-apt
sudo apt-get install python3-pip
sudo apt-get install libpq-dev python-dev
```

> 2. postgresql 10.11.x
```shell
sudo apt-get install postgresql-10
sudo apt-get install postgresql-contrib
sudo su - postgres
psql
\conninfo
\password postgres
CREATE DATABASE ai-db-name;
\q

sudo pip3 install psycopg2-binary
```

> 3. redis
```shell
sudo apt install redis-server
sudo nano /etc/redis/redis.conf  // change supervised no > supervised systemd
sudo systemctl restart redis.service
sudo systemctl status redis
```

> 4. tensorflow 2.0+
```shell
sudo pip3 install tf-nightly

```

> 5. wsgi
```shell

```

> 6. virtualenv
```shell
sudo apt install python-virtualenv
sudo apt-get install python3.7-venv
```

## Install Steps

```shell
sudo git clone ...

cd project

sudo python3 -m venv venv

source venv/bin/activate

sudo cp setting.ini.example setting.ini

sudo nano setting.ini

sudo pip3 install -r requirement.txt

sudo python manager migrate

sudo python manager loaddata service/seed/initial.json
```