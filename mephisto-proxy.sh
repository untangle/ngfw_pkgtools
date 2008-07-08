#! /bin/bash -x

# FIMXE: does it get any nastier than this ??
# make that a CGI on mephisto, for fucksake...

REMOTE_USER="mephisto"
SSH_OPTIONS="-v -o StrictHostKeyChecking=no"
TMP_DIR=/tmp/mephisto-proxy_$$

ssh $SSH_OPTIONS $REMOTE_USER "rm -fr $TMP_DIR ; mkdir $TMP_DIR"
scp $SSH_OPTIONS -q *sh $REMOTE_USER:$TMP_DIR
ssh $SSH_OPTIONS $REMOTE_USER "cd $TMP_DIR ; $@"
ssh $SSH_OPTIONS $REMOTE_USER rm -fr $TMP_DIR
