#! /bin/bash

set -x

PKG_NAME=${1/-source}-source

case $PKG_NAME in
  openswan*) PKG_NAME="openswan-modules-source" ;; # upstream package
esac

rm -f /usr/src/*deb

apt-get install --yes --force-yes module-assistant untangle-keyring
apt-get update

versions=$(apt-cache search linux-headers | awk '/untangle-/ {gsub("linux-headers-", "", $1) ; print $1}' | sort -u)

echo $version

for kvers in $versions ; do
  echo "=============================================== $kvers"
  module-assistant -t -f -l $kvers -i prepare
  module-assistant -t -f -l $kvers auto-build $PKG_NAME
done

exit 0
