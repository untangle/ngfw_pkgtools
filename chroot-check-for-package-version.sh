#! /bin/bash -x

PACKAGE_NAME=$1
VERSION=$2
DISTRIBUTION=$3

str="$PACKAGE_NAME is available in"

# corresponding chaos distribution
chaos=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')

# all distributions containing that version
output=$(apt-show-versions -p $PACKAGE_NAME -a | awk '/^'"$PACKAGE_NAME $VERSION"'/ {print $3}')

if echo "$output" | grep -q $DISTRIBUTION ; then
  echo $str $DISTRIBUTION
elif echo "$output" | grep -q $chaos ; then
  echo $str $chaos
fi

exit 0
