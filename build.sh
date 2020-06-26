#! /bin/bash

# Minimalist version of ngfw_pkgtools.git/make-build.sh so TravisCI
# and Jenkins can build packages.
#
# This is meant to be run in a disposable container.

## constants
PKGTOOLS=$(dirname $(readlink -f $0))
PKGTOOLS_VERSION=$(pushd $PKGTOOLS > /dev/null ; git describe --tags --always --long --dirty ; popd > /dev/null)

## env

# arch default to the build arch
ARCHITECTURE=${ARCHITECTURE:-$(dpkg-architecture -qDEB_BUILD_ARCH)}

# the following variable re-assignments are no-ops, and are here just
# for documentation
REPOSITORY=${REPOSITORY}
DISTRIBUTION=${DISTRIBUTION}
TRAVIS_BRANCH=${TRAVIS_BRANCH}
TRAVIS_PULL_REQUEST_BRANCH=${TRAVIS_PULL_REQUEST_BRANCH}
PACKAGE=${PACKAGE} # empty default means "all"
VERBOSE=${VERBOSE} # empty means "not verbose"
UPLOAD=${UPLOAD} # empty default means "no upload"
FORCE=${FORCE} # emtpy means "do not force build"
DEBUG=${DEBUG} # emtpy means "no debugging"
SSH_KEY=${SSH_KEY} # empty means "no key"
NO_CLEAN=${NO_CLEAN} # empty default means "perform cleaning post build"

if [[ -n "$DEBUG" ]] ; then
   set -x
   VERBOSE=1 # also force VERBOSE
fi

# use default distribution from resources/ if none was passed
if [[ -z "$DISTRIBUTION" ]] ; then
  DISTRIBUTION=$(cat $PKGTOOLS/resources/DISTRIBUTION)
fi

# only allow Travis to upload packages if it's building from official
# branches; this means taking into account the pull requests targetting
# those
if ! echo $TRAVIS_BRANCH | grep -qP '^(master|release-[\d.]+)$' || [ -n "$TRAVIS_PULL_REQUEST_BRANCH" ] ; then
  export UPLOAD=
fi

# use http_proxy if defined for apt
export http_proxy=$(perl -pe 's/.*"(.*?)".*/$1/' 2> /dev/null < /etc/apt/apt.conf.d/01proxy)

## functions
log() {
  echo "=== " $@
}

make-pkgtools() {
  make -f ${PKGTOOLS}/Makefile DISTRIBUTION=${DISTRIBUTION} REPOSITORY=${REPOSITORY} $@
}

wait-for-pid() {
  pid=$1
  delay=1
  delay_msg=30
  i=0
  while ps hp $pid > /dev/null ; do
    let i=i+1
    if [[ $(( $i % $delay_msg )) = 0 ]] ; then
      echo "... still waiting for PID ${pid} every ${delay}s, next message in ${delay_msg}s"
    fi
    sleep $delay
  done
}

install-build-deps() {
  pkg=$1
  profiles=$2

  if [[ "$pkg" =~ "/d-i" ]] && [[ $ARCHITECTURE != "amd64" ]] ; then
    # when cross-building d-i, build-dep chokes trying to install the
    # following packages and qforcing arch-spec
    apt install -y apt-utils bf-utf-source mklibs win32-loader
  elif [[ -n "$profiles" ]] ; then
    apt -o Dpkg::Options::="--force-overwrite" build-dep -y --build-profiles $profiles --host-architecture $ARCHITECTURE .
  else
    apt -o Dpkg::Options::="--force-overwrite" build-dep -y --host-architecture $ARCHITECTURE .
  fi
}

do-build() {
  pkg=$1
  shift
  dpkg_buildpackage_options="$@"

  # bring resources/ from pkgtools into the source directory we cd'ed
  # in
  cp -r ${PKGTOOLS}/resources ./

  # bump version
  if [[ "$pkg" =~ "/linux-" ]] ; then
    # for kernels, the version is manually managed
    dpkg-parsechangelog -S Version > debian/version
  else
    make-pkgtools version
  fi
  make-pkgtools create-dest-dir
  version=$(cat debian/version)

  # collect existing versions
  is_present=0
  if [[ -z "$FORCE" ]] ; then
    is_present=1
    for binary_pkg in $(dh_listpackages $pkg) ; do
      output=$(apt-show-versions -p '^'${binary_pkg}'$' -a -R)
      if ! echo "$output" | grep -qP ":(all|${ARCHITECTURE}) ${version//+/.}" ; then
	is_present=0
	break
      fi
    done
  fi

  # ... and build only if needed
  if [[ $is_present == 1 ]] ; then
    reason="ALREADY-PRESENT"
  else # build it
    reason="SUCCESS"

    # for kernels, we already have a source tarball; for other
    # packages, create one
    if ! [[ "$pkg" =~ "/linux-" ]] ; then # 
      make-pkgtools source
    fi

    # set profiles, if any
    if [[ $ARCHITECTURE != "amd64" ]] ; then
      build_profiles="cross"
    fi
    if [[ -f debian/untangle-build-profiles ]] ; then
      build_profiles="${build_profiles},$(cat debian/untangle-build-profiles)"
    fi
    if [[ -n "$build_profiles" ]] ; then
      dpkg_buildpackage_options="$dpkg_buildpackage_options --build-profiles=$build_profiles"
    fi

    # install build dependencies, and build package
    install-build-deps $pkg "$build_profiles" \
      && dpkg-buildpackage --host-arch $ARCHITECTURE -i.* $dpkg_buildpackage_options --no-sign \
      || reason=FAILURE

    # upload: never for d-i, and only if successful and UPLOAD specified
    if [[ "$pkg" != "d-i" && $reason != "FAILURE" && -n "$UPLOAD" && "$UPLOAD" != 0 ]] ; then
      make-pkgtools DPUT_METHOD=${UPLOAD} move-debian-files release || reason="FAILURE"
    fi
  fi

  # clean
  [[ "$UPLOAD" == "local" ]] || make-pkgtools move-debian-files
  [[ "$NO_CLEAN" == 1 ]] || make-pkgtools clean-untangle-files clean-build
  rm -fr resources

  # so it can be extracted by the calling shell when do-build is piped
  # into tee in VERBOSE mode
  echo $reason $version
}

## main

echo "pkgtools version ${PKGTOOLS_VERSION}"

# add mirror targetting REPOSITORY & DISTRIBUTION
echo "deb http://package-server/public/$REPOSITORY $DISTRIBUTION main non-free" > /etc/apt/sources.list.d/${DISTRIBUTION}.list
apt-get update -q

# ssh
if [[ "$SSH_KEY" =~ /tmp/ ]] ; then
  eval $(ssh-agent)
  ssh-add $SSH_KEY
  mkdir -p ~/.ssh
  cat >> ~/.ssh/config <<EOF
Host *
  IdentityFile /tmp/travis-buildbot.rsa
  StrictHostKeyChecking no
EOF
fi

if [[ "$1" == "setup-only" ]] ; then
 # we're not interested in building packages
 exit 0
fi

# update apt-show-versions cache
apt-show-versions -i

# main return code
rc=0

# iterate over packages to build
for pkg in $(awk -v repo=$REPOSITORY '$2 ~ repo && ! /^(#|$)/ {print $1}' build-order.txt) ; do
  log "BEGIN $pkg"

  if [[ -n "$PACKAGE" ]] && ! [[ $pkg = $PACKAGE ]] ; then
    log "NO-PKG-MATCH $pkg"
    continue
  fi

  # the kernel source tree needs to be prepared
  if [[ "$pkg" =~ "/linux-" ]] ; then
    pushd $(dirname "$pkg") > /dev/null
    make patch control-real
    popd > /dev/null    
  fi

  # to build or not to build, depending on target architecture and
  # package specs
  arches_to_build="${ARCHITECTURE}|any" # always build arch-dep
  if [[ $ARCHITECTURE == "amd64" ]] ; then
    # also build arch-indep packages
    arches_to_build="${arches_to_build}|all"
    # build source *and* binary packages
    DPKG_BUILDPACKAGE_OPTIONS="-sa"
  else
    # only build binary packages
    DPKG_BUILDPACKAGE_OPTIONS="-B"
  fi
  if ! grep -qE "^Architecture:.*(${arches_to_build})" ${pkg}/debian/control ; then
    log "NO-ARCHITECTURE-MATCH $pkg"
    continue
  fi

  pushd $pkg > /dev/null

  logfile=/tmp/${REPOSITORY}-${DISTRIBUTION}-${pkg//\//_}.log

  if [[ -n "$VERBOSE" && "$VERBOSE" != 0 ]] ; then
    do-build $pkg $DPKG_BUILDPACKAGE_OPTIONS 2>&1 | tee $logfile
  else
    do-build $pkg $DPKG_BUILDPACKAGE_OPTIONS > $logfile 2>&1 &
    wait-for-pid $!
  fi

  # always extract reason & version from logfile
  set $(tail -n 1 $logfile)
  reason=$1
  version=$2

  if [[ $reason == "FAILURE" ]] ; then
    let rc=rc+1 # global failure count
    [[ -n "$VERBOSE" && "$VERBOSE" != 0 ]] || cat $logfile
  fi

  rm -f $logfile

  log "$reason $pkg $version"
  popd > /dev/null
done

exit $rc
