<?php
defined('ABSPATH') || exit;

// Register Meta Keys
add_action('init', 'vani_register_web_story_meta');
function vani_register_web_story_meta() {
    register_post_meta('post', '_vani_web_story_id', array(
        'show_in_rest' => true,
        'single' => true,
        'type' => 'integer',
    ));
}

// Add Web Story Selector Metabox
add_action('add_meta_boxes', 'vani_add_web_story_metabox');
function vani_add_web_story_metabox() {
    add_meta_box(
        'vani_web_story_selector',
        'Vani Web Story Mapping',
        'vani_web_story_metabox_html',
        'post',
        'side',
        'default'
    );
}

function vani_web_story_metabox_html($post) {
    $selected_story_id = get_post_meta($post->ID, '_vani_web_story_id', true);
    
    // Check if the 'web-story' post type exists on the site
    $post_types = get_post_types();
    $web_story_post_type = isset($post_types['web-story']) ? 'web-story' : '';
    
    wp_nonce_field('vani_web_story_save', 'vani_web_story_nonce');
    
    if (empty($web_story_post_type)) {
        echo '<p style="color:red;"><strong>Warning:</strong> Google Web Stories plugin post type ("web-story") is not active.</p>';
        return;
    }
    
    $stories = get_posts(array(
        'post_type' => 'web-story',
        'posts_per_page' => -1,
        'post_status' => 'publish',
        'orderby' => 'title',
        'order' => 'ASC'
    ));
    
    ?>
    <p>
        <label for="vani_web_story_id"><strong>Select Web Story:</strong></label><br>
        <select id="vani_web_story_id" name="vani_web_story_id" style="width: 100%;">
            <option value="">-- None --</option>
            <?php foreach ($stories as $story): ?>
                <option value="<?php echo esc_attr($story->ID); ?>" <?php selected($selected_story_id, $story->ID); ?>>
                    <?php echo esc_html($story->post_title); ?>
                </option>
            <?php endforeach; ?>
        </select>
    </p>
    <?php
}

// Save Web Story Meta Box Selection
add_action('save_post', 'vani_save_web_story_meta');
function vani_save_web_story_meta($post_id) {
    if (!isset($_POST['vani_web_story_nonce']) || !wp_verify_nonce($_POST['vani_web_story_nonce'], 'vani_web_story_save')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;
    
    if (isset($_POST['vani_web_story_id'])) {
        $story_id = intval($_POST['vani_web_story_id']);
        if ($story_id > 0) {
            update_post_meta($post_id, '_vani_web_story_id', $story_id);
        } else {
            delete_post_meta($post_id, '_vani_web_story_id');
        }
    }
}

// Automatic Reading Time Calculation
function vani_get_reading_time($content) {
    $clean_content = strip_tags(strip_shortcodes($content));
    // Fallback if content is short
    if (empty($clean_content)) return 1;
    
    $word_count = str_word_count($clean_content);
    $reading_time = ceil($word_count / 200);
    return max(1, $reading_time);
}

// Hook content display to show reading time and Web Story links
add_filter('the_content', 'vani_add_reading_meta_links');
function vani_add_reading_meta_links($content) {
    if (is_single() && get_post_type() === 'post' && in_the_loop() && is_main_query()) {
        $reading_time = vani_get_reading_time($content);
        $web_story_id = get_post_meta(get_the_ID(), '_vani_web_story_id', true);
        
        $meta_html = '<div class="vani-post-reading-meta" style="margin: 10px 0 20px 0; font-style: italic; color: #555;">';
        $meta_html .= '<span>📖 Reading time: ' . esc_html($reading_time) . ' minute(s)</span>';
        
        if ($web_story_id && get_post_status($web_story_id) === 'publish') {
            $web_story_url = get_permalink($web_story_id);
            $meta_html .= ' | <a href="' . esc_url($web_story_url) . '" class="vani-web-story-link" target="_blank" style="font-weight: bold; color: #e74c3c;">🎬 View Web Story</a>';
        }
        $meta_html .= '</div>';
        
        // Inject below title (at top of the content)
        $content = $meta_html . $content;
    }
    return $content;
}
