# constants

[ -z "$REPOSITORY" ] && echo "REPOSITORY has to be set" && exit 1

PKGTOOLS=$(dirname $0)
PKGTOOLS_VERSION=$(git rev-parse --short HEAD)

if [ $(hostname) != "pkgs" ] ; then
  REMOTE_PKGTOOLS=$(mktemp -d /tmp/pkgtools.XXXXXXXXXXXXXXX)
fi
REPREPRO_BASE_DIR="/mnt/www/public/$REPOSITORY"
REPREPRO_DIST_DIR="${REPREPRO_BASE_DIR}/dists"
REPREPRO_CONF_DIR="${REPREPRO_BASE_DIR}/conf"
REPREPRO_DISTRIBUTIONS_FILE="${REPREPRO_CONF_DIR}/distributions"
REPREPRO_COMMAND="./reprepro-untangle.sh -b ${REPREPRO_BASE_DIR} ${EXTRA_ARGS}"

# functions
repreproLocal() {
  echo "Running local command '$@'"
  $PKGTOOLS/${REPREPRO_COMMAND} "$@"
}