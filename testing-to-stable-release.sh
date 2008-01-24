#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository>"
  exit 1
}

while getopts "r:" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))


[ -z "$REPOSITORY" ] && usage && exit 1

. `dirname $0`/release-constants.sh

### MAIN

# backup existing conf
backup_conf

## first we change things locally
# shift releases
perl -i -npe 's/(?<!un)stable/oldstable/' $REPREPRO_DISTRIBUTIONS_FILE
perl -i -npe 's/testing/stable/' $REPREPRO_DISTRIBUTIONS_FILE
#perl -i -npe 's/alpha/testing/' $REPREPRO_DISTRIBUTIONS_FILE

# create symlinks
$REPREPRO_BASE_COMMAND --delete createsymlinks

## then we push changes to updates.untangle.com
push_new_releases_names
