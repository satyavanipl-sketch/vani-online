<?php
defined('ABSPATH') || exit;

define('VANI_ANALYTICS_DB_VERSION', '1.0.0');

function vani_setup_analytics_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_analytics_events';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE $table_name (
        id bigint(20) NOT NULL AUTO_INCREMENT,
        event varchar(50) NOT NULL,
        post_id bigint(20) DEFAULT 0 NOT NULL,
        session_id varchar(50) DEFAULT '' NOT NULL,
        timestamp datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
        PRIMARY KEY  (id),
        KEY event (event),
        KEY post_id (post_id)
    ) $charset_collate;";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta($sql);

    add_option('vani_analytics_db_version', VANI_ANALYTICS_DB_VERSION);
}

// Log an analytics event (completely anonymous, no IPs, no PII)
function vani_log_analytics_event($event, $post_id = 0) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_analytics_events';
    
    // Generate simple session identifier based on cookie or generate a temporary one
    if (isset($_COOKIE['vani_session_id'])) {
        $session_id = sanitize_text_field($_COOKIE['vani_session_id']);
    } else {
        $session_id = md5(uniqid(rand(), true));
        setcookie('vani_session_id', $session_id, time() + 3600 * 24, COOKIEPATH, COOKIE_DOMAIN);
    }
    
    $wpdb->insert(
        $table_name,
        array(
            'event' => sanitize_text_field($event),
            'post_id' => intval($post_id),
            'session_id' => $session_id,
            'timestamp' => current_time('mysql')
        ),
        array('%s', '%d', '%s', '%s')
    );
}

// AJAX Handler for logging frontend events
add_action('wp_ajax_nopriv_vani_log_event', 'vani_ajax_log_event');
add_action('wp_ajax_vani_log_event', 'vani_ajax_log_event');

function vani_ajax_log_event() {
    check_ajax_referer('vani_core_nonce', 'nonce');
    
    $event = isset($_POST['event']) ? sanitize_text_field($_POST['event']) : '';
    $post_id = isset($_POST['post_id']) ? intval($_POST['post_id']) : 0;
    
    $valid_events = array(
        'story_view', 'story_complete', 'audio_play', 'audio_complete',
        'related_story_click', 'web_story_click', 'lead_magnet_view',
        'lead_magnet_signup', 'pdf_download'
    );
    
    if (in_array($event, $valid_events)) {
        vani_log_analytics_event($event, $post_id);
        wp_send_json_success(array('message' => 'Logged successfully'));
    } else {
        wp_send_json_error(array('message' => 'Invalid event'));
    }
}
