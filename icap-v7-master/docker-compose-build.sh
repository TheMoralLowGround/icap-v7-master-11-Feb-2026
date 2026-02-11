docker compose build \
    --build-arg HTTP_PROXY=$HTTP_PROXY \
    --build-arg http_proxy=$HTTP_PROXY \
    --build-arg HTTPS_PROXY=$HTTPS_PROXY \
    --build-arg https_proxy=$HTTPS_PROXY \
    --build-arg NO_PROXY=$NO_PROXY \
    --build-arg no_proxy=$NO_PROXY