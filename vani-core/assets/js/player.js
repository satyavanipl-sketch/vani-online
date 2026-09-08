jQuery(document).ready(function($){
    $('.vani-audio-player').each(function(){
        var player = $(this);
        var url = player.data('url');
        if (!url) return;
        
        var audio = new Audio();
        audio.src = url;
        audio.preload = 'none';
        
        var playBtn = player.find('.vani-play-btn');
        var playIcon = playBtn.find('.play-icon');
        var pauseIcon = playBtn.find('.pause-icon');
        
        var progressBar = player.find('.vani-progress-bar');
        var currentTimeText = player.find('.vani-current-time');
        var durationTimeText = player.find('.vani-duration');
        
        var speedBtn = player.find('.vani-speed-btn');
        var speedMenu = player.find('.vani-speed-menu');
        
        var volumeBtn = player.find('.vani-volume-btn');
        var volumeSlider = player.find('.vani-volume-slider');
        var volUpIcon = volumeBtn.find('.vol-up-icon');
        var volMuteIcon = volumeBtn.find('.vol-mute-icon');
        
        var playLogged = false;
        var completeLogged = false;
        
        // Helper to format time
        function formatTime(secs) {
            var m = Math.floor(secs / 60);
            var s = Math.floor(secs % 60);
            return m + ':' + (s < 10 ? '0' : '') + s;
        }
        
        // Play / Pause Toggle
        playBtn.on('click', function(){
            if (audio.paused) {
                audio.play();
                playIcon.hide();
                pauseIcon.show();
                
                // Log play event once per play session
                if (!playLogged) {
                    playLogged = true;
                    logVaniEvent('audio_play');
                }
            } else {
                audio.pause();
                playIcon.show();
                pauseIcon.hide();
            }
        });
        
        // Update progress bar & time
        audio.addEventListener('timeupdate', function(){
            if (!audio.duration) return;
            var pct = (audio.currentTime / audio.duration) * 100;
            progressBar.val(pct);
            currentTimeText.text(formatTime(audio.currentTime));
        });
        
        // Track metadata load to set exact duration if not preset
        audio.addEventListener('loadedmetadata', function(){
            durationTimeText.text(formatTime(audio.duration));
        });
        
        // Scrubbing/Seeking progress bar
        progressBar.on('input change', function(){
            if (!audio.duration) return;
            var seekTo = (progressBar.val() / 100) * audio.duration;
            audio.currentTime = seekTo;
        });
        
        // Audio Ended Event
        audio.addEventListener('ended', function(){
            playIcon.show();
            pauseIcon.hide();
            progressBar.val(0);
            currentTimeText.text('0:00');
            
            // Log audio complete event
            if (!completeLogged) {
                completeLogged = true;
                logVaniEvent('audio_complete');
            }
        });
        
        // Speed Menu Toggle
        speedBtn.on('click', function(e){
            e.stopPropagation();
            speedMenu.toggle();
        });
        
        player.find('.vani-speed-option').on('click', function(){
            var opt = $(this);
            var speed = parseFloat(opt.data('speed'));
            audio.defaultPlaybackRate = speed;
            audio.playbackRate = speed;
            
            player.find('.vani-speed-option').removeClass('active');
            opt.addClass('active');
            speedBtn.text(speed + 'x');
            speedMenu.hide();
        });
        
        // Close speed menu when clicking elsewhere
        $(document).on('click', function(){
            speedMenu.hide();
        });
        
        // Volume controls
        volumeSlider.on('input change', function(){
            var vol = volumeSlider.val() / 100;
            audio.volume = vol;
            if (vol === 0) {
                volUpIcon.hide();
                volMuteIcon.show();
            } else {
                volUpIcon.show();
                volMuteIcon.hide();
            }
        });
        
        volumeBtn.on('click', function(){
            if (audio.muted) {
                audio.muted = false;
                volUpIcon.show();
                volMuteIcon.hide();
                volumeSlider.val(audio.volume * 100);
            } else {
                audio.muted = true;
                volUpIcon.hide();
                volMuteIcon.show();
                volumeSlider.val(0);
            }
        });
        
        // Analytics AJAX logging helper
        function logVaniEvent(event_name) {
            $.ajax({
                type: 'POST',
                url: vani_core_vars.ajax_url,
                data: {
                    action: 'vani_log_event',
                    event: event_name,
                    post_id: vani_core_vars.post_id,
                    nonce: vani_core_vars.nonce
                }
            });
        }
    });
});
