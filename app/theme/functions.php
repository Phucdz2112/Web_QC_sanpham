<?php
add_action('after_setup_theme', function() { add_theme_support('title-tag'); });
add_filter('use_block_editor_for_post_type', function($use, $type) { return $type === 'product' ? false : $use; }, 10, 2);
function phuc_register_products() {
    register_post_type('product', [
      'labels'=>['name'=>'Sản phẩm','singular_name'=>'Sản phẩm','add_new_item'=>'Thêm sản phẩm','edit_item'=>'Sửa sản phẩm'],
      'public'=>true, 'has_archive'=>true, 'show_in_rest'=>true, 'menu_icon'=>'dashicons-products',
      'supports'=>['title','editor','thumbnail'], 'rewrite'=>['slug'=>'san-pham']
    ]);
    register_post_meta('product','price', ['type'=>'integer','single'=>true,'show_in_rest'=>true,
      'sanitize_callback'=>function($v) { return max(0, (int)$v); },
      'auth_callback'=>function() { return current_user_can('edit_posts'); }]);
    register_post_meta('product','kind', ['type'=>'string','single'=>true,'show_in_rest'=>true,
      'sanitize_callback'=>'sanitize_key', 'auth_callback'=>function() { return current_user_can('edit_posts'); }]);
}
add_action('init', 'phuc_register_products');
add_action('add_meta_boxes', function() {
    add_meta_box('phuc-details','Thông tin sản phẩm', function($post) {
        wp_nonce_field('phuc_product','phuc_nonce');
        echo '<p><label>Giá bán (VNĐ)<br><input type="number" min="0" step="1" name="phuc_price" value="'.esc_attr(get_post_meta($post->ID,'price',true)).'"></label></p>';
        echo '<p><label>Kiểu minh họa<br><select name="phuc_kind">';
        foreach (['keyboard','headphones','lamp','speaker','mouse','stand'] as $kind) {
            echo '<option value="'.esc_attr($kind).'" '.selected(get_post_meta($post->ID,'kind',true),$kind,false).'>'.esc_html($kind).'</option>';
        }
        echo '</select></label></p>';
    }, 'product');
});
add_action('save_post_product', function($id) {
    if (!isset($_POST['phuc_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['phuc_nonce'])),'phuc_product') || !current_user_can('edit_post',$id) || wp_is_post_autosave($id) || wp_is_post_revision($id)) return;
    if (isset($_POST['phuc_price'])) update_post_meta($id,'price',max(0,(int)$_POST['phuc_price']));
    if (isset($_POST['phuc_kind'])) update_post_meta($id,'kind',sanitize_key($_POST['phuc_kind']));
});
function phuc_price($id) { return number_format((int)get_post_meta($id,'price',true),0,',','.') . ' ₫'; }
function phuc_art($kind) {
    $allowed=['keyboard','headphones','lamp','speaker','mouse','stand'];
    return get_stylesheet_directory_uri().'/assets/'.(in_array($kind,$allowed,true)?$kind:'keyboard').'.svg';
}
