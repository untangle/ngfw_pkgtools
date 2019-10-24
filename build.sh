#! /bin/bash

# Minimalist version of ngfw_pkgtools.git/make-build.sh so TravisCI
# and Jenkins can build packages.
#
# This is meant to be run in a disposable container.

#set -x

## constants
PKGTOOLS=$(dirname $(readlink -f $0))
PKGTOOLS_VERSION=$(git describe --tags --always --long)

## env
REPOSITORY=${REPOSITORY:-buster}
DISTRIBUTION=${DISTRIBUTION:-current}
BRANCH=${BRANCH:-master}
PACKAGE=${PACKAGE} # empty default means "all"
UPLOAD=${UPLOAD} # empty default means "no upload"

## functions
log() {
  echo "=== " $@
}

make-pkgtools() {
  make -f ${PKGTOOLS}/Makefile DISTRIBUTION=${DISTRIBUTION} REPOSITORY=${REPOSITORY} $@
}

## main

# do not gzip apt lists files (for apt-show-versions)
rm /etc/apt/apt.conf.d/docker-gzip-indexes

# add mirror targetting REPOSITORY & DISTRIBUTION
echo "deb http://package-server/public/$REPOSITORY $DISTRIBUTION main non-free" > /etc/apt/sources.list.d/${DISTRIBUTION}.list
apt-get update

# update u-d-build
apt install -y untangle-development-build

# install apt-show-versions
apt install -y apt-show-versions

# iterate over packages to build
awk -v repo=$REPOSITORY '$2 ~ repo {print $1}' build-order.txt | while read pkg ; do
  log "BEGIN $pkg"

  if ! grep -qE '^Architecture:.*(amd64|any|all)' ${pkg}/debian/control ; then
    log "END $pkg NO-ARCH-MATCH"
    continue
  fi

  if [[ -n "$PACKAGE" ]] && ! [[ $pkg =~ $PACKAGE ]] ; then
    log "END $pkg NO-PKG-MATCH"
    continue
  fi

  pushd $pkg > /dev/null

  # bump version and create source tarball
  make-pkgtools version source create-dest-dir

  # collect existing versions
  version=$(cat debian/version)
  output=$(apt-show-versions -p '^'${pkg}'$' -a -R)

  # ... and build depending on that
  if echo "$output" | grep -qP " ${version//+/.}" ; then # no need to build
    # move orig tarball out of the way
    make-pkgtools move-debian-files
    reason="ALREADY-PRESENT"
  else # build it
    reason="SUCCESS"

    # install build dependencies
    apt build-dep -y .

    # build package
    dpkg-buildpackage -sa --no-sign || reason="FAIL"

    # upload only if needed
    if [[ -n "$UPLOAD" ]] ; then
      make-pkgtools move-debian-files release || reason="FAIL"
    fi
  fi

  # clean
  make-pkgtools clean-untangle-files clean-build

  log "END $pkg $reason $version"
  popd > /dev/null
done
