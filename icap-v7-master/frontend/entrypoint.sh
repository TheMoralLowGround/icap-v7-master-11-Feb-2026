#!/bin/bash
set -e

from_string='// CONFIGURATIONS_PLACEHOLDER'
to_string='window.configs = {
  "VUE_APP_BACKEND_URL":"'"${VUE_APP_BACKEND_URL}"'",
  "VUE_APP_WEBSOCKET_URL":"'"${VUE_APP_WEBSOCKET_URL}"'",
  "VUE_APP_RULES_BACKEND_URL":"'"${VUE_APP_RULES_BACKEND_URL}"'",
  "VUE_APP_DISPLAY_V6_NAVIGATION":"'"${VUE_APP_DISPLAY_V6_NAVIGATION}"'",
  "VUE_APP_DISPLAY_DEVELOPER_SETTINGS":"'"${VUE_APP_DISPLAY_DEVELOPER_SETTINGS}"'",
  "VUE_APP_DEFAULT_DEFINITION_VERSION":"'"${VUE_APP_DEFAULT_DEFINITION_VERSION}"'",
}'
file=/usr/share/nginx/html/index.html

# Replace string in given file
perl -s -0777 -pi -e 's/\Q$from\E/$to/' -- -from="$from_string" -to="$to_string" $file

exec "$@"