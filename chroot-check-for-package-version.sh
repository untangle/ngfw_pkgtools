#! /bin/bash -x

PACKAGE_NAME=$1
VERSION=$2
DISTRIBUTION=$3

if [ $# != 3 ] ; then
  echo "Usage: $0 <package> <version> <distribution>"
  exit 1
fi

str="$PACKAGE_NAME is available in"

# corresponding chaos distribution
chaos=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')
# corresponding nightly distribution
nightly=$(echo $DISTRIBUTION | perl -pe 's/chaos/nightly/')

# all distributions containing that version
apt-show-versions -p $PACKAGE_NAME -a >&2
output=$(apt-show-versions -p $PACKAGE_NAME -a | awk '/^'"$PACKAGE_NAME ${VERSION/+/\+}"'/ {print $3}')

if echo "$output" | grep -q $DISTRIBUTION ; then
  echo $str $DISTRIBUTION
elif echo "$output" | grep -q $chaos ; then
  echo $str $chaos
elif echo "$output" | grep -q $nightly ; then
  echo $str $nightly
fi

exit 0
