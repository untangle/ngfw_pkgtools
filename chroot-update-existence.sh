#! /bin/bash

REPOSITORY=$1
DISTRIBUTION=$2

echo "[update-existence] Called with REPOSITORY=$REPOSITORY and DISTRIBUTION=$DISTRIBUTION" >&2

# corresponding current distribution
current=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')
# corresponding nightly distribution
nightly=$(echo $DISTRIBUTION | perl -pe 's/current/nightly/')

echo deb http://package-server/public/$REPOSITORY $DISTRIBUTION main main/debian-installer premium non-free upstream internal >| /etc/apt/sources.list
if [ $current != $DISTRIBUTION ] ; then
  echo deb http://package-server/public/$REPOSITORY $current main main/debian-installer premium non-free upstream internal >> /etc/apt/sources.list
elif [ $nightly != $DISTRIBUTION ] ; then
  echo deb http://package-server/public/$REPOSITORY $nightly main main/debian-installer premium non-free upstream internal >> /etc/apt/sources.list
fi

echo "[update-existence] sources.list is :" >&2
cat /etc/apt/sources.list >&2

apt-get update
apt-get install --yes --force-yes apt-show-versions gawk

exit 0
