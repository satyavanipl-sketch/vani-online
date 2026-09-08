<?php
defined('ABSPATH') || exit;

// Add Admin Menus
add_action('admin_menu', 'vani_core_add_admin_menu');
function vani_core_add_admin_menu() {
    add_menu_page(
        'VaniOnline Management',
        'VaniOnline',
        'manage_options',
        'vani-online-dashboard',
        'vani_admin_dashboard_html',
        'dashicons-book-alt',
        30
    );
    
    add_submenu_page(
        'vani-online-dashboard',
        'Audio Stories Catalog',
        'Audio Stories',
        'manage_options',
        'vani-audio-catalog',
        'vani_admin_audio_catalog_html'
    );
    
    add_submenu_page(
        'vani-online-dashboard',
        'Subscribers List',
        'Subscribers',
        'manage_options',
        'vani-subscribers',
        'vani_admin_subscribers_html'
    );
}

// Redirect top menu to Audio Catalog for clean layouts
function vani_admin_dashboard_html() {
    echo '<script>window.location.href="admin.php?page=vani-audio-catalog";</script>';
}

// 1. Audio Stories Catalog Screen
function vani_admin_audio_catalog_html() {
    if (!current_user_can('manage_options')) return;
    
    $args = array(
        'post_type' => 'post',
        'posts_per_page' => -1,
        'post_status' => 'publish,draft,future'
    );
    $posts = get_posts($args);
    ?>
    <div class="wrap">
        <h1>🎙️ VaniOnline Audio Stories Catalog</h1>
        <p>This screen displays all stories on the website, their audio configuration, and associated Google Web Stories.</p>
        
        <table class="wp-list-table widefat fixed striped table-view-list" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Story Title</th>
                    <th>Audio Status</th>
                    <th>Duration</th>
                    <th>Web Story Mapping</th>
                    <th>Published Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($posts)): ?>
                    <tr><td colspan="6">No stories found.</td></tr>
                <?php else: 
                    foreach ($posts as $p):
                        $audio_url = get_post_meta($p->ID, '_vani_audio_url', true);
                        $duration = get_post_meta($p->ID, '_vani_audio_duration', true);
                        $web_story_id = get_post_meta($p->ID, '_vani_web_story_id', true);
                        
                        $duration_str = '--';
                        if (!empty($duration)) {
                            $minutes = floor($duration / 60);
                            $seconds = $duration % 60;
                            $duration_str = sprintf('%d:%02d', $minutes, $seconds);
                        }
                        
                        $audio_status = !empty($audio_url) ? '<span style="color:green; font-weight:bold;">✓ Configured</span>' : '<span style="color:red;">✗ Missing</span>';
                        
                        $web_story_status = '--';
                        if (!empty($web_story_id)) {
                            $story_post = get_post($web_story_id);
                            if ($story_post && $story_post->post_status === 'publish') {
                                $web_story_status = '<span style="color:green; font-weight:bold;">✓ Mapped (' . esc_html($story_post->post_title) . ')</span>';
                            } else {
                                $web_story_status = '<span style="color:orange;">✗ Invalid Mapping</span>';
                            }
                        }
                        ?>
                        <tr>
                            <td><strong><a href="<?php echo get_edit_post_link($p->ID); ?>"><?php echo esc_html($p->post_title); ?></a></strong></td>
                            <td><?php echo $audio_status; ?></td>
                            <td><code><?php echo esc_html($duration_str); ?></code></td>
                            <td><?php echo $web_story_status; ?></td>
                            <td><?php echo esc_html(get_the_date('Y/m/d H:i', $p->ID)); ?></td>
                            <td><span class="badge" style="background:#ddd; padding:2px 8px; border-radius:4px; font-size:11px;"><?php echo esc_html(strtoupper($p->post_status)); ?></span></td>
                        </tr>
                    <?php endforeach;
                endif; ?>
            </tbody>
        </table>
    </div>
    <?php
}

// 2. Subscribers Manager Screen
function vani_admin_subscribers_html() {
    if (!current_user_can('manage_options')) return;
    
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    
    // Handle subscriber deletion
    if (isset($_GET['action']) && $_GET['action'] === 'delete' && isset($_GET['sub_id'])) {
        check_admin_referer('vani_delete_subscriber_nonce');
        $sub_id = intval($_GET['sub_id']);
        vani_delete_subscriber($sub_id);
        echo '<div class="notice notice-success is-dismissible"><p>Subscriber marked as deleted.</p></div>';
    }
    
    $subscribers = $wpdb->get_results("SELECT * FROM $table_name WHERE status != 'deleted' ORDER BY created_at DESC");
    $total_subs = $wpdb->get_var("SELECT COUNT(*) FROM $table_name WHERE status = 'active'");
    
    $export_url = add_query_arg(array(
        'vani_export_subscribers' => '1',
        'nonce' => wp_create_nonce('vani_export_subs_nonce')
    ), admin_url('admin-ajax.php'));
    ?>
    <div class="wrap">
        <h1>👥 VaniOnline Lead Magnet Subscribers</h1>
        <p>Manage list of active subscribers captured via the bedtime stories lead magnet funnel.</p>
        
        <div style="background:#fff; padding: 15px; border: 1px solid #ccd0d4; margin-top:20px; border-radius:4px; display:inline-block; min-width:300px;">
            <h3>Active Audience Stats</h3>
            <p style="font-size:24px; font-weight:bold; margin:10px 0; color:#2c3e50;"><?php echo intval($total_subs); ?> Subscribers</p>
            <p><a href="<?php echo esc_url($export_url); ?>" class="button button-primary">📤 Export Active Subscribers to CSV</a></p>
        </div>
        
        <table class="wp-list-table widefat fixed striped table-view-list" style="margin-top: 25px;">
            <thead>
                <tr>
                    <th>Email Address</th>
                    <th>Status</th>
                    <th>Consent Recorded</th>
                    <th>Signup Source</th>
                    <th>Signup Timestamp</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($subscribers)): ?>
                    <tr><td colspan="6">No subscribers found.</td></tr>
                <?php else:
                    foreach ($subscribers as $sub):
                        $delete_url = wp_nonce_url(
                            admin_url('admin.php?page=vani-subscribers&action=delete&sub_id=' . $sub->id),
                            'vani_delete_subscriber_nonce'
                        );
                        ?>
                        <tr>
                            <td><strong><?php echo esc_html($sub->email); ?></strong></td>
                            <td><code><?php echo esc_html($sub->status); ?></code></td>
                            <td><?php echo $sub->consent ? '<span style="color:green;font-weight:bold;">Yes</span>' : '<span style="color:red;">No</span>'; ?></td>
                            <td><?php echo esc_html($sub->source); ?></td>
                            <td><?php echo esc_html($sub->created_at); ?></td>
                            <td>
                                <a href="<?php echo esc_url($delete_url); ?>" class="submitdelete" style="color:red;" onclick="return confirm('Are you sure you want to mark this subscriber as deleted?');">Delete</a>
                            </td>
                        </tr>
                    <?php endforeach;
                endif; ?>
            </tbody>
        </table>
    </div>
    <?php
}

// 3. Subscribers CSV Export Handler
add_action('wp_ajax_vani_export_subscribers', 'vani_ajax_export_subscribers');
function vani_ajax_export_subscribers() {
    if (!current_user_can('manage_options')) {
        wp_die('Permission denied.');
    }
    
    if (!isset($_GET['nonce']) || !wp_verify_nonce($_GET['nonce'], 'vani_export_subs_nonce')) {
        wp_die('Security check failed.');
    }
    
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    $subscribers = $wpdb->get_results("SELECT email, status, consent, consent_timestamp, source, created_at FROM $table_name WHERE status = 'active' ORDER BY created_at DESC", ARRAY_A);
    
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="vanionline_subscribers_' . date('Y-m-d') . '.csv"');
    header('Pragma: no-cache');
    header('Expires: 0');
    
    $output = fopen('php://output', 'w');
    fputcsv($output, array('Email', 'Status', 'Consent', 'Consent Timestamp', 'Source', 'Created At'));
    
    if (!empty($subscribers)) {
        foreach ($subscribers as $row) {
            fputcsv($output, $row);
        }
    }
    fclose($output);
    exit;
}

// 4. Simple WordPress Dashboard Stats Widget
add_action('wp_dashboard_setup', 'vani_core_add_dashboard_widget');
function vani_core_add_dashboard_widget() {
    wp_add_dashboard_widget(
        'vani_core_stats_widget',
        '📊 VaniOnline Story Engagement Summary',
        'vani_core_render_dashboard_widget'
    );
}

function vani_core_render_dashboard_widget() {
    global $wpdb;
    $sub_table = $wpdb->prefix . 'vani_subscribers';
    $events_table = $wpdb->prefix . 'vani_analytics_events';
    
    $total_stories = wp_count_posts('post')->publish;
    
    // Count stories with audio
    $audio_stories = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM $wpdb->postmeta WHERE meta_key = '_vani_audio_url' AND meta_value != ''");
    
    // Total subscribers
    $total_subscribers = $wpdb->get_var("SELECT COUNT(*) FROM $sub_table WHERE status = 'active'");
    
    // Analytics stats
    $plays = $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM $events_table WHERE event = %s", 'audio_play'));
    $completions = $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM $events_table WHERE event = %s", 'story_complete'));
    $downloads = $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM $events_table WHERE event = %s", 'pdf_download'));
    ?>
    <div style="padding:10px 0;">
        <ul style="margin: 0; padding: 0; list-style: none;">
            <li style="padding: 6px 0; border-bottom: 1px solid #eee;">📚 <strong>Total Stories Published:</strong> <?php echo intval($total_stories); ?></li>
            <li style="padding: 6px 0; border-bottom: 1px solid #eee;">🎙️ <strong>Audio Enabled Stories:</strong> <?php echo intval($audio_stories); ?></li>
            <li style="padding: 6px 0; border-bottom: 1px solid #eee;">👥 <strong>Active Email Subscribers:</strong> <?php echo intval($total_subscribers); ?></li>
            <li style="padding: 6px 0; border-bottom: 1px solid #eee;">▶️ <strong>Audio Playbacks Started:</strong> <?php echo intval($plays); ?></li>
            <li style="padding: 6px 0; border-bottom: 1px solid #eee;">🎓 <strong>Story Reading Completions (90% scrolled):</strong> <?php echo intval($completions); ?></li>
            <li style="padding: 6px 0;">📥 <strong>PDF Lead Magnet Downloads:</strong> <?php echo intval($downloads); ?></li>
        </ul>
        <p style="margin-top: 15px;"><a href="admin.php?page=vani-subscribers" class="button">Manage Subscribers</a></p>
    </div>
    <?php
}

// Clean up legacy conflicting _wp_old_slug for Post 796 so Benny Bear loads directly
add_action('init', 'vani_cleanup_legacy_post796_redirect');
function vani_cleanup_legacy_post796_redirect() {
    global $wpdb;
    $wpdb->query("DELETE FROM {$wpdb->postmeta} WHERE meta_key = '_wp_old_slug' AND meta_value = 'bedtime-stories-for-kids-benny-bear-fallen-star'");
}

// Prevent WordPress canonical fuzzy redirect from collapsing Post 796 into Post 715
add_filter('redirect_canonical', 'vani_disable_post796_canonical_redirect', 10, 2);
function vani_disable_post796_canonical_redirect($redirect_url, $requested_url) {
    if (strpos($requested_url, 'benny-bear-fallen-star') !== false) {
        return false;
    }
    return $redirect_url;
}

// Disable old slug redirect for Post 796
add_action('template_redirect', function() {
    if (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], 'benny-bear-fallen-star') !== false) {
        remove_action('template_redirect', 'wp_old_slug_redirect');
    }
}, 1);

// Intercept wp_redirect for post 796 and trace caller
add_filter('wp_redirect', 'vani_debug_post796_redirect_caller', 10, 2);
function vani_debug_post796_redirect_caller($location, $status) {
    if (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], 'benny-bear-fallen-star') !== false) {
        $trace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 8);
        $callers = array();
        foreach ($trace as $t) {
            $f = isset($t['file']) ? basename($t['file']) : '';
            $l = isset($t['line']) ? $t['line'] : '';
            $fn = isset($t['function']) ? $t['function'] : '';
            $callers[] = "$f:$l($fn)";
        }
        header('X-Redirect-Caller: ' . implode(' > ', $callers));
    }
    return $location;
}
