#! /bin/bash

usage() {
  echo "Usage: $0"
  exit 1
}

. release-constants.sh

### MAIN

# backup existing conf
backup_conf

## first we change things locally
# shift releases
perl -i -npe 's/(?<!un)stable/oldstable/' $REPREPRO_DISTRIBUTIONS_FILE
perl -i -npe 's/testing/stable/' $REPREPRO_DISTRIBUTIONS_FILE
perl -i -npe 's/alpha/testing/' $REPREPRO_DISTRIBUTIONS_FILE
# create symlinks
$REPREPRO_BASE_COMMAND --delete createsymlinks

## then we push changes to updates.untangle.com
push_new_releases_names
