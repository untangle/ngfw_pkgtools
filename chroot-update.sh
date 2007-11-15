#! /bin/bash

echo deb http://mephisto/public/$1 $2 main upstream >> /etc/apt/sources.list
apt-get update