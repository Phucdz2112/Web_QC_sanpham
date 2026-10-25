<?php
/** Plugin Name: Project audit log */
function phuc_audit($event, $details = []) {
    $record = array_merge(['time'=>gmdate('c'), 'event'=>$event], $details);
    // Never log passwords, cookies, request bodies or tokens.
    error_log(wp_json_encode($record, JSON_UNESCAPED_UNICODE) . "\n", 3, '/var/log/project/audit.log');
}
add_action('wp_login', function($login, $user) { phuc_audit('login_success', ['user_id'=>$user->ID]); }, 10, 2);
add_action('wp_login_failed', function() { phuc_audit('login_failed'); });
add_action('save_post_product', function($id, $post, $update) {
    if (!wp_is_post_revision($id) && !wp_is_post_autosave($id)) phuc_audit('product_saved', ['post_id'=>$id, 'updated'=>$update]);
}, 10, 3);
add_action('before_delete_post', function($id, $post) {
    if ($post->post_type === 'product') phuc_audit('product_deleted', ['post_id'=>$id]);
}, 10, 2);
