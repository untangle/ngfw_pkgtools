#! /bin/bash

REPOSITORY=$1
DISTRIBUTION=$2

echo "[update-existence] Called with REPOSITORY=$REPOSITORY and DISTRIBUTION=$DISTRIBUTION" >&2

echo deb http://package-server/public/$REPOSITORY $DISTRIBUTION main main/debian-installer non-free citrix >| /etc/apt/sources.list

echo "[update-existence] sources.list is :" >&2
cat /etc/apt/sources.list >&2

apt-get update
apt-get install --yes --force-yes apt-show-versions gawk

exit 0
