# constants

[ -z "$REPOSITORY" ] && echo "REPOSITORY has to be set" && exit 1

PKGTOOLS=$(dirname $0)
VERSION=$(git rev-parse --short HEAD)

MUTT_CONF_FILE=$PKGTOOLS/mutt.conf
RECIPIENT="engineering@untangle.com"

REMOTE_USER="root"
REMOTE_SERVER="updates.untangle.com"
SSH_COMMAND="ssh -t ${REMOTE_USER}@${REMOTE_SERVER}"
if [ $(hostname) != "pkgs" ] ; then
  REMOTE_PKGTOOLS=$(mktemp -d /tmp/pkgtools.XXXXXXXXXXXXXXX)
fi
REPREPRO_BASE_DIR="/var/www/public/$REPOSITORY"
REPREPRO_DIST_DIR="${REPREPRO_BASE_DIR}/dists"
REPREPRO_CONF_DIR="${REPREPRO_BASE_DIR}/conf"
REPREPRO_DISTRIBUTIONS_FILE="${REPREPRO_CONF_DIR}/distributions"
REPREPRO_COMMAND="./reprepro-untangle.sh -V -b ${REPREPRO_BASE_DIR} ${EXTRA_ARGS}"

# functions
repreproLocal() {
  echo "Running local command '$@'"
  $PKGTOOLS/${REPREPRO_COMMAND} "$@"
}

remoteCommand() {
  echo "Running remote command: '$@'"
  case "$@" in
    *"${REMOTE_PKGTOOLS}"*)
      $SSH_COMMAND "$@" ;;
    *)
      $SSH_COMMAND "cd ${REMOTE_PKGTOOLS} && $@" ;;
  esac
}

repreproRemote() {
  remoteCommand ${REPREPRO_COMMAND} "$@"
}

copyRemotePkgtools() {
  removeRemotePkgtools
  rsync -aH $PKGTOOLS/ ${REMOTE_USER}@${REMOTE_SERVER}:${REMOTE_PKGTOOLS}/
}

removeRemotePkgtools() {
  remoteCommand "rm -fr ${REMOTE_PKGTOOLS}"
}
