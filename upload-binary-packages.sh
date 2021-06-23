#! /bin/bash

set -e

## constants
PKGTOOLS=$(dirname $(readlink -f $0))
USER=buildbot
BASE_DIR=/var/www/public

## functions
usage() {
  echo "Usage: $0 -r <repository> [-d <distribution>] [-h host] [-i ssh_key] [-A architecture] [-a]"
  echo -e "\t-a : all (recurse into subdirectories)"
  echo -e "\t-r : repository to target"
  echo -e "\t-d : distribution to target"
  echo -e "\t-i : host to upload to"
  echo -e "\t-h : ssh key to use"
  echo -e "\t-A <arch> : only act on architecture <arch>"
  exit 1
}

## main
HOST=package-server.untangle.int
ARCH=amd64
DISTRIBUTION=$(cat $PKGTOOLS/resources/DISTRIBUTION)
MAX_DEPTH="-maxdepth 1"

while getopts "r:d:A:h:i:a?" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    h) HOST=$OPTARG ;;
    i) SSH_KEY="-i $OPTARG" ;;
    a) MAX_DEPTH="" ;;
    A) ARCH=$OPTARG ;;
    h|\?) usage ;;
  esac
done

[ -z "$REPOSITORY" ] || [ -z "$DISTRIBUTION" ] && usage

DEBS=$(find . $MAX_DEPTH -iregex '.+_'$ARCH'\.u?deb$' | xargs)

[ $ARCH = amd64 ] && DEBS="$DEBS $(find . $MAX_DEPTH -iregex '.+_all\.u?deb$' | xargs)"

echo "About to upload:"

if [ -n "$DEBS" ] ; then
  for p in $DEBS ; do
    echo $p
    manifest=$(echo $p | perl -pe 's/u?deb$/'${REPOSITORY}_${DISTRIBUTION}.manifest'/')
    touch $manifest
    echo $manifest
  done

  MANIFESTS=$(find . $MAXDEPTH -name "*.manifest" | xargs)

  [ -n "$MANIFESTS" ] && scp -o StrictHostKeyChecking=no $SSH_KEY $DEBS $UDEBS $MANIFESTS $USER@$HOST:$BASE_DIR/$REPOSITORY/incoming

  rm -f $MANIFESTS
fi
