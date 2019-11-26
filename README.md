# AI-Chatting-Filter

> Requirements

## 1. python3.7 / pip3
```shell
sudo apt-get update
```

## 2. postgresql 10.11.x
```shell
sudo apt-get install postgresql-10
sudo su - postgres
psql
\conninfo
\password postgres
CREATE DATABASE ai-db-name;
\q
```

## 3. redis
```shell
sudo apt install redis-server
sudo nano /etc/redis/redis.conf  // change supervised no > supervised systemd
sudo systemctl restart redis.service
sudo systemctl status redis
```

## 4. tensorflow 2.0+

## 5. wsgi

## Install steps

```shell
pip install -r requirement.txt

setting postgresql

python manager migrate

python manager loaddata service/seed/initial.json
```