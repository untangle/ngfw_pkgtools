#! /bin/bash

PACKAGE_NAME=$1
VERSION=$2
DISTRIBUTION=$3

if [ $# != 3 ] ; then
  echo "Usage: $0 <package> <version> <distribution>"
  exit 1
fi

echo "[existence] Looking for $PACKAGE_NAME version $VERSION for $DISTRIBUTION" >&2
echo "[existence] sources.list is :" >&2
cat /etc/apt/sources.list >&2

str="$PACKAGE_NAME is available in"

# corresponding chaos distribution
chaos=$(echo $DISTRIBUTION | perl -pe 's/nightly/chaos/')
# corresponding nightly distribution
nightly=$(echo $DISTRIBUTION | perl -pe 's/chaos/nightly/')

apt-get install --yes --force-yes apt-show-versions

# all distributions containing that version
echo "[existence] apt-show-versions result:" >&2
apt-show-versions -p '^'$PACKAGE_NAME'$' -a -R >&2

output=$(apt-show-versions -p '^'$PACKAGE_NAME'$' -a -R | awk '/^'"$PACKAGE_NAME(:[a-z0-9]+)? ${VERSION//+/\+}"'/ {print $3}')
echo "[existence] Matching line:" >&2
echo $output >&2

if echo "$output" | grep -q $DISTRIBUTION ; then
  echo $str $DISTRIBUTION
elif echo "$output" | grep -q $chaos ; then
  echo $str $chaos
elif echo "$output" | grep -q $nightly ; then
  echo $str $nightly
fi

exit 0
