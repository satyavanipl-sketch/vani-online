jQuery(document).ready(function($){
    // Only run on single post detail views
    if ($('body').hasClass('single-post')) {
        var postId = vani_core_vars.post_id;
        var nonce = vani_core_vars.nonce;
        var ajaxUrl = vani_core_vars.ajax_url;
        
        // 1. Log story_view event on page load
        logVaniEvent('story_view');
        
        // 2. Track 90% scroll depth for story_complete event
        var storyContent = $('.entry-content');
        if (storyContent.length) {
            var contentHeight = storyContent.outerHeight();
            var contentTop = storyContent.offset().top;
            var loggedComplete = false;
            
            $(window).on('scroll', function() {
                if (loggedComplete) return;
                
                var scrollBottom = $(window).scrollTop() + $(window).height();
                var triggerPoint = contentTop + (contentHeight * 0.90);
                
                if (scrollBottom >= triggerPoint) {
                    loggedComplete = true;
                    logVaniEvent('story_complete');
                }
            });
        }
        
        // 3. Track clicks on related stories
        $('.related-posts a, .vani-related-story-link').on('click', function(){
            logVaniEvent('related_story_click');
        });
        
        // 4. Track clicks on Google Web Story links
        $('.vani-web-story-link').on('click', function(){
            logVaniEvent('web_story_click');
        });
        
        function logVaniEvent(event_name) {
            $.ajax({
                type: 'POST',
                url: ajaxUrl,
                data: {
                    action: 'vani_log_event',
                    event: event_name,
                    post_id: postId,
                    nonce: nonce
                }
            });
        }
    }
    
    // 5. Track clicks on the PDF lead magnet landing page
    if ($('body').hasClass('page-template-default') || $('.vani-lead-box').length) {
        // Track lead magnet banner views
        var loggedView = false;
        if ($('.vani-lead-box').length && !loggedView) {
            loggedView = true;
            $.ajax({
                type: 'POST',
                url: vani_core_vars.ajax_url,
                data: {
                    action: 'vani_log_event',
                    event: 'lead_magnet_view',
                    post_id: vani_core_vars.post_id,
                    nonce: vani_core_vars.nonce
                }
            });
        }
    }
});
