#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose run --rm --no-deps --entrypoint sh cli -c 'wp core is-installed || wp core install --url="$SITE_URL" --title="PHUC STUDIO" --admin_user="$WP_ADMIN_USER" --admin_password="$WP_ADMIN_PASSWORD" --admin_email="phuc@example.test" --skip-email; wp eval-file /opt/seed.php'
