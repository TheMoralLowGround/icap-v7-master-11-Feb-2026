#!/bin/bash

# stop executing the script on error
set -e

PROJECT_ROOT_PATH=$(pwd)

echo ""
echo "-----------------------------------------"
echo "Running git pull"
echo "-----------------------------------------"
echo ""
git pull

echo ""
echo "-----------------------------------------"
echo "Deploying Backend"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/backend
docker compose stop daphne nginx worker extraction-service-consumer
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Input-Channel"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/input-channel
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Classifier"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/classifier
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Postprocess"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/postprocess
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying OCR-Engine"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/ocr-engine
../docker-compose-build.sh
docker compose up -d


echo ""
echo "-----------------------------------------"
echo "Deploying Docbuilder"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/docbuilder
../docker-compose-build.sh
docker compose up -d


echo ""
echo "-----------------------------------------"
echo "Deploying Utility"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/utility
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying AI-Agent"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/ai-agent
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Auto-Extraction"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/auto-extraction
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Preprocess"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/preprocess
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Frontend"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/frontend
../docker-compose-build.sh
docker compose up -d

echo ""
echo "-----------------------------------------"
echo "Deploying Utility Engine"
echo "-----------------------------------------"
echo ""
cd ${PROJECT_ROOT_PATH}/utility-engine
../docker-compose-build.sh
docker compose up -d


echo ""
echo "-----------------------------------------"
echo "Deployment completed successfully"
echo "-----------------------------------------"
echo ""

# Fixing permissions for a few backend services
../fix_permissions.sh
