#! /bin/bash

set -x

PACKAGE_NAME=$1
VERSION=$2
REPOSITORY=$3
DISTRIBUTION=$4

if [ $# != 4 ] ; then
  echo "Usage: $0 <package> <version> <distribution> <repository>"
  exit 1
fi

echo "[existence] Looking for $PACKAGE_NAME version $VERSION for $DISTRIBUTION"
echo "[existence] sources.list is :"
cat /etc/apt/sources.list

str="$PACKAGE_NAME is available in"

apt-get install --yes --force-yes apt-show-versions gawk

# all distributions containing that version
tmpFile=$(mktemp /tmp/${PACKAGE_NAME}-${REPOSITORY}-${DISTRIBUTION}-XXXXXX)
apt-show-versions -p '^'$PACKAGE_NAME'$' -a -R > $tmpFile

echo "[existence] apt-show-versions output:"
cat $tmpFile

output=$(gawk '/^'"$PACKAGE_NAME(:[a-z0-9]+)? ${VERSION//+/.}"'/ {print $3 ; exit}' < $tmpFile)
echo "[existence] 1st distribution matching this version:" $output

case $output in
  $DISTRIBUTION) echo $str $DISTRIBUTION ;;
esac

rm $tmpFile

exit 0
