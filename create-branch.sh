#! /bin/bash

set -e

##### start of script

BRANCH_NAME=$1
NEW_VERSION_NUMBER=$2

GIT_BASE_URL="git@github.com:untangle/"

if [ -z "${BRANCH_NAME}" ] || [ -z "${NEW_VERSION_NUMBER}" ]; then
  echo "Usage: $0 <branch_name> <new_version_number>"
  exit 1
fi

# release-XY.Z -> current-releaseXYZ
BRANCH_DISTRIBUTION="current-$(echo $BRANCH_NAME | perl -pe 's/[\.\-]//g')"

## Create a temporary directory to clone everything
TEMP_DIST="/localhome/for-branching"
rm -rf "${TEMP_DIST}"
mkdir -p "$TEMP_DIST"
pushd $TEMP_DIST

for component in ngfw_src ngfw_pkgs ngfw_hades-pkgs ngfw_pkgtools ngfw_imgtools ngfw_upstream sync-settings classd runtests ; do
  component="$component"
  url="${GIT_BASE_URL}$component"
  git clone $url
  pushd $component
  git branch $BRANCH_NAME
  git push origin ${BRANCH_NAME}:$BRANCH_NAME
  popd
done

if [ -n "${NEW_VERSION_NUMBER}" ] ; then
  echo "Updating the version number in the mainline"
  pushd ngfw_pkgtools/resources
  git checkout master
  echo "${NEW_VERSION_NUMBER}.0" >| VERSION
  echo "${NEW_VERSION_NUMBER}" >| PUBVERSION
  echo "${BRANCH_DISTRIBUTION}" >| DISTRIBUTION
  git commit -a -m "Updating the version string to ${NEW_VERSION_NUMBER}, and the branch to ${BRANCH_DISTRIBUTION}"
  git push
  popd
fi

popd
rm -rf "${TEMP_DIST}"
