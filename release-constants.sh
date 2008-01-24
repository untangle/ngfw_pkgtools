# CONSTANTS

[ -z "$REPOSITORY" ] && echo "REPOSITORY has to be set" && exit 1

REMOTE_USER="root"
REMOTE_SERVER="updates.untangle.com"
REPREPRO_BASE_DIR="/var/www/public/$REPOSITORY"
REPREPRO_CONF_DIR="${REPREPRO_BASE_DIR}/conf"
REPREPRO_DISTRIBUTIONS_FILE="${REPREPRO_CONF_DIR}/distributions"
REPREPRO_BASE_COMMAND="sudo `dirname $0`/reprepro-untangle.sh -V -b ${REPREPRO_BASE_DIR} ${COMPONENT} ${TYPE}"
SSH_COMMAND="ssh ${REMOTE_USER}@${REMOTE_SERVER} cd /localhome/pkgtools &&"
REPREPRO_REMOTE_COMMAND="${SSH_COMMAND} ${REPREPRO_BASE_COMMAND}"

# FUNCTIONS
backup_conf() {
  tar czvf /var/www/untangle/conf.`date -Iseconds`.tar.gz /var/www/untangle/conf
}

push_new_releases_names() {
  # copy files
  scp $REPREPRO_DISTRIBUTIONS_FILE ${REPREPRO_CONF_DIR}/updates ${REMOTE_USER}@${REMOTE_SERVER}:${REPREPRO_CONF_DIR}/
  # create symlinks
  $REPREPRO_REMOTE_COMMAND --delete createsymlinks
}
