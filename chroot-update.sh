#! /bin/bash

# Use the current distro to pull main, but use upstream from stage/testing+$1/testing+$1/alpha
# (not everyone has upstream in his target distro)
# --Seb

SOURCES=/etc/apt/sources.list
DEBIAN_MIRROR=http://debian/debian
UBUNTU_MIRROR=http://ubuntu/ubuntu

if [ $# = 0 ] ; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -o DPkg::Options::=--force-confnew --yes --force-yes --fix-broken --purge debhelper aptitude
  DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -o DPkg::Options::=--force-confnew --yes --force-yes --fix-broken --purge
  exit 0
fi

addSource() {
  SRC="deb $1"
  grep -q "$SRC" ${SOURCES} || echo $SRC >> ${SOURCES}
}

REPOSITORY=$1
DISTRIBUTION=$2

case DISTRIBUTION in
  *-*) branch="`echo $DISTRIBUTION | perl -pe 's/.*?-/-/'`" ;;
  *) branch="" ;;
esac

# reset sources.list to start with: we don't want to use packages from
# the official repositories to get our build-dependencies, as this may
# impact us when there is a Debian point release
echo >| $SOURCES

# for our own build-deps
addSource "http://package-server/public/$REPOSITORY $DISTRIBUTION main main/debian-installer non-free citrix"

# also search in current-$branch if not buildbot
case $DISTRIBUTION in
  current*) ;;
  *)
    case "$HOME" in
      *buildbot*) ;;
      *) addSource "http://package-server/public/$REPOSITORY current${branch} main main/debian-installer non-free citrix"
    esac ;;
esac

# if grep -q debian $SOURCES ; then
#   grep -q "non-free" $SOURCES || perl -i -pe 's/main\s*$/main contrib non-free\n/' $SOURCES
# else
#   grep -q "universe" $SOURCES || perl -i -pe 's/main\s*$/main universe multiverse\n/' $SOURCES
# fi

cat >| /etc/apt/preferences <<EOF
Explanation: main lenny archive
Package: *
Pin: release a=stable, o=Debian, l=Debian
Pin-Priority: 101

Explanation: security archive
Package: *
Pin: release a=stable, o=Debian, l=Debian-security
Pin-Priority: 101

Explanation: 00default-untangle.conf
Package: *
Pin: release o=Untangle
Pin-Priority: 1001 
EOF

apt-get -q update

# do not ever prompt the user, even if the distribution name doesn't
# please dch
sed -i -e '/garbage/d' /usr/bin/dch

exit 0
