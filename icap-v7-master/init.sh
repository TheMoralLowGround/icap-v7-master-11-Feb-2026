#!/bin/bash

# stop executing the script on error
set -e

PROJECT_ROOT_PATH=$(pwd)

echo ""
echo "-----------------------------------------"
echo "Settingup media folders"
echo "-----------------------------------------"
echo ""

mkdir -p "${PROJECT_ROOT_PATH}/backend/media"
chmod 777 "${PROJECT_ROOT_PATH}/backend/media"

mkdir -p "${PROJECT_ROOT_PATH}/rules-backend/media"
chmod 777 "${PROJECT_ROOT_PATH}/rules-backend/media"

echo ""
echo "-----------------------------------------"
echo "Initialization completed successfully"
echo "-----------------------------------------"
echo ""