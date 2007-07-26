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
  echo "$symbolic_name already exits in ${REPREPRO_DISTRIBUTIONS_FILE}, this will change it"
  perl -npe "s/Suite: $symbolic_name$//" $REPREPRO_DISTRIBUTIONS_FILE
fi

perl -npe "s/+SYMBOLIC_NAME+/$symbolic_name/ ; s/+VERSION+/$version/ ; s/+CODENAME+/$name/" ${REPREPRO_CONF_DIR}/distribution.template
perl -npe "s/+SYMBOLIC_NAME+/$symbolic_name/ ; s/+VERSION+/$version/ ; s/+CODENAME+/$name/" ${REPREPRO_CONF_DIR}/update.template
