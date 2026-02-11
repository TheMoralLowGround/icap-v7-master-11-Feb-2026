#!/bin/bash
set -e

envsubst '${WEB_HOST}' < /opt/app-root/etc/nginx.d/app.conf.template > /opt/app-root/etc/nginx.d/app.conf

exec "$@"