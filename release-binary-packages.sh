#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> [a]"
  echo -e "\t-a : all (recurse into subdirectories)"
  exit 1
}

MAX_DEPTH="-maxdepth 1"

while getopts "r:d:ah?" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    a) MAX_DEPTH="" ;;
    h|\?) usage ;;
  esac
done

[ -z "$REPOSITORY" ] || [ -z "$DISTRIBUTION" ] && usage

DEBS=$(find . $MAX_DEPTH -name "*.deb" | xargs)

if [ -n "$DEBS" ] ; then
  for p in $DEBS ; do
    touch ${p/.deb/.$REPOSITORY_$DISTRIBUTION.manifest}
  done

  MANIFESTS=$(find . $MAXDEPTH -name "*.manifest" | xargs)
  lftp -e "set net:max-retries 1 ; cd incoming ; put $DEBS $MANIFESTS ; exit" mephisto
  rm -f $MANIFESTS
fi
