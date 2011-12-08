#! /bin/bash

REPOSITORY=$1
DISTRIBUTION=$2

# corresponding chaos distribution
chaos=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')
# corresponding nightly distribution
nightly=$(echo $DISTRIBUTION | perl -pe 's/chaos/nightly/')

echo deb http://mephisto/public/$REPOSITORY $DISTRIBUTION main premium upstream internal >| /etc/apt/sources.list
if [ $chaos != $DISTRIBUTION ] ; then
  echo deb http://mephisto/public/$REPOSITORY $chaos main premium upstream internal >> /etc/apt/sources.list
elif [ $nightly != $DISTRIBUTION ] ; then
  echo deb http://mephisto/public/$REPOSITORY $nightly main premium upstream internal >> /etc/apt/sources.list
fi
apt-get update
apt-get install --yes --force-yes apt-show-versions

exit 0
