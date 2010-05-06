#!/bin/dash

read_user_input()
{
    local t_validator
    local t_prompt
    local t_variable
    local t_value

    t_prompt=$1
    t_variable=$2
    t_validator=$3

    
    while test -z "${t_value}" ; do
        read -p "${t_prompt}" t_value
        if [ -n "${t_validator}" ] ; then
            echo "${t_value}" | grep -q "${t_validator}" && break

            echo "The value: '${t_value}' is invalid"
            t_value=""            
            continue
        fi
        
        test -n "${t_value}" && break
    done
    
    eval "${t_variable}='${t_value}'"
}

get_new_version_string()
{
    local t_input
    local t_version_name
    local t_version_number

    read_user_input "Do you want to update the version string in the mainline[y/N]: " t_input "^[yYnN]\?$"
    if [ "${t_input}" != "y" ] && [ "${t_input}" != "Y" ] ; then
        return
    fi

    read_user_input "New version name (eg, corvette): " t_version_name "^[a-zA-Z]\+$"

    echo "Since minor revisions are done off of branches, only the major release number should be specified."
    read_user_input "New version number (eg, 6.0): " t_version_number "[0-9]\.[0-9]"
    
    NEW_VERSION_NAME=${t_version_name}
    NEW_VERSION_NUMBER=${t_version_number}
}

update_external()
{
    local t_directory=$1
    cat >| "${SVN_EXTERNALS}"

    echo "[svn propset] svn:externals ${BRANCH_PATH}/${t_directory}"
    svn propset svn:externals -F "${SVN_EXTERNALS}" ${TEMP_DIST}/${t_directory}
    echo "Updating svn:externals on ${BRANCH_PATH}/${t_directory}" >> ${CHANGE_LOG}
}

##### start of script.

BRANCH_PATH=$1
DESCRIPTION="$2"
BRANCH_REVISION="${3:+-r $3}"

NEW_VERSION_NAME=""
NEW_VERSION_NUMBER=""

if [ -z "${DESCRIPTION}" ] || [ -z "${BRANCH_PATH}" ]; then
    echo "Usage: $0 <svn path> <branch description> [<branch revision>]"
    exit 1
fi

svn list "${BRANCH_PATH}" > /dev/null 2>&1 && {
    echo "The path ${BRANCH_PATH} already exists, cowardly refusing to replace the branch."
    exit 2
}

get_new_version_string

CHANGE_LOG=`mktemp`

echo "${DESCRIPTION}" >> ${CHANGE_LOG}

## Copy in all of the components that make up a release
echo "[svn mkdir] ${BRANCH_PATH}"
svn mkdir -m "${DESCRIPTION}" ${BRANCH_PATH}

## Create a temporary directory to check this out to.
TEMP_DIST=`mktemp -d`
rm -rf "${TEMP_DIST}"
svn checkout ${BRANCH_PATH} ${TEMP_DIST}

echo "[svn copy] ${BRANCH_REVISION} svn://chef/work ${BRANCH_PATH}"
svn copy ${BRANCH_REVISION} svn://chef/work ${TEMP_DIST}
echo "Copying work to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] ${BRANCH_REVISION} svn://chef/hades ${BRANCH_PATH}"
svn copy ${BRANCH_REVISION} svn://chef/hades ${TEMP_DIST}
echo "Copying hades to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] ${BRANCH_REVISION} svn://chef/internal/pkgtools ${BRANCH_PATH}"
svn copy ${BRANCH_REVISION} svn://chef/internal/pkgtools ${TEMP_DIST}
echo "Copying pkgtools to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] ${BRANCH_REVISION} svn://chef/internal/isotools ${BRANCH_PATH}"
svn copy ${BRANCH_REVISION} svn://chef/internal/isotools ${TEMP_DIST}
echo "Copying isotools to ${BRANCH_PATH}" >> ${CHANGE_LOG}

echo "[svn copy] ${BRANCH_REVISION} svn://chef/upstream/pkgs ${BRANCH_PATH}"
svn copy ${BRANCH_REVISION} svn://chef/upstream/pkgs ${TEMP_DIST}
echo "Copying svn://chef/upstream/pkgs to ${BRANCH_PATH}" >> ${CHANGE_LOG}
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

cat <<EOF | update_external isotools
resources       ${BRANCH_PATH}/work/version/resources
EOF

cat <<EOF | update_external work/pkgs/untangle-net-alpaca/files/var/lib/rails/untangle-net-alpaca
version       ${BRANCH_PATH}/work/version/resources
EOF

svn commit -F "${CHANGE_LOG}" ${TEMP_DIST}

rm -f "${SVN_EXTERNALS}"
rm -f "${CHANGE_LOG}"
rm -rf "${TEMP_DIST}"

if [ -n "${NEW_VERSION_NUMBER}" ] &&  [ -n "${NEW_VERSION_NAME}" ] ; then
    echo "Updating the version number in the mainline"
    svn checkout svn://chef/work/version/resources ${TEMP_DIST}
    
    echo "${NEW_VERSION_NUMBER}.0" >| "${TEMP_DIST}/VERSION"
    echo "${NEW_VERSION_NUMBER}" >| "${TEMP_DIST}/PUBVERSION"
    echo "${NEW_VERSION_NAME}" >| "${TEMP_DIST}/RELEASE_CODENAME"
    
    ## Need this sleep, otherwise SVN doesn't detect the files changed.
    ## this was tested svn 1.4.2 several times without success.
    sleep 1

    touch "${TEMP_DIST}"/*
    
    svn commit -m "Updating the version string to ${NEW_VERSION_NUMBER}" "${TEMP_DIST}"
    rm -rf ${TEMP_DIST}
fi
