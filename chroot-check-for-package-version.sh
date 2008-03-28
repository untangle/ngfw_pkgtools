#! /bin/bash

PACKAGE_NAME=$1
REPOSITORY=$2
DISTRIBUTION=$3
VERSION=$4
MARKER=$5

# we only need this one
echo deb http://mephisto/public/$REPOSITORY $DISTRIBUTION main premium upstream > /etc/apt/sources.list

apt-get update -q

# highest version available
output=`apt-cache show ${PACKAGE_NAME} | grep -E '^Version: ' | head -1`

if [ ! $? = 0 ] || echo "$output" | grep -vq "$VERSION" ; then
  echo $MARKER
fi

exit 0
