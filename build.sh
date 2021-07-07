#! /bin/bash

# Minimalist version of ngfw_pkgtools.git/make-build.sh so TravisCI
# and Jenkins can build packages.
#
# This is meant to be run in a disposable container.

## constants
PKGTOOLS=$(dirname $(readlink -f $0))
PKGTOOLS_VERSION=$(pushd $PKGTOOLS > /dev/null ; git describe --tags --always --long --dirty ; popd > /dev/null)
VERSION_FILE=debian/version

## env
export CCACHE_DISABLE=true
export CCACHE_DIR=/tmp

# arch default to the build arch
BUILD_ARCHITECTURE=$(dpkg-architecture -qDEB_BUILD_ARCH)
ARCHITECTURE=${ARCHITECTURE:-${BUILD_ARCHITECTURE}}

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

# use http_proxy if defined for apt
export http_proxy=$(perl -pe 's/.*"(.*?)".*/$1/' 2> /dev/null < /etc/apt/apt.conf.d/01proxy)

## functions
log() {
  echo "=== " $@
}

is-official-branch() {
  echo $1 | grep -qP '^(master|release-[\d.]+)$'
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

  if [[ "$pkg" =~ "/d-i" ]] && [[ $ARCHITECTURE != $BUILD_ARCHITECTURE ]] ; then
    # when cross-building d-i, build-dep chokes trying to install the
    # following packages
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

  source_name=$(dpkg-parsechangelog -S source)

  # bring resources/ from pkgtools into the source directory we cd'ed
  # in
  cp -r ${PKGTOOLS}/resources ./

  # bump version, except for kernels where it's manually managed
  if ! [[ "$pkg" =~ "/linux-" ]] ; then
    bash ${PKGTOOLS}/set-version.sh $TARGET_DISTRIBUTION $REPOSITORY
  fi

  # store this version
  version=$(dpkg-parsechangelog -S Version)
  echo $version >| $VERSION_FILE

  # collect existing versions
  is_present=0
  if [[ -z "$FORCE" ]] ; then
    is_present=1
    for binary_pkg in $(DEB_HOST_ARCH="$ARCHITECTURE" dh_listpackages $pkg) ; do
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
    # packages, create an ad-hoc one
    if ! [[ "$pkg" =~ "/linux-" ]] ; then
      quilt pop -a 2> /dev/null || true
      tar ca --exclude="*stamp*.txt" \
	     --exclude="*-stamp" \
	     --exclude="./debian" \
	     --exclude="todo" \
	     --exclude="staging" \
	     --exclude=".git" \
	     -f ../${source_name}_$(echo $version | perl -pe 's/(^\d+:|-.*)//').orig.tar.xz ../$(basename $pkg)
    fi

    # set profiles, if any
    if [[ $ARCHITECTURE != $BUILD_ARCHITECTURE ]] ; then
      build_profiles="cross"
      if [[ $ARCHITECTURE = "arm64" ]] &&  [[ "$pkg" =~ "/linux-" ]] ; then
	# FIXME: add pkg.linux.notools to profiles for now (NGFW-13152)
	build_profiles="${build_profiles},pkg.linux.notools"
      fi
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
    if [[ "$pkg" != "d-i" && $reason != "FAILURE" && -n "$UPLOAD" && "$UPLOAD" != 0 && "$UPLOAD" != "local" ]] ; then
      dput_profile=${DPUT_BASE_PROFILE}_${REPOSITORY}_${UPLOAD}
      changes_file=../${source_name}_$(perl -pe 's/^.+://' ${VERSION_FILE})*.changes
      dput -c ${PKGTOOLS}/dput.cf $dput_profile $changes_file || reason="FAILURE"
    fi
  fi

  # clean
  if [[ "$UPLOAD" != "local" ]] ; then
    find .. -maxdepth 1 -name "*$(perl -pe 's/(^.+:|-.*)//' ${VERSION_FILE})*"  -regextype posix-extended -regex ".*[._](upload|changes|udeb|deb|upload|dsc|build|buildinfo|diff.gz|debian.tar\..z|orig\.tar\..z|${ARCHITECTURE}\.tar\..z)" -delete
  fi

  if [[ "$NO_CLEAN" != 1 ]] ; then
    git checkout -- debian/changelog 2>&1 || true
    rm -f $VERSION_FILE
    fakeroot debian/rules clean
    quilt pop -a 2> /dev/null || true
    find . -type f -regex '\(.*-modules?-3.\(2\|16\).0-4.*\.deb\|core\)' -exec rm -f "{}" \;
  fi

  rm -fr resources

  # so it can be extracted by the calling shell when do-build is piped
  # into tee in VERBOSE mode
  echo $reason $version
}

## main

echo "pkgtools version ${PKGTOOLS_VERSION}"

# only allow Travis to upload packages if it's building from official
# branches, or from PRs targetting those
if ! is-official-branch $TRAVIS_BRANCH ; then
  UPLOAD=
fi

# set base distribution if none was passed
if [[ -z "$DISTRIBUTION" ]] ; then
  DISTRIBUTION=$(cat $PKGTOOLS/resources/DISTRIBUTION)
fi

# set target distribution for PRs
if [[ -n "$TRAVIS_PULL_REQUEST_BRANCH" ]] ; then
  DPUT_BASE_PROFILE=package-server-dev
  TARGET_DISTRIBUTION=$TRAVIS_PULL_REQUEST_BRANCH
else
  DPUT_BASE_PROFILE=package-server
  TARGET_DISTRIBUTION=$DISTRIBUTION
fi

# add mirrors for base and target distributions
echo "deb http://package-server/public/$REPOSITORY $DISTRIBUTION main non-free" > /etc/apt/sources.list.d/${DISTRIBUTION}.list
if [[ $DISTRIBUTION != $TARGET_DISTRIBUTION ]] ; then
  echo "deb http://package-server/dev/$REPOSITORY $TARGET_DISTRIBUTION main non-free" > /etc/apt/sources.list.d/${TARGET_DISTRIBUTION}.list
fi
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
