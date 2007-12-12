#! /bin/bash -x

PACKAGE_NAME=$1
VERSION=$2
MARKER=$3

output=`apt-cache show ${PACKAGE_NAME}`
[ $? = 0 ] && echo "$output" | awk '/Version: '"$VERSION"'/ {print "'"$MARKER"'"}'
