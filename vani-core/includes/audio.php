<?php
defined('ABSPATH') || exit;

// Register Meta Fields
add_action('init', 'vani_register_audio_meta');
function vani_register_audio_meta() {
    register_post_meta('post', '_vani_audio_url', array(
        'show_in_rest' => true,
        'single' => true,
        'type' => 'string',
    ));
    register_post_meta('post', '_vani_audio_duration', array(
        'show_in_rest' => true,
        'single' => true,
        'type' => 'integer',
    ));
}

// Add Metabox to Edit Screens
add_action('add_meta_boxes', 'vani_add_audio_metabox');
function vani_add_audio_metabox() {
    add_meta_box(
        'vani_audio_settings',
        'Vani Audio Story Settings',
        'vani_audio_metabox_html',
        'post',
        'normal',
        'high'
    );
}

function vani_audio_metabox_html($post) {
    $audio_url = get_post_meta($post->ID, '_vani_audio_url', true);
    $duration = get_post_meta($post->ID, '_vani_audio_duration', true);
    
    // Format duration string if exists
    $duration_str = '';
    if (!empty($duration)) {
        $minutes = floor($duration / 60);
        $seconds = $duration % 60;
        $duration_str = sprintf('%d:%02d', $minutes, $seconds);
    }
    
    wp_nonce_field('vani_audio_save', 'vani_audio_nonce');
    ?>
    <div style="padding: 10px 0;">
        <p>
            <label for="vani_audio_url"><strong>Audio File URL:</strong></label><br>
            <input type="text" id="vani_audio_url" name="vani_audio_url" value="<?php echo esc_attr($audio_url); ?>" style="width: 75%;" />
            <button type="button" class="button" id="vani_upload_audio_btn">Upload / Select Audio</button>
        </p>
        <p>
            <label for="vani_audio_duration"><strong>Audio Duration (MM:SS or seconds):</strong></label><br>
            <input type="text" id="vani_audio_duration" name="vani_audio_duration" value="<?php echo esc_attr($duration_str); ?>" style="width: 25%;" />
            <span class="description">Automatically detected when saving a selected library attachment. Leave empty to auto-detect.</span>
        </p>
    </div>
    
    <script>
    jQuery(document).ready(function($){
        var file_frame;
        $('#vani_upload_audio_btn').on('click', function(e){
            e.preventDefault();
            if (file_frame) {
                file_frame.open();
                return;
            }
            file_frame = wp.media.frames.file_frame = wp.media({
                title: 'Select Audio File',
                button: { text: 'Use this Audio' },
                multiple: false,
                library: { type: 'audio' }
            });
            file_frame.on('select', function() {
                var attachment = file_frame.state().get('selection').first().toJSON();
                $('#vani_audio_url').val(attachment.url);
                if (attachment.meta && attachment.meta.length_formatted) {
                    $('#vani_audio_duration').val(attachment.meta.length_formatted);
                } else if (attachment.meta && attachment.meta.length) {
                    var secs = Math.round(attachment.meta.length);
                    var min = Math.floor(secs / 60);
                    var rem = secs % 60;
                    $('#vani_audio_duration').val(min + ':' + (rem < 10 ? '0' : '') + rem);
                }
            });
            file_frame.open();
        });
    });
    </script>
    <?php
}

// Save Meta Box Data
add_action('save_post', 'vani_save_audio_meta');
function vani_save_audio_meta($post_id) {
    if (!isset($_POST['vani_audio_nonce']) || !wp_verify_nonce($_POST['vani_audio_nonce'], 'vani_audio_save')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;
    
    if (isset($_POST['vani_audio_url'])) {
        $audio_url = sanitize_text_field($_POST['vani_audio_url']);
        update_post_meta($post_id, '_vani_audio_url', $audio_url);
        
        $manual_duration = isset($_POST['vani_audio_duration']) ? sanitize_text_field($_POST['vani_audio_duration']) : '';
        
        if (!empty($manual_duration)) {
            if (strpos($manual_duration, ':') !== false) {
                $parts = explode(':', $manual_duration);
                $seconds = intval($parts[0]) * 60 + intval($parts[1]);
            } else {
                $seconds = intval($manual_duration);
            }
            update_post_meta($post_id, '_vani_audio_duration', $seconds);
        } else if (!empty($audio_url)) {
            // Attempt auto detect duration
            global $wpdb;
            $attachment_id = $wpdb->get_var($wpdb->prepare("SELECT ID FROM $wpdb->posts WHERE guid = %s", $audio_url));
            if ($attachment_id) {
                $metadata = wp_get_attachment_metadata($attachment_id);
                if ($metadata && isset($metadata['length'])) {
                    update_post_meta($post_id, '_vani_audio_duration', round($metadata['length']));
                }
            }
        } else {
            delete_post_meta($post_id, '_vani_audio_duration');
        }
    }
}

// Render Audio Player HTML
function vani_render_audio_player($url, $duration_seconds) {
    if (empty($url)) return '';
    $minutes = floor($duration_seconds / 60);
    $seconds = $duration_seconds % 60;
    $duration_str = sprintf('%d:%02d', $minutes, $seconds);
    
    ob_start();
    ?>
    <div class="vani-audio-player" data-url="<?php echo esc_url($url); ?>">
        <div class="vani-player-title">🎵 Listen to This Story</div>
        <div class="vani-player-controls">
            <button class="vani-play-btn" aria-label="Play audio">
                <svg class="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>
                <svg class="pause-icon" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" fill="currentColor"/></svg>
            </button>
            <span class="vani-time vani-current-time">0:00</span>
            <div class="vani-progress-container">
                <input type="range" class="vani-progress-bar" min="0" max="100" value="0" aria-label="Audio progress">
            </div>
            <span class="vani-time vani-duration"><?php echo esc_html($duration_str); ?></span>
            
            <div class="vani-speed-container">
                <button class="vani-speed-btn" aria-label="Playback speed">1x</button>
                <div class="vani-speed-menu" style="display:none;">
                    <div class="vani-speed-option" data-speed="0.75">0.75x</div>
                    <div class="vani-speed-option active" data-speed="1.0">1x</div>
                    <div class="vani-speed-option" data-speed="1.25">1.25x</div>
                    <div class="vani-speed-option" data-speed="1.5">1.5x</div>
                </div>
            </div>
            
            <div class="vani-volume-container">
                <button class="vani-volume-btn" aria-label="Mute">
                    <svg class="vol-up-icon" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" fill="currentColor"/></svg>
                    <svg class="vol-mute-icon" viewBox="0 0 24 24" style="display:none;"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.21.05-.42.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73 4.27 3zM12 4L9.91 6.09 12 8.18V4z" fill="currentColor"/></svg>
                </button>
                <input type="range" class="vani-volume-slider" min="0" max="100" value="80" aria-label="Volume">
            </div>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

// Injected audio player into single post template content
add_filter('the_content', 'vani_inject_audio_player');
function vani_inject_audio_player($content) {
    if (is_single() && get_post_type() === 'post' && in_the_loop() && is_main_query()) {
        $audio_url = get_post_meta(get_the_ID(), '_vani_audio_url', true);
        $duration = get_post_meta(get_the_ID(), '_vani_audio_duration', true);
        
        if (!empty($audio_url)) {
            $player_html = vani_render_audio_player($audio_url, $duration);
            
            // Inject after first paragraph
            if (strpos($content, '</p>') !== false) {
                $pos = strpos($content, '</p>') + 4;
                $content = substr_replace($content, $player_html, $pos, 0);
            } else {
                $content = $player_html . $content;
            }
        }
    }
    return $content;
}

// Schema AudioObject Structured Data
add_action('wp_head', 'vani_inject_audio_schema');
function vani_inject_audio_schema() {
    if (is_single() && get_post_type() === 'post') {
        $audio_url = get_post_meta(get_the_ID(), '_vani_audio_url', true);
        $duration = get_post_meta(get_the_ID(), '_vani_audio_duration', true);
        
        if (!empty($audio_url)) {
            $mins = floor($duration / 60);
            $secs = $duration % 60;
            $iso_duration = sprintf('PT%dM%dS', $mins, $secs);
            
            $post_title = get_the_title();
            $post_excerpt = wp_strip_all_tags(get_the_excerpt());
            $upload_date = get_the_date('c');
            
            $schema = array(
                '@context' => 'https://schema.org',
                '@type' => 'AudioObject',
                'name' => $post_title . ' - Audio Story',
                'description' => $post_excerpt,
                'contentUrl' => $audio_url,
                'duration' => $iso_duration,
                'encodingFormat' => 'audio/mpeg',
                'uploadDate' => $upload_date
            );
            
            echo "\n<!-- Vani Audio Story Structured Data -->\n";
            echo '<script type="application/ld+json">' . json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT) . "</script>\n";
        }
    }
}

// Shortcode: [vani_audio_stories]
add_shortcode('vani_audio_stories', 'vani_render_audio_stories_shortcode');
function vani_render_audio_stories_shortcode() {
    $args = array(
        'post_type' => 'post',
        'posts_per_page' => -1,
        'post_status' => 'publish',
        'meta_query' => array(
            array(
                'key' => '_vani_audio_url',
                'value' => '',
                'compare' => '!='
            )
        )
    );
    $query = new WP_Query($args);
    
    if (!$query->have_posts()) {
        return '<p>No audio stories available yet. Check back soon!</p>';
    }
    
    ob_start();
    ?>
    <div id="two-column" class="blog-portfolio vani-audio-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; margin-top:20px;">
        <?php while ($query->have_posts()): $query->the_post(); 
            $post_id = get_the_ID();
            $audio_url = get_post_meta($post_id, '_vani_audio_url', true);
            $duration = get_post_meta($post_id, '_vani_audio_duration', true);
            
            $duration_str = '--';
            if (!empty($duration)) {
                $minutes = floor($duration / 60);
                $seconds = $duration % 60;
                $duration_str = sprintf('%d:%02d', $minutes, $seconds);
            }
            
            // Get age group
            $categories = get_the_category($post_id);
            $age_group = 'All Ages';
            foreach ($categories as $cat) {
                if (strpos($cat->name, 'Year-Olds') !== false || strpos($cat->name, 'Age') !== false) {
                    $age_group = str_replace('Stories for ', '', $cat->name);
                    break;
                }
            }
            
            // Calculate reading time
            $reading_time = vani_get_reading_time(get_post_field('post_content', $post_id));
            ?>
            <article class="blog-item has-post-thumbnail hentry" style="margin-bottom: 0; background: #fff; border: 1px solid #eee; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                <div class="blog-post-wrap" style="padding: 0;">
                    <?php if (has_post_thumbnail()): ?>
                        <div class="post-thumbnail" style="aspect-ratio: 3/2; overflow: hidden;">
                            <a href="<?php the_permalink(); ?>"><?php the_post_thumbnail('medium', array('style' => 'width:100%; height:100%; object-fit:cover;')); ?></a>
                        </div>
                    <?php endif; ?>
                    
                    <div style="padding: 20px;">
                        <header class="entry-header">
                            <h2 class="entry-title" style="font-size: 18px; margin-top: 0;"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                            <p class="entry-meta" style="font-size: 12px; color: #7f8c8d; margin-bottom: 12px;">
                                <span>🎂 Age: <?php echo esc_html($age_group); ?></span> | 
                                <span>📖 <?php echo esc_html($reading_time); ?> min read</span> | 
                                <span>🎧 <?php echo esc_html($duration_str); ?></span>
                            </p>
                        </header>
                        
                        <div class="entry-content">
                            <p style="font-size: 14px; line-height: 1.5; color: #555;"><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
                            <a href="<?php the_permalink(); ?>" class="read-more" style="background:#2ecc71; color:white; padding:8px 16px; border-radius:20px; text-decoration:none; display:inline-block; font-weight:bold; font-size:13px; margin-top: 10px;">Listen to Story 🎙/a>
                        </div>
                    </div>
                </div>
            </article>
        <?php endwhile; wp_reset_postdata(); ?>
    </div>
    <?php
    return ob_get_clean();
}
