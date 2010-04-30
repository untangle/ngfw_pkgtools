#! /bin/sh

set -e

SVN_SERVER="chef"
SVN_BASE_DIR="work"

GIT_DEFAULT_BRANCH="origin/master"
GIT_REMOTE_TRUNK=".git/refs/remotes/trunk"

# main
module=$(git config --get remote.origin.url | perl -pe 's|.*/(.+)\.git|$1|')

if [ "$module" = "work" ] || [ "$module" = "pkgs" ] ; then
  dir=${SVN_BASE_DIR}/$module
else
  dir=$module
fi

git svn init -T $dir \
             -b branch/prod/*/$dir \
             -t tags/*/$dir \
             svn://$SVN_SERVER

git show $GIT_BRANCH | awk '{print $2 ; exit}' >| $GIT_REMOTE_TRUNK

git svn fetch -r HEAD
