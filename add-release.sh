#! /bin/bash

usage() {
  echo "Usage: $0 <version> <name> [<symbolic-name>]"
  exit 1
}

while getopts "h" opt ; do
  case "$opt" in
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
  usage
fi

. release-constants.sh

version=$1
name=$2
symbolic_name=${3:-$1}

# MAIN
if grep -q "^Version: ${version}\$" $REPREPRO_DISTRIBUTIONS_FILE ; then
  echo "$version already exists in ${REPREPRO_DISTRIBUTIONS_FILE}, giving up"
  exit 2
elif  grep -q -E "^Codename: ${name}\$" $REPREPRO_DISTRIBUTIONS_FILE ; then
  echo "$name already exists in ${REPREPRO_DISTRIBUTIONS_FILE}, giving up"
  exit 2
elif grep -q -E "^Suite: ${symbolic_name}\$" $REPREPRO_DISTRIBUTIONS_FILE ; then
  # just a warning
  echo "$symbolic_name already exists in ${REPREPRO_DISTRIBUTIONS_FILE}, this will change it"
fi

# backup existing conf
tar czvf /var/www/conf.`date -Iseconds`.tar.gz /var/www/conf

# remove existing codename; won't do anything if it doesn't exist already
perl -i npe "s/^Suite: ${symbolic_name}\n//" $REPREPRO_DISTRIBUTIONS_FILE

## first we change things locally
# add the new release
perl -npe "s/\+SYMBOLIC_NAME\+/$symbolic_name/ ; s/\+VERSION\+/$version/ ; s/\+CODENAME\+/$name/" ${REPREPRO_CONF_DIR}/distribution.template >> $REPREPRO_DISTRIBUTIONS_FILE
# add the corresponding update section in the updates file
perl -npe "s/\+SYMBOLIC_NAME\+/$symbolic_name/ ; s/\+VERSION\+/$version/ ; s/\+CODENAME\+/$name/" ${REPREPRO_CONF_DIR}/updates.template >> ${REPREPRO_CONF_DIR}/updates
# create symlinks
$REPREPRO_BASE_COMMAND --delete createsymlinks

## then we push changes to updates.untangle.com
# copy files
scp $REPREPRO_DISTRIBUTIONS_FILE ${REPREPRO_CONF_DIR}/updates ${REMOTE_USER}@${REMOTE_SERVER}:${REPREPRO_CONF_DIR}/
# create symlinks
$REPREPRO_REMOTE_COMMAND --delete createsymlinks
