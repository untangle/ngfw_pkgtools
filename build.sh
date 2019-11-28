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
VERBOSE=${VERBOSE} # empty means "not verbose"
UPLOAD=${UPLOAD} # empty default means "no upload"

## functions
log() {
  echo "=== " $@
}

make-pkgtools() {
  make -f ${PKGTOOLS}/Makefile DISTRIBUTION=${DISTRIBUTION} REPOSITORY=${REPOSITORY} $@
}

do-build() {
  pkg=$1

  # bump version and create source tarball
  make-pkgtools version source create-dest-dir

  # collect existing versions
  version=$(cat debian/version)
  binary_pkg=$(dh_listpackages $pkg | tail -1)
  output=$(apt-show-versions -p '^'${binary_pkg}'$' -a -R)

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
    dpkg-buildpackage -i.* -sa --no-sign || reason="FAILURE"

    # upload only if needed
    if [[ -n "$UPLOAD" && "$UPLOAD" != 0 ]] ; then
      make-pkgtools move-debian-files release || reason="FAILURE"
    fi
  fi

  # clean
  make-pkgtools move-debian-files clean-untangle-files clean-build

  # so it can be extracted by the calling shell when do-build is piped
  # into tee in VERBOSE mode
  echo $reason $version
}

## main

echo "pkgtools version ${PKGTOOLS_VERSION}"

# add mirror targetting REPOSITORY & DISTRIBUTION
echo "deb http://package-server/public/$REPOSITORY $DISTRIBUTION main non-free" > /etc/apt/sources.list.d/${DISTRIBUTION}.list
apt-get update -q

# update u-d-build
apt install -q -y untangle-development-build

# update apt-show-versions cache
apt-show-versions -i

# main return code
rc=0

# iterate over packages to build
for pkg in $(awk -v repo=$REPOSITORY '$2 ~ repo && ! /^(#|$)/ {print $1}' build-order.txt) ; do
  log "BEGIN $pkg"

  if ! grep -qE '^Architecture:.*(amd64|any|all)' ${pkg}/debian/control ; then
    log "NO-ARCH-MATCH $pkg"
    continue
  fi

  if [[ -n "$PACKAGE" ]] && ! [[ $pkg = $PACKAGE ]] ; then
    log "NO-PKG-MATCH $pkg"
    continue
  fi

  pushd $pkg > /dev/null

  logfile=/tmp/${REPOSITORY}-${DISTRIBUTION}-${pkg//\//_}.log

  if [[ -n "$VERBOSE" && "VERBOSE" != 0 ]] ; then
    do-build $pkg 2>&1 | tee $logfile
    set $(tail -n 1 $logfile)
    reason=$1
    version=$2
  else
    do-build $pkg > $logfile 2>&1
  fi

  if [[ $reason == "FAILURE" ]] ; then
    let rc=rc+1 # global failure count
    [[ -n "$VERBOSE" ]] || cat $logfile
  fi

  rm -f $logfile

  log "$reason $pkg $version"
  popd > /dev/null
done

exit $rc
