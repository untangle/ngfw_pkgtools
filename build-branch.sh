#!/bin/dash

BRANCH_PATH=$1
DESCRIPTION="$2"

if [ -z "${DESCRIPTION}" ] || [ -z "${BRANCH_PATH}" ]; then
    echo "Usage: $0 <svn path> <branch description>"
    exit 1
fi

svn list "${BRANCH_PATH}" > /dev/null 2>&1 && {
    echo "The path ${BRANCH_PATH} already exists, cowardly refusing to replace the branch."
    exit 2
}

update_external()
{
    local t_directory=$1
    cat > "${SVN_EXTERNALS}"

    echo "[svn propset] svn:externals ${BRANCH_PATH}/${t_directory}"
    svn propset svn:externals -F "${SVN_EXTERNALS}" ${TEMP_DIST}/${t_directory}
    echo "Updating svn:externals on ${BRANCH_PATH}/${t_directory}" >> ${CHANGE_LOG}
}

CHANGE_LOG=`mktemp`

echo "${DESCRIPTION}" >> ${CHANGE_LOG}

## Copy in all of the components that make up a release
echo "[svn mkdir] ${BRANCH_PATH}"
svn mkdir -m "${DESCRIPTION}" ${BRANCH_PATH}

## Create a temporary directory to check this out to.
TEMP_DIST=`mktemp -d`
rm -rf "${TEMP_DIST}"
svn checkout ${BRANCH_PATH} ${TEMP_DIST}

echo "[svn copy] svn://chef/work ${BRANCH_PATH}"
svn copy svn://chef/work ${TEMP_DIST}
echo "Copying work to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] svn://chef/hades ${BRANCH_PATH}"
svn copy svn://chef/hades ${TEMP_DIST}
echo "Copying hades to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] svn://chef/internal/pkgtools ${BRANCH_PATH}"
svn copy svn://chef/internal/pkgtools ${TEMP_DIST}
echo "Copying pkgtools to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] svn://chef/internal/isotools ${BRANCH_PATH}"
svn copy svn://chef/internal/isotools ${TEMP_DIST}
echo "Copying isotools to ${BRANCH_PATH}" >> ${CHANGE_LOG}

for t in `svn list 'svn://chef/internal' | awk '/^upstream_/ { print $1 }'` ; do 
    echo "[svn copy] svn://chef/internal/${t} ${BRANCH_PATH}"
    svn copy svn://chef/internal/${t} ${TEMP_DIST}
    echo "Copying svn://chef/internal/${t} to ${BRANCH_PATH}" >> ${CHANGE_LOG}
done

# Update all of the externals, this will no longer be necessary when we move to subversion 1.5
SVN_EXTERNALS=`mktemp`

cat <<EOF | update_external work/src
version         ${BRANCH_PATH}/work/version
EOF

cat <<EOF | update_external hades
resources       ${BRANCH_PATH}/work/version/resources
EOF

cat <<EOF | update_external hades/rup
resources       ${BRANCH_PATH}/work/version/resources
buildtools      ${BRANCH_PATH}/work/src/buildtools
EOF

cat <<EOF | update_external pkgtools
resources       ${BRANCH_PATH}/work/version/resources
EOF

svn commit -F "${CHANGE_LOG}" ${TEMP_DIST}

rm -f "${SVN_EXTERNALS}"
rm -f "${CHANGE_LOG}"
rm -rf "${TEMP_DIST}"
