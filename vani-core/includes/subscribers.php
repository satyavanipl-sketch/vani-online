<?php
defined('ABSPATH') || exit;

define('VANI_SUBSCRIBERS_DB_VERSION', '1.0.0');

function vani_setup_subscribers_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE $table_name (
        id bigint(20) NOT NULL AUTO_INCREMENT,
        email varchar(100) NOT NULL,
        status varchar(20) DEFAULT 'active' NOT NULL,
        consent tinyint(1) DEFAULT 0 NOT NULL,
        consent_timestamp datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
        source varchar(50) DEFAULT '' NOT NULL,
        created_at datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
        updated_at datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
        PRIMARY KEY  (id),
        UNIQUE KEY email (email)
    ) $charset_collate;";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta($sql);

    add_option('vani_subscribers_db_version', VANI_SUBSCRIBERS_DB_VERSION);
}

// Check for existing subscriber
function vani_get_subscriber_by_email($email) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    return $wpdb->get_row($wpdb->prepare("SELECT * FROM $table_name WHERE email = %s", $email));
}

// Insert new subscriber
function vani_add_subscriber($email, $consent, $source = 'lead_magnet') {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    
    $existing = vani_get_subscriber_by_email($email);
    if ($existing) {
        if ($existing->status === 'unsubscribed' || $existing->status === 'deleted') {
            // Reactivate subscriber
            $wpdb->update(
                $table_name,
                array(
                    'status' => 'active',
                    'consent' => $consent ? 1 : 0,
                    'consent_timestamp' => current_time('mysql'),
                    'source' => $source,
                    'updated_at' => current_time('mysql')
                ),
                array('id' => $existing->id),
                array('%s', '%d', '%s', '%s', '%s'),
                array('%d')
            );
            return $existing->id;
        }
        return false; // Already active
    }

    $wpdb->insert(
        $table_name,
        array(
            'email' => $email,
            'status' => 'active',
            'consent' => $consent ? 1 : 0,
            'consent_timestamp' => current_time('mysql'),
            'source' => $source,
            'created_at' => current_time('mysql'),
            'updated_at' => current_time('mysql')
        ),
        array('%s', '%s', '%d', '%s', '%s', '%s', '%s')
    );
    
    return $wpdb->insert_id;
}

// Delete subscriber (restricted)
function vani_delete_subscriber($id) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'vani_subscribers';
    
    // We update status to 'deleted' to satisfy retention/privacy, or do a hard delete
    // The prompt says "Delete subscriber" and "Status values should support active, unsubscribed, deleted"
    // So we will perform a soft delete (update status to deleted) or hard delete if required. Let's do a soft delete.
    return $wpdb->update(
        $table_name,
        array(
            'status' => 'deleted',
            'updated_at' => current_time('mysql')
        ),
        array('id' => $id),
        array('%s', '%s'),
        array('%d')
    );
}
