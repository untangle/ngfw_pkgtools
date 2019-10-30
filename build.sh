#! /bin/bash

# Minimalist version of ngfw_pkgtools.git/make-build.sh so TravisCI
# and Jenkins can build packages.
#
# This is meant to be run in a disposable container.

#set -x

## constants
PKGTOOLS=$(dirname $(readlink -f $0))
PKGTOOLS_VERSION=$(pushd $PKGTOOLS > /dev/null ; git describe --tags --always --long --dirty ; popd > /dev/null)

## env
REPOSITORY=${REPOSITORY:-buster}
DISTRIBUTION=${DISTRIBUTION:-current}
BRANCH=${BRANCH:-master}
PACKAGE=${PACKAGE} # empty default means "all"
UPLOAD=${UPLOAD} # empty default means "no upload"

## functions
log() {
  echo "===" $@
}

make-pkgtools() {
  make -f ${PKGTOOLS}/Makefile DISTRIBUTION=${DISTRIBUTION} REPOSITORY=${REPOSITORY} $@
}

## main

echo "pkgtools version ${PKGTOOLS_VERSION}"

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
    log "NO-ARCH-MATCH $pkg"
    continue
  fi

  if [[ -n "$PACKAGE" ]] && ! [[ $pkg =~ $PACKAGE ]] ; then
    log "NO-PKG-MATCH $pkg"
    continue
  fi

  pushd $pkg > /dev/null

  logfile=/tmp/${REPOSITORY}-${DISTRIBUTION}-${pkg}.log

  {
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
    dpkg-buildpackage -sa --no-sign || reason="FAILURE"

    # upload only if needed
    if [[ -n "$UPLOAD" ]] ; then
      make-pkgtools move-debian-files release || reason="FAILURE"
    fi
  fi

  # clean
  make-pkgtools clean-untangle-files clean-build
  } > $logfile 2>&1

  if [[ $reason == "FAIL" ]] ; then
    cat $logfile
  fi

  rm -f $logfile

  log "$reason $pkg $version"
  popd > /dev/null
done
