#! /bin/bash

usage() {
  echo "Usage: $0 <version> <fromName> <toName>"
  exit 1
}

while getopts "h" opt ; do
  case "$opt" in
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# -eq 2 ]; then
  usage
fi

. release-constants.sh

fromName=$1
toName=$2

# MAIN
$REPREPRO_BASE_COMMAND listfilter $fromName 'Package' | awk '{print $2}' | xargs $REPREPRO_BASE_COMMAND copy $toName $fromName
