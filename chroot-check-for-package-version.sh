#! /bin/bash

PACKAGE_NAME=$1
VERSION=$2
MARKER=$3

# highest version available
output=`apt-cache show ${PACKAGE_NAME} | grep -E '^Version: ' | head -1`

if [ ! $? = 0 ] || echo "$output" | grep -vq "$VERSION" ; then
  echo $MARKER
fi

exit 0
