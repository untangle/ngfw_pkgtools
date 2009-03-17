# constants

[ -z "$REPOSITORY" ] && echo "REPOSITORY has to be set" && exit 1

PKGTOOLS=`dirname $0`

MUTT_CONF_FILE=$PKGTOOLS/mutt.conf
RECIPIENT="engineering@untangle.com"

REMOTE_USER="root"
REMOTE_SERVER="updates.untangle.com"
REMOTE_PKGTOOLS=$(mktemp -d /tmp/pkgtools.XXXXXXXXXXXXXXX)
REPREPRO_BASE_DIR="/var/www/public/$REPOSITORY"
REPREPRO_DIST_DIR="${REPREPRO_BASE_DIR}/dists"
REPREPRO_CONF_DIR="${REPREPRO_BASE_DIR}/conf"
REPREPRO_DISTRIBUTIONS_FILE="${REPREPRO_CONF_DIR}/distributions"
REPREPRO_COMMAND="./reprepro-untangle.sh -V -b ${REPREPRO_BASE_DIR} ${EXTRA_ARGS}"

# functions
repreproLocal() {
  $PKGTOOLS/${REPREPRO_COMMAND} "$@"
}

remoteCommand() {
  ssh -t ${REMOTE_USER}@${REMOTE_SERVER} cd ${REMOTE_PKGTOOLS} && "$@"
}

repreproRemote() {
  remoteCommand ${REPREPRO_COMMAND} "$@"
}

removeRemotePkgtools() {
  remoteCommand rm -fr ${REMOTE_PKGTOOLS}
}

copyRemotePkgtools() {
  removeRemotePkgtools
  scp -r $PKGTOOLS ${REMOTE_USER}@${REMOTE_SERVER}:${REMOTE_PKGTOOLS}
}

backup_conf() {
  tar czvf /var/www/public/$1/conf.`date -Iseconds`.tar.gz /var/www/public/$1/conf
}

push_new_releases_names() {
  # copy files
  scp $REPREPRO_DISTRIBUTIONS_FILE ${REPREPRO_CONF_DIR}/updates ${REMOTE_USER}@${REMOTE_SERVER}:${REPREPRO_CONF_DIR}/
  # create symlinks
  $REPREPRO_REMOTE_COMMAND --delete createsymlinks
}
