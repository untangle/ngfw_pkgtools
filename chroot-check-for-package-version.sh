#! /bin/bash

PACKAGE_NAME=$1
VERSION=$2
DISTRIBUTION=$3

str="$PACKAGE_NAME is available in"

# corresponding chaos distribution
chaos=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')

# all distributions containing that version
output=$(apt-show-versions -p $PACKAGE_NAME -a | awk '/^'"$PACKAGE_NAME $VERSION"'/ {print $3}')

if grep -q $DISTRIBUTION "$output" ; then
  echo $str $DISTRIBUTION
elif grep -q $chaos $output ; then
  echo $str $chaos
fi

exit 0
