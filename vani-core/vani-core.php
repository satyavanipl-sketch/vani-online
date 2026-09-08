<?php
/**
 * Plugin Name: Vani Core
 * Description: Core functional plugin for VaniOnline.com. Handles Audio Story player, lead magnets, subscribers, web-stories mapping, and analytics event logging.
 * Version: 1.0.0
 * Author: Antigravity
 * License: GPL2
 */

defined('ABSPATH') || exit;

define('VANI_CORE_VERSION', '1.0.0');
define('VANI_CORE_PATH', plugin_dir_path(__FILE__));
define('VANI_CORE_URL', plugin_dir_url(__FILE__));

// Activation / Deactivation hooks
register_activation_hook(__FILE__, 'vani_core_activate');
register_deactivation_hook(__FILE__, 'vani_core_deactivate');

function vani_core_activate() {
    require_once VANI_CORE_PATH . 'includes/subscribers.php';
    require_once VANI_CORE_PATH . 'includes/analytics.php';
    
    // Setup Database Tables
    vani_setup_subscribers_table();
    vani_setup_analytics_table();
    
    // Flush rewrite rules on activation
    flush_rewrite_rules();
}

function vani_core_deactivate() {
    flush_rewrite_rules();
}

// Load include files
require_once VANI_CORE_PATH . 'includes/subscribers.php';
require_once VANI_CORE_PATH . 'includes/analytics.php';
require_once VANI_CORE_PATH . 'includes/audio.php';
require_once VANI_CORE_PATH . 'includes/web-stories.php';
require_once VANI_CORE_PATH . 'includes/lead-magnet.php';
require_once VANI_CORE_PATH . 'includes/admin.php';

// Enqueue frontend scripts and styles
add_action('wp_enqueue_scripts', 'vani_core_enqueue_assets');
function vani_core_enqueue_assets() {
    wp_enqueue_style('vani-core-player', VANI_CORE_URL . 'assets/css/player.css', array(), VANI_CORE_VERSION);
    wp_enqueue_script('vani-core-player-js', VANI_CORE_URL . 'assets/js/player.js', array('jquery'), VANI_CORE_VERSION, true);
    wp_enqueue_script('vani-core-analytics-js', VANI_CORE_URL . 'assets/js/analytics.js', array('jquery'), VANI_CORE_VERSION, true);
    
    // Pass AJAX details to javascript
    wp_localize_script('vani-core-player-js', 'vani_core_vars', array(
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce'    => wp_create_nonce('vani_core_nonce'),
        'post_id'  => get_the_ID()
    ));
}

// Inject critical global styles for header dropdown navigation & high-contrast post text
add_action('wp_head', 'vani_core_custom_head_styles', 999);
function vani_core_custom_head_styles() {
    ?>
    <style id="vani-core-global-fixes">
        header.site-header, #masthead {
            z-index: 99999 !important;
            position: relative !important;
            background-color: #ffffff !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }
        .main-navigation ul ul, .nav-menu ul, .sub-menu, .children {
            background-color: #ffffff !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15) !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            z-index: 999999 !important;
            border: 1px solid #e2e8f0 !important;
        }
        .main-navigation ul ul a, .nav-menu ul a, .sub-menu a, .children a {
            color: #1e293b !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 8px 12px !important;
            display: block !important;
            white-space: nowrap !important;
            background: transparent !important;
        }
        .main-navigation ul ul a:hover, .nav-menu ul a:hover, .sub-menu a:hover, .children a:hover {
            color: #0284c7 !important;
            background-color: #f1f5f9 !important;
            border-radius: 6px !important;
        }
        .main-navigation a, .nav-menu > li > a {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        .entry-content, .blog-post-wrap, article {
            color: #0f172a !important;
        }
        .entry-content p {
            color: #0f172a !important;
            font-size: 17px !important;
            line-height: 1.8 !important;
        }
        .entry-content h1, .entry-content h2, .entry-content h3, .entry-content h4 {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        .entry-content ul li, .entry-content ol li, .entry-content li {
            color: #1e293b !important;
            font-size: 16px !important;
            line-height: 1.8 !important;
        }
        .story-intro-box {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border-left: 6px solid #10b981 !important;
            border-radius: 12px !important;
            padding: 22px 25px !important;
            margin: 25px 0 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }
        .story-intro-box h3 { color: #047857 !important; margin-top: 0 !important; }
        .story-intro-box ul, .story-intro-box li { color: #334155 !important; }
        .story-intro-box li strong { color: #0f172a !important; }
        .story-moral {
            background-color: #fffbeb !important;
            color: #78350f !important;
            border-left: 6px solid #f59e0b !important;
            border-radius: 12px !important;
            padding: 22px 25px !important;
            margin: 20px 0 !important;
            font-size: 17px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        }
        .story-moral strong, .story-moral span { color: #78350f !important; }
    </style>
    <?php
}
