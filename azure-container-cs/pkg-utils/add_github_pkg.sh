#!/bin/sh

# This script is used to set things up to install .NET components which are distributed via Github Packages. 

if [ $# -ne 2 ]
then
  echo "Usage: $0 SOURCE_NAME ENVIRONMENT_NAME"
  echo "Where SOURCE_NAME is the github package name (e.g. Pequod.Stackmgmt)"
  echo "Where ENVIRONMENT_NAME is the ESC environment that projects \$GITHUB_USERNAME and \$GITHUB_TOKEN for accessing the Github package."
  exit 255
fi

# Name of the package source
source_name=${1}
env_name=${2}

# Set up env vars with the creds
eval "$(pulumi env open ${env_name} -f shell)"

# See if the source is already configured
dotnet nuget list source | grep $source_name -q
if [ $? -ne 0 ]
then
  dotnet nuget add source --username $GITHUB_USERNAME --password $GITHUB_TOKEN --store-password-in-clear-text --name $source_name https://nuget.pkg.github.com/pulumi-pequod/index.json
else
  echo "$source_name is already added as a source"
fi