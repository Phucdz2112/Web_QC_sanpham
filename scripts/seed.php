<?php
// Idempotent: preserve existing users/content and create sample products only once.
$url = getenv('SITE_URL');
if (!is_blog_installed()) {
    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    wp_install('PHUC STUDIO', getenv('WP_ADMIN_USER'), 'phuc@example.test', true, '', getenv('WP_ADMIN_PASSWORD'));
}
$user = get_user_by('login', getenv('WP_ADMIN_USER'));
if (!$user) {
    $id = wp_create_user(getenv('WP_ADMIN_USER'), getenv('WP_ADMIN_PASSWORD'), 'phuc@example.test');
    if (is_wp_error($id)) { throw new Exception($id->get_error_message()); }
    (new WP_User($id))->set_role('administrator');
} else { wp_set_password(getenv('WP_ADMIN_PASSWORD'), $user->ID); }
update_option('home', $url);
update_option('siteurl', $url);
update_option('blogname', 'PHUC STUDIO');
update_option('blogdescription', 'Thiết bị cho góc làm việc sáng tạo');
switch_theme('phuc-catalog');
require_once get_theme_file_path('/functions.php');
phuc_register_products();
$products = [
 ['Bàn phím cơ Forma 75', 'keyboard', 1890000, 'Gõ êm, thiết kế gọn và kết nối không dây. Layout 75% giữ đủ phím chức năng cho công việc mỗi ngày.'],
 ['Tai nghe không dây Wave', 'headphones', 2490000, 'Âm thanh cân bằng, đệm tai mềm và thời lượng pin dài. Một khoảng tập trung cho riêng bạn.'],
 ['Đèn bàn Halo', 'lamp', 890000, 'Ánh sáng dịu, điều chỉnh độ sáng theo không gian và thời điểm làm việc.'],
 ['Loa để bàn Orbit', 'speaker', 1590000, 'Âm thanh đầy đặn trong một thiết kế tối giản. Dễ kết nối với laptop và điện thoại.'],
 ['Chuột không dây Arc', 'mouse', 690000, 'Thân chuột nhẹ, cảm biến chính xác và thao tác êm. Phù hợp cho góc làm việc gọn gàng.'],
 ['Đế laptop Elevate', 'stand', 790000, 'Nâng màn hình lên tầm mắt, tạo không gian thông thoáng bên dưới laptop.']
];
foreach ($products as [$title,$kind,$price,$description]) {
    $slug = sanitize_title($title);
    if (get_page_by_path($slug, OBJECT, 'product')) continue;
    $id = wp_insert_post(['post_type'=>'product','post_status'=>'publish','post_title'=>$title,'post_name'=>$slug,'post_content'=>$description], true);
    if (is_wp_error($id)) throw new Exception($id->get_error_message());
    update_post_meta($id,'price',$price);
    update_post_meta($id,'kind',$kind);
}
update_option('permalink_structure','/%postname%/');
flush_rewrite_rules();
echo "Website configured; existing content preserved.\n";
