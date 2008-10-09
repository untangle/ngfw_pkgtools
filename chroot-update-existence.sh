#! /bin/bash

REPOSITORY=$1
DISTRIBUTION=$2

# we only need this one
echo deb http://mephisto/public/$REPOSITORY $DISTRIBUTION main premium upstream > /etc/apt/sources.list

apt-get update

exit 0
