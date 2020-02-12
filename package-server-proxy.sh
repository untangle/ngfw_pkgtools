#! /bin/bash

# FIMXE: does it get any nastier than this ??
# make that a CGI on package-server, for fucksake...

PKGTOOLS_DIR=$(readlink -f $(dirname $0))
REMOTE_USER="buildbot"
REMOTE_HOST="package-server"
REMOTE=${REMOTE_USER}@$REMOTE_HOST
SSH_OPTIONS="-o StrictHostKeyChecking=no -i /tmp/travis-buildbot.rsa"
TMP_DIR=/tmp/package-server-proxy_$$

LOCAL_TARGET_SCRIPT=$1
shift
REMOTE_TARGET_SCRIPT="./$(basename $LOCAL_TARGET_SCRIPT)"

ssh $SSH_OPTIONS $REMOTE "rm -fr $TMP_DIR ; mkdir $TMP_DIR"
scp $SSH_OPTIONS -q $LOCAL_TARGET_SCRIPT $REMOTE:$TMP_DIR
ssh $SSH_OPTIONS $REMOTE "cd $TMP_DIR ; $REMOTE_TARGET_SCRIPT $@"
rc=$?
ssh $SSH_OPTIONS $REMOTE rm -fr $TMP_DIR

exit $rc
