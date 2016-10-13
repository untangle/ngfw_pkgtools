#!/bin/bash

#set -x

CHROOT_BASE=

usage() {
  echo "$0 -r <repository> -d <distribution> -b <builddir> [-n] [-a <arch>] [-v <version>] [-u] [-e] [-c] [-m] [-k]"
  exit 1
}

DEFAULT_TARGETS="source pkg-chroot"

### CLI args
while getopts r:b:d:v:a:uencmhk option ; do
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
    k) DEFAULT_TARGETS="clean patch kpkg-arch" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
[[ -z "$ARCH" ]] && ARCH=i386

if [[ $ARCH == i386 ]] && [[ $DEFAULT_TARGETS == *kpkg-arch* ]] ; then
  # also build source, doc, etc
  DEFAULT_TARGETS="$DEFAULT_TARGETS kpkg-indep"
fi
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
  [[ "$DEFAULT_TARGETS" != *kpkg-arch* ]] && make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES clean-chroot-files
  str="**** %-7s %-40s in %3ds: make in %-40s exited with return code $result"
  printf "$str" "${resultString}" "($action)" "$seconds" "$directory"
  echo
  echo "# ======================="
  popd > /dev/null
}

### a few variables
export PATH=/sbin:/usr/sbin:${PATH}
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
while read package repositories architectures ; do
  case $package in
    \#*) continue ;; # comment
    \$*) #command
      # for a command, there's no delimited fields, so use the whole line
      [[ "${package} ${repositories} ${architectures}" != *${TARGET_REP}* ]] && continue
      build_dirs[${#build_dirs[*]}]="$package ${repositories//,/ }"
      ;;
    "") continue ;; # empty line
    *) # valid line
      # do we build this package for this arch ?
      [[ -n "$architectures" ]] && [[ "$architectures" != *${ARCH}* ]] && continue
      # do we build this package for this repository ?
      [[ "$repositories" != *${TARGET_REP}* ]] && continue
      case $ARCH in
        i386) pattern="(any|all|$ARCH)" ;;
        *) pattern="(any|$ARCH)" ;;
      esac
      if [[ "$DEFAULT_TARGETS" = "kernel-module-chroot" ]] || [[ "$DEFAULT_TARGETS" == *kpkg-arch* ]] || grep -qE "^Architecture:.*$pattern" $package/debian/control ; then
	build_dirs[${#build_dirs[*]}]="$package"
      fi ;;
  esac
done < $FILE_IN

# now cd into each dir in build_dirs and make
for directory in "${build_dirs[@]}" ; do
  echo 
  case $directory in
    \$*) # command
      echo "Running $directory"
      eval "${directory/\$}"
      continue
      ;;
  esac
  echo "# $directory"
  # cd into it, and attempt to build
  pushd "$directory" > /dev/null
  # clean up a bit
  find . -type f -name core -exec rm {} \;
  # bring resources/ from pkgtools into the source directory we cd'ed in
  cp -r $PKGTOOLS_HOME/resources ./
  seconds=$(date +%s)
  make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES clean-build || true # try anyway
  if [[ "$DEFAULT_TARGETS" != *kpkg-arch* ]] ; then
    output=$(make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES clean-chroot-files $VERSION_TARGET $CHECK_EXISTENCE)
    version=$(cat debian/version)
    if [ -n "$CHECK_EXISTENCE" ] ; then
      matches=$(echo "$output" | grep "is available in")
      if [ -n "$matches" ] ; then
        if echo "$matches" | grep -q $DISTRIBUTION ; then
          processResult 0 "$version already present in $DISTRIBUTION" $seconds && continue
        else
          distributionFrom=$(echo $matches | awk '{print $NF}')
          make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES DISTRIBUTION_FROM=$distributionFrom copy-src
          processResult $? "$version copied from $distributionFrom" $seconds && continue
        fi
      fi
    fi
    make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES $DEFAULT_TARGETS $RELEASE
  else
    make -f ./Makefile $MAKE_VARIABLES $DEFAULT_TARGETS $RELEASE
  fi
  rm -fr ./resources
  result=$?
  processResult $result "$version actual build" $seconds
  # # if we're building only arch-dependent pkgs, we need to give the IQD time to process uploads
  # [ $ARCH = "i386" ] || sleep 31
done

# do this last
make -f $PKGTOOLS_HOME/Makefile $MAKE_VARIABLES remove-existence-chroot remove-chroot

exit $results
