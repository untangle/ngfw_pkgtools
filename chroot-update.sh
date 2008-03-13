#! /bin/bash

# Use the current distro to pull main, but use upstream from stage/testing+$1/testing+$1/alpha
# (not everyone has upstream in his target distro)
# --Seb

SOURCES=/etc/apt/sources.list

# for our own build-deps
echo deb http://mephisto/public/$1 $2 main premium upstream >> ${SOURCES}
case "$HOME" in
  *buildbot*) echo deb http://mephisto/public/$1 $2 internal >> ${SOURCES}
esac

# also search in nightly
if [ $2 != nightly ] ; then
  echo deb http://mephisto/public/$1 nightly main premium upstream >> ${SOURCES}
  case "$USER" in
    *buildbot*) echo deb http://mephisto/public/$1 nightly internal >> ${SOURCES}
  esac
fi
#echo deb http://mephisto/public/sarge testing upstream >> ${SOURCES}
#echo deb http://mephisto/public/sarge alpha upstream >> ${SOURCES}

apt-get -q update

#umount -f /proc 2> /dev/null

exit 0
