<?php
defined('ABSPATH') || exit;

// Shortcode: [vani_lead_magnet_form]
add_shortcode('vani_lead_magnet_form', 'vani_render_lead_form');
function vani_render_lead_form() {
    // Check if user has already submitted and has a token in URL or session
    // We render the form with honeypot, nonce, and privacy link
    $privacy_url = get_privacy_policy_url();
    if (empty($privacy_url)) {
        // Log admin warning if not configured
        if (is_admin()) {
            add_action('admin_notices', function() {
                echo '<div class="notice notice-warning"><p><strong>Vani Warning:</strong> No Privacy Policy Page is configured in WordPress. Please set one in Settings -> Privacy.</p></div>';
            });
        }
        $privacy_link = '<span style="color:red;">Privacy Policy (not configured)</span>';
    } else {
        $privacy_link = '<a href="' . esc_url($privacy_url) . '" target="_blank">Privacy Policy</a>';
    }

    ob_start();
    ?>
    <div class="vani-lead-box">
        <form id="vani_lead_form" method="POST" class="vani-form">
            <?php wp_nonce_field('vani_lead_submit', 'vani_nonce'); ?>
            
            <!-- Honeypot field (hidden from users) -->
            <div style="display:none;">
                <label for="vani_hp_field">Do not fill this field if you are human:</label>
                <input type="text" id="vani_hp_field" name="vani_hp_field" value="" autocomplete="off" />
            </div>
            
            <div class="vani-form-group">
                <label for="vani_email"><strong>Your Email Address:</strong></label><br>
                <input type="email" id="vani_email" name="vani_email" required placeholder="name@example.com" class="vani-input" />
            </div>
            
            <div class="vani-form-group consent-group">
                <input type="checkbox" id="vani_consent" name="vani_consent" value="1" required />
                <label for="vani_consent">I agree to receive VaniOnline bedtime story emails and understand the <?php echo $privacy_link; ?>.</label>
            </div>
            
            <button type="submit" class="vani-submit-btn">Get the Free Stories 🎒</button>
            <div class="vani-form-message" style="margin-top:15px; font-weight:bold;"></div>
        </form>
    </div>
    
    <script>
    jQuery(document).ready(function($){
        $('#vani_lead_form').on('submit', function(e){
            e.preventDefault();
            var form = $(this);
            var msgDiv = form.find('.vani-form-message');
            msgDiv.text('Submitting...').css('color', '#333');
            
            $.ajax({
                type: 'POST',
                url: vani_core_vars.ajax_url,
                data: form.serialize() + '&action=vani_submit_lead',
                success: function(response) {
                    if (response.success) {
                        msgDiv.text('Success! Redirecting to download...').css('color', 'green');
                        // Redirect to the success success page
                        window.location.href = response.data.redirect_url;
                    } else {
                        msgDiv.text(response.data.message).css('color', 'red');
                    }
                },
                error: function() {
                    msgDiv.text('An error occurred. Please try again.').css('color', 'red');
                }
            });
        });
    });
    </script>
    <?php
    return ob_get_clean();
}

// Shortcode: [vani_download_success]
add_shortcode('vani_download_success', 'vani_render_download_success');
function vani_render_download_success() {
    $token = isset($_GET['token']) ? sanitize_text_field($_GET['token']) : '';
    if (empty($token)) {
        return '<p style="color:red;">Error: Access denied. Please sign up to access free downloads.</p>';
    }
    
    // Validate token exists in WordPress transients
    $email = get_transient('vani_download_token_' . $token);
    if (!$email) {
        return '<p style="color:red;">Error: Your download link has expired or is invalid. Please sign up again.</p>';
    }
    
    $download_url = add_query_arg(array(
        'vani_download_pdf' => '1',
        'token' => $token
    ), home_url('/'));
    
    ob_start();
    ?>
    <div class="vani-success-box" style="text-align: center; padding: 40px; background: #f9f9f9; border-radius: 12px;">
        <h2 style="color: #27ae60;">🎉 Your free bedtime stories are ready!</h2>
        <p style="margin-bottom: 30px;">Thank you for subscribing. You can now download the PDF collection of bedtime stories.</p>
        
        <p>
            <a href="<?php echo esc_url($download_url); ?>" class="button vani-btn-primary" style="background: #2ecc71; color:#fff; padding: 15px 30px; border-radius: 30px; text-decoration:none; font-size: 18px; font-weight:bold; display:inline-block;">Download the 10 Stories 📥</a>
        </p>
        
        <p style="margin-top: 30px;">
            <a href="<?php echo home_url('/stories-for-kids/'); ?>" class="vani-link-secondary" style="font-weight:bold; color:#3498db;">Explore More VaniOnline Stories →</a>
        </p>
    </div>
    <?php
    return ob_get_clean();
}

// AJAX Handler for Lead Form submissions
add_action('wp_ajax_nopriv_vani_submit_lead', 'vani_ajax_submit_lead');
add_action('wp_ajax_vani_submit_lead', 'vani_ajax_submit_lead');

function vani_ajax_submit_lead() {
    // 1. Verify Nonce / CSRF
    if (!isset($_POST['vani_nonce']) || !wp_verify_nonce($_POST['vani_nonce'], 'vani_lead_submit')) {
        wp_send_json_error(array('message' => 'Security check failed. Please refresh the page and try again.'));
    }
    
    // 2. Honeypot check
    if (!empty($_POST['vani_hp_field'])) {
        wp_send_json_success(array('redirect_url' => home_url('/'))); // Silently redirect spam bots
    }
    
    // 3. Rate Limit check (max 5 submissions per session per hour)
    if (isset($_SESSION['vani_lead_sub_count']) && $_SESSION['vani_lead_sub_count'] > 5) {
        wp_send_json_error(array('message' => 'Too many signups. Please try again later.'));
    }
    
    // 4. Validate Email
    $email = isset($_POST['vani_email']) ? sanitize_email($_POST['vani_email']) : '';
    if (!is_email($email)) {
        wp_send_json_error(array('message' => 'Please enter a valid email address.'));
    }
    
    // 5. Consent Check
    $consent = isset($_POST['vani_consent']) ? intval($_POST['vani_consent']) : 0;
    if ($consent !== 1) {
        wp_send_json_error(array('message' => 'You must agree to the privacy consent terms to proceed.'));
    }
    
    // Increment rate limit session count
    if (!headers_sent() && !session_id()) {
        session_start();
    }
    $_SESSION['vani_lead_sub_count'] = isset($_SESSION['vani_lead_sub_count']) ? $_SESSION['vani_lead_sub_count'] + 1 : 1;
    
    // 6. Insert Subscriber in database
    $sub_id = vani_add_subscriber($email, $consent, 'lead_magnet_landing');
    
    // Track signup view event
    vani_log_analytics_event('lead_magnet_signup');
    
    // 7. Create temporary expiring download token (valid for 1 hour = 3600s)
    $token = md5(uniqid(rand(), true) . $email);
    set_transient('vani_download_token_' . $token, $email, 3600);
    
    // Success Redirect URL
    // Create the page /success/ or dynamic url
    $redirect_url = add_query_arg('token', $token, home_url('/free-bedtime-stories/success/'));
    
    wp_send_json_success(array(
        'message' => 'Successfully subscribed!',
        'redirect_url' => $redirect_url
    ));
}

// Handle secure PDF download file streaming
add_action('template_redirect', 'vani_handle_pdf_download');
function vani_handle_pdf_download() {
    if (isset($_GET['vani_download_pdf']) && isset($_GET['token'])) {
        $token = sanitize_text_field($_GET['token']);
        $email = get_transient('vani_download_token_' . $token);
        
        if ($email) {
            // Delete transient immediately to ensure single-use
            delete_transient('vani_download_token_' . $token);

            // Track download event
            vani_log_analytics_event('pdf_download');
            
            // Path inside the plugin folder
            $pdf_path = VANI_CORE_PATH . 'assets/10_Free_Bedtime_Stories.pdf';
            if (file_exists($pdf_path)) {
                // Clear any outputs
                if (ob_get_level()) {
                    ob_end_clean();
                }
                header('Content-Type: application/pdf');
                header('Content-Disposition: attachment; filename="10_Free_Bedtime_Stories.pdf"');
                header('Content-Length: ' . filesize($pdf_path));
                header('Pragma: no-cache');
                header('Expires: 0');
                readfile($pdf_path);
                exit;
            } else {
                wp_die('Error: PDF file could not be retrieved from secure storage.', 'File Not Found', array('response' => 404));
            }
        } else {
            wp_die('Error: Your download token has expired or is invalid. Please sign up again.', 'Token Expired', array('response' => 403));
        }
    }
}
