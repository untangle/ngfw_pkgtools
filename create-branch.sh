#! /bin/bash

set -e

## functions
set_resources_version() {
  local version=$1
  echo $version >| resources/PUBVERSION
  echo ${version}.0 >| resources/VERSION
  git commit -a -m "Updating resources: version=$version"
}

set_resources_branch() {
  local branch=$1
  echo $branch >| resources/DISTRIBUTION
  git commit -a -m "Updating resources: branch=$branch"
}

## constants
GIT_BASE_URL="git@github.com:untangle"
REPOSITORIES="ngfw_pkgtools ngfw_src ngfw_pkgs ngfw_hades-pkgs ngfw_imgtools debian-cloud-images ngfw_upstream sync-settings classd runtests"


## main

# CLI parameters
BRANCH_NAME=$1
NEW_VERSION_NUMBER=$2

if [ -z "${BRANCH_NAME}" ] || [ -z "${NEW_VERSION_NUMBER}" ]; then
  echo "Usage: $0 <branch_name> <new_version_number>"
  exit 1
fi

# create a temporary directory to clone everything
TEMP_DIST="/localhome/for-branching"
rm -rf "${TEMP_DIST}"
mkdir -p "$TEMP_DIST"
pushd $TEMP_DIST

# branch each repository
for repository in $REPOSITORIES ; do
  url="${GIT_BASE_URL}/$repository"
  git clone --depth 2 $url
  pushd $repository
  git checkout -b $BRANCH_NAME
  if [[ $repository == ngfw_pkgtools ]] ; then
    # release-XY.Z -> current-releaseXYZ
    branch_distribution=current-$(echo $BRANCH_NAME | perl -pe 's/[\.\-]//g')
    # bump distribution in pkgtools:release
    set_resources_branch $branch_distribution
  fi
  git push origin ${BRANCH_NAME}:$BRANCH_NAME
  popd
done

# bump version in pkgtools:master
pushd ngfw_pkgtools
git checkout master
set_resources_version ${NEW_VERSION_NUMBER}
git push origin master:master
popd

# cleanup
popd
rm -rf "${TEMP_DIST}"
