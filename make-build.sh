#!/bin/bash

CHROOT_BASE=

usage() {
  echo "$0 -r <repository> -d <distribution> -b <builddir> [-n] [-a <arch>] [-v <version>] [-u] [-e] [-c] [-m]"
  exit 1
}

DEFAULT_TARGETS="source pkg-chroot"

### CLI args
while getopts r:b:d:v:a:uencmh option ; do
  case "$option" in
    r) TARGET_REP="$OPTARG" ;;
    b) BUILD_DIR="$OPTARG" ;;
    d) DISTRIBUTION="$OPTARG" ;;
    v) VERSION="$OPTARG" ;;
    n) BINARY_UPLOAD="BINARY_UPLOAD=true" ;;
    c) CHECKROOT_UPGRADE="true" ;;
    u) RELEASE="release" ;;
    a) ARCH="$OPTARG" ;;
    e) CHECK_EXISTENCE="check-existence" ;;
    m) DEFAULT_TARGETS="kernel-module-chroot" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
[ -z "$ARCH" ] && ARCH=i386
MAKE_VARIABLES="DISTRIBUTION=${DISTRIBUTION} REPOSITORY=${TARGET_REP} ${BINARY_UPLOAD} TIMESTAMP=`date +%Y-%m-%dT%H%M%S_%N`"
if [ -n "$VERSION" ] ; then
  MAKE_VARIABLES="$MAKE_VARIABLES VERSION=\"${VERSION}\""
  VERSION_TARGET=""
else
  VERSION_TARGET="version"
fi

processResult() {
  result=$1
  action=$2
  seconds=$(( $(date +%s) - $3 ))
  [ $result = 0 ] && resultString="SUCCESS" || resultString="ERROR"
  let results=results+result
  make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES clean-chroot-files
  str="**** %-7s %-40s in %3ds: make in %-40s exited with return code $result"
  printf "$str" "(${resultString})" "$action" "$seconds" "$directory"
  echo
  echo "# ======================="
  popd > /dev/null
}

### a few variables
FILE_IN="build-order.txt"
PKGTOOLS_HOME=`dirname $(readlink -f $0)`
results=0

### main
# cd into the main trunk (the buildbot is already in there)
cd "${BUILD_DIR}" 2> /dev/null

# patch, if necessary
[ -f Makefile ] && grep -qE '^patch:' Makefile && echo "Patching sources" && make -f Makefile patch

# grab the content of the build-order.txt file
build_dirs=()
while read package repositories ; do
  case $package in
    \#*) continue ;; # comment
    "") continue ;; # empty line
    *) # yes
      if [[ "$repositories" = *${TARGET_REP}* ]] ; then
	case $ARCH in
          i386) pattern="(any|all|$ARCH)" ;;
          *) pattern="(any|$ARCH)" ;;
        esac
        if [ "$DEFAULT_TARGETS" = "kernel-module-chroot" ] || grep -qE "^Architecture:.*$pattern" $package/debian/control ; then
	  build_dirs[${#build_dirs[*]}]="$package"
	fi
      fi ;;
  esac
done < $FILE_IN

# # do this only once, instead of for each package
# [ -n "$CHECKROOT_UPGRADE" ] && make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES upgrade-base-chroot

# now cd into each dir in build_dirs and make
for directory in "${build_dirs[@]}" ; do
  echo 
  echo "# $directory"
  # cd into it, and attempt to build
  pushd "$directory" > /dev/null
  seconds=$(date +%s)
  output=$(make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES clean-chroot-files $VERSION_TARGET $CHECK_EXISTENCE)
  if [ -n "$CHECK_EXISTENCE" ] ; then
    matches=$(echo "$output" | grep "is available in")
    if [ -n "$matches" ] ; then
      if echo "$matches" | grep -q $DISTRIBUTION ; then
        processResult 0 "already present in $DISTRIBUTION" $seconds && continue
      else
        distributionFrom=$(echo $matches | awk '{print $NF}')
        make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES DISTRIBUTION_FROM=$distributionFrom copy-src
        processResult $? "copied from $distributionFrom" $seconds && continue
      fi
    fi
  fi
  make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES $DEFAULT_TARGETS $RELEASE
  result=$?
  processResult $result "actual build" $seconds
  # if we're building only arch-dependent pkgs, we need to give the IQD time to process uploads
  [ $ARCH = "i386" ] || sleep 31
done

# do this last
make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES remove-existence-chroot remove-chroot

exit $results
