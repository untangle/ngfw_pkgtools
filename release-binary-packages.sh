#! /bin/bash -x

set -e

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> [-h host] [-A architecture] [-a]"
  echo -e "\t-a : all (recurse into subdirectories)"
  echo -e "\t-A <arch> : only act on architecture <arch>"
  exit 1
}

MAX_DEPTH="-maxdepth 1"

while getopts "r:d:A:ah?" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    h) HOST=$OPTARG ;;
    a) MAX_DEPTH="" ;;
    A) ARCH="$OPTARG" ;;
    h|\?) usage ;;
  esac
done
ARCH=${ARCH:-i386}
HOST=${HOST:-mephisto}

[ -z "$REPOSITORY" ] || [ -z "$DISTRIBUTION" ] && usage

DEBS=$(find . $MAX_DEPTH -iregex '.+_\(all\|'$ARCH'\)\.u?deb$' | xargs)

echo "About to upload:"

if [ -n "$DEBS" ] ; then
  for p in $DEBS ; do
    echo $p
    manifest=$(echo $p | perl -pe 's/u?deb$/'${REPOSITORY}_${DISTRIBUTION}.manifest'/')
    touch $manifest
    echo $manifest
  done

  MANIFESTS=$(find . $MAXDEPTH -name "*.manifest" | xargs)
  
  lftp -e "set net:max-retries 1 ; cd $REPOSITORY/incoming ; put $DEBS $UDEBS $MANIFESTS ; exit" $HOST
  rm -f $MANIFESTS
fi
