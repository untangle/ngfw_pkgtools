#! /bin/bash -x

PACKAGE_NAME=$1
VERSION=$2
MARKER=$3

output=`apt-cache show ${PACKAGE_NAME} | grep -E '^Version: '`
if [ ! $? = 0 ] || echo "$output" | grep -vq "$VERSION" ; then
  echo $MARKER
fi

exit 0