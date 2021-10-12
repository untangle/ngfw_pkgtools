#! /bin/bash

set -e

## functions
usage() {
  echo "Usage: $0 [-s] <product> <branch_name> <new_version_number>"
  echo "   where <product> can be NGFW or WAF"
  exit 1
}

set_resources_version() {
  local version=$1
  echo $version >| resources/PUBVERSION
  echo ${version}.0 >| resources/VERSION
  git commit -a -m "Updating resources: version=$version"
}

set_resources_distribution() {
  local branch=$1
  echo $branch >| resources/DISTRIBUTION
  git commit -a -m "Updating resources: distribution=$branch"
}

## constants
GIT_BASE_URL="git@github.com:untangle"
NGFW_REPOSITORIES="ngfw_src ngfw_pkgs ngfw_hades-pkgs ngfw_vendor-pkgs ngfw_imgtools ngfw_kernels debian-cloud-images ngfw_upstream sync-settings classd runtests"
WAF_REPOSITORIES="sync-settings client-license-service waf waf_pkgs waf_ui ngfw_imgtools"

## main

# CLI parameters
while getopts "A:T:C:shwr:f:v:" opt ; do
  case "$opt" in
    s) simulate="-n" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))

if [ $# != 3 ] ; then
  usage
fi

PRODUCT=$1
BRANCH_NAME=$2
NEW_VERSION_NUMBER=$3

case $PRODUCT in
  NGFW)
    repositories=$NGFW_REPOSITORIES
    pkgtools_branch=master ;;
  WAF)
    repositories=$WAF_REPOSITORIES
    pkgtools_branch=waf-master ;;
  *) usage ;;
esac

# create a temporary directory to clone everything
tmp_dir="/localhome/for-branching"
rm -rf "${tmp_dir}"
mkdir -p "$tmp_dir"
pushd $tmp_dir

# branch pkgtools and update branch in resources/
git clone ${GIT_BASE_URL}/ngfw_pkgtools
pushd ngfw_pkgtools
git checkout -t origin/${pkgtools_branch}
git checkout -b $BRANCH_NAME
set_resources_distribution $BRANCH_NAME
git push $simulate origin ${BRANCH_NAME}:${BRANCH_NAME}
popd

# branch each repository except pkgtools
for repository in ${repositories} ; do
  url="${GIT_BASE_URL}/$repository"
  git clone --depth 2 $url
  pushd $repository
  git checkout -b $BRANCH_NAME
  git push $simulate origin ${BRANCH_NAME}:${BRANCH_NAME}
  popd
done

# set new version in pkgtools/resources
pushd ngfw_pkgtools
git checkout ${pkgtools_branch}
set_resources_version $NEW_VERSION_NUMBER
git push $simulate origin ${pkgtools_branch}:${pkgtools_branch}
popd

# cleanup
popd
[[ -n "$simulate" ]] || rm -rf "${tmp_dir}"
