FROM wordpress:php8.3-apache
# Sources are also bind-mounted read-only so existing wp_data receives updates.
COPY app/theme /usr/src/wordpress/wp-content/themes/phuc-catalog
COPY app/audit.php /usr/src/wordpress/wp-content/mu-plugins/project-audit.php
