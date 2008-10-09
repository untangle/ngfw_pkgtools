#! /bin/bash

ARCH=$1
VERSION=$2
MARKER=$3

if [ -z "$ARCH" ] ; then
  DH_SWITCH=""
else
  DH_SWITCH="-a"  
fi

PACKAGE_NAME=`dh_listpackages $DH_SWITCH | head -1`

# highest version available
output=`apt-cache show ${PACKAGE_NAME} | grep -E '^Version: ' | head -1`

if [ ! $? = 0 ] || echo "$output" | grep -vq "$VERSION" ; then
  echo $MARKER
fi

exit 0
