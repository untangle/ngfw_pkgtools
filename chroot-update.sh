#! /bin/sh

echo deb http://mephisto/public/$1 $2 main >> /etc/apt/sources.list
apt-get update