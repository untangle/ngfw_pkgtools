#! /bin/bash

set -e

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
    local t_version_number

    read_user_input "Do you want to update the version string in the mainline[y/N]: " t_input "^[yYnN]\?$"
    if [ "${t_input}" != "y" ] && [ "${t_input}" != "Y" ] ; then
        return
    fi

    echo "Since minor revisions are done off of branches, only the major release number should be specified."
    read_user_input "New version number (eg, 6.0): " t_version_number "[0-9]\.[0-9]"
    
    NEW_VERSION_NUMBER=${t_version_number}
}

##### start of script

BRANCH_NAME=$1
NEW_VERSION_NUMBER=$2

GIT_BASE_URL="git@github.com:untangle/"

if [ -z "${BRANCH_NAME}" ]; then
  echo "Usage: $0 <branch_name> [<new_version_number>]"
  exit 1
fi

if [ -z "$NEW_VERSION_NUMBER" ] ; then
  get_new_version_string
fi

## Create a temporary directory to clone everything
TEMP_DIST="/localhome/for-branching"
rm -rf "${TEMP_DIST}"
mkdir -p "$TEMP_DIST"
pushd $TEMP_DIST

for component in src pkgs hades-pkgs pkgtools isotools-jessie isotools-stretch upstream ; do
  component="ngfw_$component"
  url="${GIT_BASE_URL}$component"
  git clone $url
  pushd $component
  git branch $BRANCH_NAME
  git push origin ${BRANCH_NAME}:$BRANCH_NAME
  popd
done

if [ -n "${NEW_VERSION_NUMBER}" ] ; then
  echo "Updating the version number in the mainline"
  pushd ngfw_pkgtools/resources
  git checkout master
  echo "${NEW_VERSION_NUMBER}.0" >| VERSION
  echo "${NEW_VERSION_NUMBER}" >| PUBVERSION
  git commit -a -m "Updating the version string to ${NEW_VERSION_NUMBER}"
  git push
  popd
fi

popd
rm -rf "${TEMP_DIST}"
