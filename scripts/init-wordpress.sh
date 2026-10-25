#!/bin/sh
set -eu
if ! wp core is-installed; then
  wp core install --url="$SITE_URL" --title="PHUC STUDIO" --admin_user="$WP_ADMIN_USER" --admin_password="$WP_ADMIN_PASSWORD" --admin_email="${WP_ADMIN_USER}@example.test" --skip-email
fi
wp eval-file /opt/seed.php
