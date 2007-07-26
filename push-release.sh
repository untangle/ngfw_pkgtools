#! /bin/bash

usage() {
  echo "Usage: $0 [-s|--simulate] <release>"
  exit 1
}

while getopts "sh" opt ; do
  case "$opt" in
    s) simulate=1 ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 1 ] ; then
  usage
fi

. release-constants.sh

# MAIN
if [ -z "$simulate" ] ; then
  reprepro_action="update"
else
  reprepro_action="checkupdate"
fi

$REPREPRO_REMOTE_COMMAND $reprepro_action $1
