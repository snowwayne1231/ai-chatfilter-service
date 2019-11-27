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

sudo apt-get install -y python-apt
sudo apt-get install -y python3-pip
sudo apt-get install -y libpq-dev python-dev python3.7-dev
sudo apt-get install -y python-levenshtein
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

```

> 3. redis
```shell
sudo apt install redis-server
sudo nano /etc/redis/redis.conf  // change supervised no > supervised systemd
sudo systemctl restart redis.service
sudo systemctl status redis
```

> 4. virtualenv
```shell
sudo apt-get install python-virtualenv
sudo apt-get install python3.7-venv
```

> 5. tensorflow 2.0+

Should be install after

```shell
pip install tf-nightly
pip install tensorflow_datasets

```

> 6. wsgi
```shell
sudo pip3 install uwsgi

```

> 7. nginx
```shell
sudo apt-get install nginx
sudo /etc/init.d/nginx start

```
depending <https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html> do the section of "Configure nginx for your site"

```shell
sudo cp nginx.conf.example nginx.conf
```
then chang all the path in nginx.conf file

```shell
sudo ln -s /path/to/mysite/nginx.conf /etc/nginx/sites-enabled/
```


## Install Steps

```shell
sudo git clone ...

cd project

sudo python3 -m venv venv

sudo chmod -R 777 venv

source venv/bin/activate

sudo cp setting.ini.example setting.ini

sudo nano setting.ini

pip install -r requirement.txt

pip install psycopg2-binary

python manage.py migrate

python manage.py loaddata service/seed/initial.json

python manage.py createsuperuser

python manage.py collectstatic

sudo apt install nginx supervisor

```