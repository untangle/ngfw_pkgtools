#! /bin/bash

usage() {
  echo "$0 -i <ami-id>"
  echo "Copy AMI <ami-id> to all regions listed in ./regions.txt"
  echo "Both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY need to be defined and exported"
  exit 1
}

#############
## Constants
#############
SRC_REGION="us-east-1"
DIR=$(dirname $0)
REGIONS_FILE="${DIR}/regions.txt"

#############
## CLI args
#############
while getopts i: option ; do
  case "$option" in
    i) AMI_ID="$OPTARG" ;;
    h|\?) usage ;;
  esac
done

##########
## main
##########

##################
# check CLI args
{ [[ -z "$AMI_ID" ]] || [[ -z "$AWS_ACCESS_KEY_ID" ]] || [[ -z "$AWS_SECRET_ACCESS_KEY" ]] ; } && usage

amiName=$(aws ec2 --region $SRC_REGION describe-images --image-id $AMI_ID | jq -r '.Images[].Name')

grep -vE '^#' $REGIONS_FILE | while read region ; do
  [[ -n "$region" ]] || continue
  aws ec2 copy-image --source-region $SRC_REGION --source-image-id $AMI_ID --name $amiName --region $region --dry-run
done
