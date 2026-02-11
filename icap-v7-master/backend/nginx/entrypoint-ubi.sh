#!/bin/bash
set -e

envsubst '${WEB_HOST} ${DAPHNE_HOST} ${PROXY_TIMEOUT}' < /opt/app-root/etc/nginx.d/app.conf.template > /opt/app-root/etc/nginx.d/app.conf

exec "$@"