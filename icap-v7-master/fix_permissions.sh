#!/bin/bash
# fix_permissions.sh

#!/bin/bash
# fix_permissions.sh

echo "==================================================================================================="
echo "Fixing Permissions for Web, Worker, Celery, extraction-service-consumer & ai-agent-service-consumer"
echo "==================================================================================================="

PROJECT_ROOT_PATH=$(pwd)

# Define services and their required directories
declare -A BACKEND_SERVICE_DIRS
BACKEND_SERVICE_DIRS["web"]="/batches:777 /training-dataset/selected-batches:777 /change_logs:777 /app/media:777 /app/models:777"
BACKEND_SERVICE_DIRS["worker"]="/batches:777 /training-dataset/selected-batches:777 /scripts:777 /input-files:777 /app/media:777 /app/models:777"
BACKEND_SERVICE_DIRS["celery"]="/batches:777 /training-dataset/selected-batches:777 /app/models:777"
BACKEND_SERVICE_DIRS["celery_beat"]="/app/models:777"
BACKEND_SERVICE_DIRS["extraction-service-consumer"]="/batches:777 /app/media:777 /app/models:777"
BACKEND_SERVICE_DIRS["extraction-service-ws-bridge"]="/app/models:777"
BACKEND_SERVICE_DIRS["ai-agent-service-consumer"]="/batches:777 /app/media:777 /app/models:777"
BACKEND_SERVICE_DIRS["ai-agent-service-ws-bridge"]="/app/models:777"
BACKEND_SERVICE_DIRS["nginx"]="/app/batches:777 /app/training-dataset/selected-batches:777 /app/media:777"
BACKEND_SERVICE_DIRS["qdrant"]="/qdrant/storage:777"

declare -A UTILITY_SERVICE_DIRS
UTILITY_SERVICE_DIRS["web"]="/scripts:777"
UTILITY_SERVICE_DIRS["worker"]="/scripts:777"

declare -A CLASSIFIER_SERVICE_DIRS
CLASSIFIER_SERVICE_DIRS["web"]="/batches:777 /scripts:777 /app/media:777"

declare -A INPUT_CHANNEL_SERVICE_DIRS
INPUT_CHANNEL_SERVICE_DIRS["web"]="/input-files:777 /app/media:777"
INPUT_CHANNEL_SERVICE_DIRS["worker"]="/input-files:777"
INPUT_CHANNEL_SERVICE_DIRS["celery"]="/input-files:777"

# Function to fix permissions for a service
fix_service_permissions() {
    local service=$1
    local dirs=$2
    
    echo "→ Fixing $service container permissions..."
    
    # Check if container is running
    if ! docker compose ps | grep -q "$service"; then
        echo "  ⚠️  Warning: $service container is not running, skipping..."
        return 0
    fi
    
    # Build chmod commands
    local chmod_commands=""
    for dir_perm in $dirs; do
        local dir=$(echo $dir_perm | cut -d':' -f1)
        local perm=$(echo $dir_perm | cut -d':' -f2)
        chmod_commands="$chmod_commands
            if [ -d '$dir' ]; then
                chmod -R $perm '$dir' 2>/dev/null && echo '  ✓ Set $perm on $dir' || echo '  ✗ Failed to set permissions on $dir'
            else
                echo '  ⚠️  Directory $dir does not exist'
            fi"
    done
    
    # Execute permissions fix
    docker compose exec -T -u root $service sh -c "$chmod_commands
        echo '✓ $service container permissions fixed'
    " || echo "  ✗ Failed to fix $service permissions"
}

echo "→ Fixing backend container permissions..."
# Fix permissions for all backend services
cd ${PROJECT_ROOT_PATH}/backend
for service in "${!BACKEND_SERVICE_DIRS[@]}"; do
    fix_service_permissions "$service" "${BACKEND_SERVICE_DIRS[$service]}"
done


echo "→ Fixing utility container permissions..."
# Fix permissions for all utility services
cd ${PROJECT_ROOT_PATH}/utility
for service in "${!UTILITY_SERVICE_DIRS[@]}"; do
    fix_service_permissions "$service" "${UTILITY_SERVICE_DIRS[$service]}"
done


echo "→ Fixing classifier container permissions..."
# Fix permissions for all classifier services
cd ${PROJECT_ROOT_PATH}/classifier
for service in "${!CLASSIFIER_SERVICE_DIRS[@]}"; do
    fix_service_permissions "$service" "${CLASSIFIER_SERVICE_DIRS[$service]}"
done


echo "→ Fixing classifier input-channel permissions..."
# Fix permissions for all input-channel services
cd ${PROJECT_ROOT_PATH}/input-channel
for service in "${!INPUT_CHANNEL_SERVICE_DIRS[@]}"; do
    fix_service_permissions "$service" "${INPUT_CHANNEL_SERVICE_DIRS[$service]}"
done

echo "==================================="
echo "✓ All permissions fixed successfully!"
echo "==================================="