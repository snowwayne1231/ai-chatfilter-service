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
sudo apt install python3-pip
```

> 2. postgresql 10.11.x
```shell
sudo apt-get install postgresql-10
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

> 4. tensorflow 2.0+

> 5. wsgi

> Install steps

```shell
pip install -r requirement.txt

setting postgresql

python manager migrate

python manager loaddata service/seed/initial.json
```