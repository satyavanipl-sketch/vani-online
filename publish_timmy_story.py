import os
import io
import json
import re
import urllib.request
import urllib.parse
import http.cookiejar
from PIL import Image

# Base URLs and setup
base_url = "https://vanionline.com"
login_url = f"{base_url}/wp-login.php"
media_api_url = f"{base_url}/wp-json/wp/v2/media"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"
posts_api_url = f"{base_url}/wp-json/wp/v2/posts"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]

# Story Metadata
story_data = {
    "title": "Timmy the Turtle's Courage | Courage Story for Kids",
    "post_title": "Timmy the Turtle's Courageous Adventure 🐢✨",
    "slug": "timmy-turtle-courage-story-for-kids",
    "focus_keyword": "courage story for kids",
    "seo_title": "Timmy the Turtle's Courage | Courage Story for Kids",
    "seo_description": "Read this uplifting courage story for kids about Timmy the little turtle who finds his inner bravery to help a friend. Inspiring bedtime moral tale.",
    "categories": [1, 2, 27, 35],  # Moral Stories, Bedtime Stories, Animal Stories, Stories for 5-Year-Olds
}

raw_images = [
    {
        "key": "featured",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_cover_1788770020209.jpg",
        "filename": "timmy-turtle-courage-story-cover.webp",
        "alt_text": "Timmy the courageous turtle resting near Whispering Creek - Courage story for kids"
    },
    {
        "key": "scene1",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_scene_1_1788770042033.jpg",
        "filename": "timmy-turtle-whispering-creek.webp",
        "alt_text": "Timmy the little turtle strolling along Whispering Creek path - Courage story for kids"
    },
    {
        "key": "scene2",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_scene_2_1788770064077.jpg",
        "filename": "timmy-turtle-meeting-barnaby-bunny.webp",
        "alt_text": "Timmy the courageous turtle reassuring worried Barnaby bunny - Courage story for kids"
    },
    {
        "key": "scene3",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_scene_3_1788770086840.jpg",
        "filename": "timmy-turtle-braving-dark-forest.webp",
        "alt_text": "Timmy the turtle leading Barnaby bunny through dark forest with fireflies - Courage story for kids"
    },
    {
        "key": "scene4",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_scene_4_1788770112020.jpg",
        "filename": "timmy-turtle-reuniting-bunny-family.webp",
        "alt_text": "Timmy the turtle happily reuniting Barnaby bunny with mother rabbit - Courage story for kids"
    },
    {
        "key": "scene5",
        "raw_path": "/Users/raju/.gemini/antigravity-ide/brain/e4d4c2e6-7a0b-4b25-901b-bec9f4ac757f/timmy_scene_5_1788770140713.jpg",
        "filename": "timmy-turtle-starry-night-courage.webp",
        "alt_text": "Timmy the courageous turtle looking up at starry night sky with forest friends - Courage story for kids"
    }
]

def load_credentials():
    db_file = "/Users/raju/.gemini/antigravity-ide/Vani/backend/db.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            creds = data.get("credentials", {})
            return creds.get("wp_username", "satyavanipl@gmail.com"), creds.get("wp_password", "Satya@2501")
    return "satyavanipl@gmail.com", "Satya@2501"

def login_wp(username, password):
    print("Logging into WordPress...")
    login_data = urllib.parse.urlencode({
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In',
        'testcookie': '1'
    }).encode('utf-8')
    try:
        opener.open(login_url)
        res = opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))
        success = "wp-admin" in res.geturl()
        print(f"Login success: {success}")
        return success
    except Exception as e:
        print(f"WordPress Login failed: {e}")
        return False

def get_rest_nonce():
    print("Fetching REST nonce...")
    req = urllib.request.Request("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings")
    try:
        with opener.open(req) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
            if nonce_match:
                nonce = nonce_match.group(1)
                print(f"Nonce obtained: {nonce}")
                return nonce
    except Exception as e:
        print(f"Failed to fetch REST nonce: {e}")
    return None

def convert_to_webp(input_path, output_path, max_size=(900, 600), quality=85):
    img = Image.open(input_path)
    img = img.convert("RGB")
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    img.save(output_path, "WEBP", quality=quality, optimize=True)
    print(f"Converted {os.path.basename(input_path)} -> {os.path.basename(output_path)} ({os.path.getsize(output_path)//1024} KB)")
    return output_path

def upload_webp_media(rest_nonce, webp_path, filename, alt_text):
    print(f"Uploading media: {filename}...")
    try:
        with open(webp_path, 'rb') as f:
            webp_bytes = f.read()
            
        req = urllib.request.Request(media_api_url, data=webp_bytes, method='POST')
        req.add_header('Content-Type', 'image/webp')
        req.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        req.add_header('X-WP-Nonce', rest_nonce)
        
        with opener.open(req, timeout=30) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            attachment_id = res_json.get("id")
            source_url = res_json.get("source_url")
            
            # Update alt text and title
            update_url = f"{media_api_url}/{attachment_id}"
            update_payload = {
                "alt_text": alt_text,
                "description": alt_text,
                "title": alt_text
            }
            update_data = json.dumps(update_payload).encode('utf-8')
            update_req = urllib.request.Request(update_url, data=update_data, method='POST')
            update_req.add_header('Content-Type', 'application/json; charset=utf-8')
            update_req.add_header('X-WP-Nonce', rest_nonce)
            
            with opener.open(update_req, timeout=15) as update_resp:
                pass
                
            print(f"  Uploaded! ID: {attachment_id}, URL: {source_url}")
            return source_url, attachment_id
    except Exception as e:
        print(f"  Failed to upload media {filename}: {e}")
    return None, None

def build_post_html(uploaded_images):
    img_s1 = uploaded_images.get("scene1", {}).get("url", "")
    alt_s1 = "Timmy the little turtle strolling along Whispering Creek path - Courage story for kids"
    
    img_s2 = uploaded_images.get("scene2", {}).get("url", "")
    alt_s2 = "Timmy the courageous turtle reassuring worried Barnaby bunny - Courage story for kids"
    
    img_s3 = uploaded_images.get("scene3", {}).get("url", "")
    alt_s3 = "Timmy the turtle leading Barnaby bunny through dark forest with fireflies - Courage story for kids"
    
    img_s4 = uploaded_images.get("scene4", {}).get("url", "")
    alt_s4 = "Timmy the turtle happily reuniting Barnaby bunny with mother rabbit - Courage story for kids"
    
    img_s5 = uploaded_images.get("scene5", {}).get("url", "")
    alt_s5 = "Timmy the courageous turtle looking up at starry night sky with forest friends - Courage story for kids"

    left_style = 'float: left !important; margin: 10px 25px 20px 0 !important; border-radius: 24px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'
    right_style = 'float: right !important; margin: 10px 0 20px 25px !important; border-radius: 24px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'

    p_style = 'color: #0f172a !important; font-size: 17px !important; line-height: 1.8 !important; margin-bottom: 18px !important;'
    h2_style = 'clear: both !important; padding-top: 24px !important; color: #0f172a !important; font-size: 24px !important; font-weight: 700 !important;'

    html = f"""<p style="{p_style}">Welcome to an inspiring bedtime tale that will teach your little ones the true power of bravery! This heartwarming <strong>courage story for kids</strong> features Timmy, a gentle little turtle who discovers that real courage does not mean being giant or loud, but taking brave steps to help a friend in need. Perfect for bedtime reading, early learning, or cozy family storytime.</p>

<div class="story-intro-box" style="background-color: #ffffff !important; color: #1e293b !important; border-left: 6px solid #10b981 !important; padding: 22px 25px !important; border-radius: 12px !important; margin: 25px 0 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;">
    <h3 style="margin-top: 0 !important; margin-bottom: 12px !important; color: #047857 !important; font-size: 22px !important; font-weight: 700 !important;">🌟 Story Highlights for Young Readers</h3>
    <ul style="margin-bottom: 0 !important; padding-left: 20px !important; color: #334155 !important; font-size: 16px !important; line-height: 1.8 !important;">
        <li style="color: #334155 !important; margin-bottom: 6px !important;"><strong style="color: #0f172a !important;">Character:</strong> Timmy, a quiet turtle with a smooth green shell and a big brave heart.</li>
        <li style="color: #334155 !important; margin-bottom: 6px !important;"><strong style="color: #0f172a !important;">Core Lesson:</strong> Bravery is moving forward with kindness even when you feel scared inside.</li>
        <li style="color: #334155 !important; margin-bottom: 0 !important;"><strong style="color: #0f172a !important;">Best For:</strong> Preschoolers, kindergarteners, and young kids aged 3 to 8.</li>
    </ul>
</div>

<h2 style="{h2_style}">1. The Quiet Turtle of Whispering Creek</h2>
<img src="{img_s1}" alt="{alt_s1}" class="alignnone size-medium" style="{left_style}" />
<p style="{p_style}">Along the peaceful banks of Whispering Creek lived Timmy, a sweet little turtle who moved with careful, steady steps. While swift jackrabbits bounded past and high-flying hawks soared through the blue sky, Timmy enjoyed admiring the small wonders of nature—colorful river pebbles, blooming wild violet flowers, and gentle dancing dragonflies.</p>
<p style="{p_style}">Some of the younger forest animals thought Timmy was too shy because he often pulled his head into his smooth green shell whenever thunder rumbled. But Timmy’s grandmother always reminded him, "True bravery lives deep inside your heart, little Timmy. When someone needs your help, your courage will shine brighter than the stars."</p>
<p style="{p_style}">Timmy held those wise words closely as he explored the sunny woodland trails every afternoon, always ready to lend a helping hand to his woodland neighbors.</p>

<h2 style="{h2_style}">2. A Worried Friend in the Shadows</h2>
<img src="{img_s2}" alt="{alt_s2}" class="alignnone size-medium" style="{right_style}" />
<p style="{p_style}">One sunny afternoon as the golden sun began dipping behind the tall pine trees, Timmy heard a faint, nervous trembling sound near the edge of the Shady Woods. Stepping gently around a mossy rock, he saw Barnaby, a small fluffy white bunny, shivering beneath a fern leaf.</p>
<p style="{p_style}">Barnaby had wandered too far into the forest while chasing blue butterflies, and now the shadowed trail leading back home looked dark and unfamiliar. "The shadows look scary, Timmy," whimpered Barnaby softly. "My burrow is across the Shadowy Glen, but I am too afraid to walk through alone."</p>
<p style="{p_style}">Timmy’s heart fluttered with nervous butterfly feelings of his own—the Shadowy Glen was indeed dark. Yet he looked at his worried little friend and smiled with warm reassurance. "You do not have to walk alone, Barnaby," Timmy promised gently. "I will walk right beside you."</p>

<h2 style="{h2_style}">3. Braving the Dark Glen Together</h2>
<img src="{img_s3}" alt="{alt_s3}" class="alignnone size-medium" style="{left_style}" />
<p style="{p_style}">Hand in paw, the tiny turtle and little bunny stepped onto the dimly lit forest path. As nocturnal rustles echoed through the tall oak branches, Timmy took deep, steady breaths to keep his courage strong. He knew that being brave did not mean never feeling afraid—it meant taking caring steps forward anyway.</p>
<p style="{p_style}">Suddenly, magical yellow fireflies fluttered out from the surrounding clover, floating together to light up the path with warm golden lanterns! Timmy guided Barnaby safely past tall arching roots and friendly sleeping owls, pointing out the beautiful glowing fireflies to calm Barnaby's fear.</p>
<p style="{p_style}">Step by slow step, Timmy’s steady confidence filled Barnaby with hope, proving that even small steps can overcome big fears when friends stand together.</p>

<h2 style="{h2_style}">4. A Triumphant Reunion and Starry Night</h2>
<img src="{img_s4}" alt="{alt_s4}" class="alignnone size-medium" style="{right_style}" />
<p style="{p_style}">Soon, the gloomy shadows parted, revealing the cozy, warm glow of Barnaby’s hillside burrow. Mother Bunny ran out with open arms, embracing Barnaby with joyful tears of relief. "Thank you, brave Timmy!" cheered Barnaby. "You helped me cross the dark forest when I was scared!"</p>
<p style="{p_style}">Word of Timmy’s courageous deed quickly spread throughout Whispering Creek. That evening, all the forest animals gathered around the meadow to celebrate Timmy's brave spirit with fresh sweet berries and delicious river mint tea.</p>

<img src="{img_s5}" alt="{alt_s5}" class="alignnone size-medium" style="{left_style}" />
<p style="{p_style}">As a glowing crescent moon rose into the calm night sky, Timmy looked up at the sparkling stars with a quiet smile. He realized that courage had been inside him all along, ready to shine whenever love and friendship called.</p>

<h2 style="{h2_style}">Moral of the Story</h2>
<div class="story-moral" style="background: #fffbeb !important; color: #78350f !important; padding: 22px 25px !important; border-left: 6px solid #f59e0b !important; border-radius: 12px !important; margin: 20px 0 !important; font-size: 17px !important; line-height: 1.8 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;">
    <strong style="color: #b45309 !important; font-size: 18px !important; display: block; margin-bottom: 6px;">💡 Heart of the Lesson:</strong>
    <span style="color: #78350f !important; font-style: italic; font-weight: 500;">True courage is not about being fearless or giant. Real bravery is taking gentle, kind action to help a friend in need, even when you feel nervous inside.</span>
</div>

<h2 style="{h2_style}">What Children Learn</h2>
<div style="background: #eff6ff !important; color: #1e3a8a !important; padding: 22px 25px !important; border-left: 6px solid #3b82f6 !important; border-radius: 12px !important; margin: 20px 0 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;">
    <ul style="margin-bottom: 0 !important; padding-left: 20px !important; color: #1e3a8a !important; font-size: 16px !important; line-height: 1.8 !important;">
        <li style="color: #1e3a8a !important; margin-bottom: 6px !important;"><strong style="color: #172554 !important;">Inner Bravery:</strong> Understanding that feeling scared is natural, but kindness helps us overcome fear.</li>
        <li style="color: #1e3a8a !important; margin-bottom: 6px !important;"><strong style="color: #172554 !important;">Friendship &amp; Support:</strong> The power of standing by friends when they need comfort and guidance.</li>
        <li style="color: #1e3a8a !important; margin-bottom: 0 !important;"><strong style="color: #172554 !important;">Perseverance:</strong> Taking slow, steady steps toward your goal leads to success.</li>
    </ul>
</div>

<h2 style="{h2_style}">Interactive Questions for Kids</h2>
<ol style="line-height: 1.9; font-size: 16px; color: #0f172a !important;">
    <li style="color: #0f172a !important; margin-bottom: 8px !important;">How did Timmy show inner bravery when Barnaby was scared in the dark forest?</li>
    <li style="color: #0f172a !important; margin-bottom: 8px !important;">What is one moment when you felt nervous but decided to be brave anyway?</li>
    <li style="color: #0f172a !important; margin-bottom: 8px !important;">How can you help a friend or classmate when they are feeling worried or lost?</li>
</ol>

<h2 style="{h2_style}">Read Next: More Inspiring Stories for Kids</h2>
<div style="background: #ffffff !important; color: #1e293b !important; border: 1px solid #e2e8f0 !important; padding: 22px 25px !important; border-radius: 12px !important; margin-top: 20px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;">
    <p style="margin-top: 0 !important; font-weight: 700 !important; color: #0f172a !important; font-size: 17px !important;">Continue your bedtime storytime journey with these wonderful moral tales:</p>
    <ul style="margin-bottom: 0 !important; padding-left: 20px !important; color: #334155 !important; line-height: 1.8 !important;">
        <li style="color: #334155 !important; margin-bottom: 8px !important;"><a style="color: #0284c7 !important; font-weight: 700 !important; text-decoration: underline !important;" href="https://vanionline.com/2026/09/03/ella-gentle-elephant-kindness-story/">Ella the Gentle Elephant | Kindness Story for Kids</a> — A sweet tale about how gentleness and compassion bring lasting friendship.</li>
        <li style="color: #334155 !important; margin-bottom: 8px !important;"><a style="color: #0284c7 !important; font-weight: 700 !important; text-decoration: underline !important;" href="https://vanionline.com/2026/08/31/fox-story-for-kids-learned-to-share/">The Little Fox Who Learned to Share</a> — An inspiring story teaching young children the joy of sharing and generosity.</li>
        <li style="color: #334155 !important; margin-bottom: 0 !important;"><a style="color: #0284c7 !important; font-weight: 700 !important; text-decoration: underline !important;" href="https://vanionline.com/2026/08/26/moral-stories-for-kids-lilys-seeds-kindness/">Moral Stories for Kids: Lily’s Amazing Seeds of Kindness</a> — Discover how planting small seeds of caring changes an entire village.</li>
    </ul>
</div>
"""
    return html

def main():
    print("=== STARTING TIMMY TURTLE STORY PUBLISHING ===")
    
    # 1. Convert all images to WebP
    temp_dir = "/Users/raju/.gemini/antigravity-ide/Vani/backend/assets/timmy_illustrations"
    os.makedirs(temp_dir, exist_ok=True)
    
    webp_map = {}
    for item in raw_images:
        out_webp = os.path.join(temp_dir, item["filename"])
        convert_to_webp(item["raw_path"], out_webp)
        webp_map[item["key"]] = {
            "path": out_webp,
            "filename": item["filename"],
            "alt_text": item["alt_text"]
        }
        
    # 2. Login to WordPress
    wp_user, wp_pass = load_credentials()
    if not login_wp(wp_user, wp_pass):
        print("Error: Could not login to WordPress. Aborting.")
        return False
        
    rest_nonce = get_rest_nonce()
    if not rest_nonce:
        print("Error: Could not retrieve REST nonce. Aborting.")
        return False
        
    # 3. Upload all WebP images
    uploaded_images = {}
    for key, data in webp_map.items():
        src_url, attach_id = upload_webp_media(rest_nonce, data["path"], data["filename"], data["alt_text"])
        if src_url and attach_id:
            uploaded_images[key] = {"url": src_url, "id": attach_id}
            
    print(f"Successfully uploaded {len(uploaded_images)}/6 WebP images.")
    if len(uploaded_images) < 6:
        print("Warning: Some images failed to upload.")
        
    # 4. Build post HTML
    post_content = build_post_html(uploaded_images)
    
    # Word count check
    clean_text = re.sub(r'<[^>]+>', ' ', post_content)
    words = [w for w in clean_text.split() if w.strip()]
    word_count = len(words)
    print(f"Article Word Count: {word_count} words (Target: 600-700 words)")
    
    # 5. Publish Post to WordPress
    featured_id = uploaded_images.get("featured", {}).get("id")
    post_payload = {
        'title': story_data["post_title"],
        'slug': story_data["slug"],
        'content': post_content,
        'status': 'publish',
        'categories': story_data["categories"]
    }
    if featured_id:
        post_payload['featured_media'] = featured_id
        
    print("Publishing post on WordPress...")
    req = urllib.request.Request(
        posts_api_url,
        data=json.dumps(post_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
        method='POST'
    )
    
    post_id = None
    post_link = None
    try:
        with opener.open(req, timeout=30) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            post_id = res_data.get("id")
            post_link = res_data.get("link")
            print(f"SUCCESS! Post published with ID: {post_id}")
            print(f"Live URL: {post_link}")
    except Exception as e:
        print(f"Failed to publish post: {e}")
        return False
        
    # 6. Update AIOSEO Meta
    if post_id:
        print("Updating AIOSEO metadata...")
        get_url = f"{base_url}/wp-json/aioseo/v1/post?postId={post_id}"
        get_req = urllib.request.Request(get_url)
        get_req.add_header('X-WP-Nonce', rest_nonce)
        
        current_post_data = None
        try:
            with opener.open(get_req, timeout=15) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                current_post_data = res_json.get("data", {}).get("currentPost", {})
        except Exception as e:
            print(f"Failed to fetch AIOSEO data: {e}")
            
        if current_post_data:
            current_post_data["title"] = story_data["seo_title"]
            current_post_data["description"] = story_data["seo_description"]
            current_post_data["default"] = False
            
            if "keyphrases" not in current_post_data:
                current_post_data["keyphrases"] = {}
            if "focus" not in current_post_data["keyphrases"]:
                current_post_data["keyphrases"]["focus"] = {}
                
            current_post_data["keyphrases"]["focus"]["keyphrase"] = story_data["focus_keyword"]
            
            post_data_payload = json.dumps(current_post_data).encode('utf-8')
            post_req = urllib.request.Request(aioseo_post_url, data=post_data_payload, method='POST')
            post_req.add_header('Content-Type', 'application/json; charset=utf-8')
            post_req.add_header('X-WP-Nonce', rest_nonce)
            
            try:
                with opener.open(post_req, timeout=15) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    if res_json.get("success"):
                        print(f"SUCCESS: AIOSEO focus keyword and metadata saved!")
            except Exception as e:
                print(f"Failed to update AIOSEO: {e}")
                
    # 7. Flush cache
    print("Flushing cache...")
    try:
        opener.open(f"{base_url}/?antigravity_action=flush_cache")
        print("Cache flushed successfully!")
    except Exception as e:
        print(f"Cache flush notice: {e}")
        
    print("\n=== PUBLISHING PROCESS COMPLETED SUCCESSFULLY ===")
    return post_id, post_link

if __name__ == "__main__":
    main()
