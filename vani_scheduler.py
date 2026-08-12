import argparse
import datetime
import json
import os
import re
import urllib.request
import urllib.parse
import http.cookiejar
import io
from PIL import Image, ImageDraw, ImageFont
import time
import google.generativeai as genai

# Setup configurations
db_path = "/Users/raju/.gemini/antigravity-ide/Vani/backend/db.json"
draft_path = "/Users/raju/.gemini/antigravity-ide/Vani/backend/story_draft.json"
base_url = "https://vanionline.com"
media_api_url = f"{base_url}/wp-json/wp/v2/media"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"

# Cookie jar and opener for WordPress
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]

def load_db():
    if not os.path.exists(db_path):
        print(f"Error: db.json not found at {db_path}")
        return {}
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

def login_wp(username, password, login_url):
    login_data = urllib.parse.urlencode({
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In',
        'testcookie': '1'
    }).encode('utf-8')
    try:
        opener.open(login_url)
        res = opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))
        return "wp-admin" in res.geturl()
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
                return nonce_match.group(1)
    except Exception as e:
        print(f"Failed to fetch REST nonce: {e}")
    return None

def create_fallback_image(text_label, output_path):
    print(f"  Creating fallback placeholder image for: '{text_label}'")
    colors = [
        (255, 223, 186), # Peach
        (186, 255, 201), # Mint
        (186, 225, 255), # Ice Blue
        (255, 186, 255), # Lavender
        (255, 255, 186)  # Light Yellow
    ]
    bg_color = colors[hash(text_label) % len(colors)]
    
    img = Image.new("RGB", (800, 800), bg_color)
    draw = ImageDraw.Draw(img)
    
    font = ImageFont.load_default()
    
    # Simple label overlay
    draw.text((100, 380), text_label[:50], fill=(50, 50, 50), font=font)
    draw.text((100, 420), "(WebP Illustration Placeholder)", fill=(100, 100, 100), font=font)
    
    img.save(output_path, "WEBP", quality=80)
    return output_path

def generate_illustration(api_key, prompt, output_path, label):
    """Generates an image using Gemini Image API, falls back to Pillow if quota is 0/error."""
    try:
        genai.configure(api_key=api_key)
        model_name = "imagen-3.0-generate-002"
        print(f"  Attempting AI image generation with model {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(data)
                    print(f"  SUCCESS: Generated image saved to {output_path}")
                    return output_path
        
        # If no inline data was found
        print("  AI image generation response did not contain inline data.")
    except Exception as e:
        print(f"  AI image generation failed or quota exceeded: {e}")
        
    # Fallback to local Pillow image creation
    return create_fallback_image(label, output_path)

def upload_webp_media(rest_nonce, img_path, alt_text):
    print(f"  Uploading WebP to WordPress: {os.path.basename(img_path)}...")
    try:
        with open(img_path, 'rb') as f:
            webp_bytes = f.read()
            
        req = urllib.request.Request(media_api_url, data=webp_bytes, method='POST')
        req.add_header('Content-Type', 'image/webp')
        req.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(img_path)}"')
        req.add_header('X-WP-Nonce', rest_nonce)
        
        with opener.open(req, timeout=30) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            attachment_id = res_json.get("id")
            source_url = res_json.get("source_url")
            
            # Update alt text and description
            update_url = f"{media_api_url}/{attachment_id}"
            update_payload = {
                "alt_text": alt_text,
                "description": alt_text
            }
            update_data = json.dumps(update_payload).encode('utf-8')
            update_req = urllib.request.Request(update_url, data=update_data, method='POST')
            update_req.add_header('Content-Type', 'application/json; charset=utf-8')
            update_req.add_header('X-WP-Nonce', rest_nonce)
            
            with opener.open(update_req, timeout=15) as update_resp:
                pass
                
            return source_url, attachment_id
    except Exception as e:
        print(f"  Failed to upload media {img_path}: {e}")
    return None, None

def get_google_access_token(client_id, client_secret, refresh_token):
    if not client_id or not client_secret or not refresh_token:
        print("Blogger OAuth credentials incomplete in db.json. Skipping token refresh.")
        return None
    url = "https://oauth2.googleapis.com/token"
    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            return res_data.get("access_token")
    except Exception as e:
        print(f"Failed to refresh Google Access Token: {e}")
        return None

def publish_to_blogger(blog_id, access_token, title, content):
    if not blog_id or not access_token:
        print("Missing Blogger ID or Access Token. Skipping Blogger publish.")
        return None
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    payload = json.dumps({
        "kind": "blogger#post",
        "title": title,
        "content": content
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            url = res_data.get("url")
            print(f"Successfully posted to Blogger! Link: {url}")
            return url
    except Exception as e:
        print(f"Failed to publish to Blogger: {e}")
        return None

def get_pinterest_board_id(access_token, board_url_or_name):
    if not access_token:
        return None
    url = "https://api.pinterest.com/v5/boards"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            boards = res_data.get("items", [])
            board_slug = board_url_or_name.rstrip("/").split("/")[-1].lower()
            for board in boards:
                name = board.get("name", "").lower()
                board_id = board.get("id")
                if board_slug in name or board_id == board_slug:
                    return board_id
            if boards:
                return boards[0].get("id")
    except Exception as e:
        print(f"Failed to fetch Pinterest boards: {e}")
    return None

def publish_to_pinterest(access_token, board_id, title, description, link_url, image_url):
    if not access_token or not board_id:
        print("Missing Pinterest Access Token or Board ID. Skipping Pinterest Pin.")
        return None
    url = "https://api.pinterest.com/v5/pins"
    payload = json.dumps({
        "link": link_url,
        "title": title,
        "description": description,
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            pin_id = res_data.get("id")
            print(f"Successfully pinned to Pinterest! Pin ID: {pin_id}")
            return pin_id
    except Exception as e:
        print(f"Failed to post to Pinterest: {e}")
        return None

def run_saturday_phase(db):
    print("RUNNING SATURDAY PHASE...")
    
    # 1. Topic selection based on calendar week number (Odd: Animal, Even: People)
    week_num = datetime.date.today().isocalendar()[1]
    is_even = (week_num % 2 == 0)
    topic_type = "people/human-centered story" if is_even else "animal-centered story"
    print(f"Calendar Week: {week_num} (Even: {is_even}) -> Generating {topic_type}")
    
    # 2. Query Gemini to write the story text
    api_key = db["credentials"]["gemini_api_key"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""You are an expert children's book author writing bedtime stories for kids.
Generate a new, highly engaging {topic_type} about virtues like kindness, sharing, bravery, curiosity, or friendship.
The story must have exactly 10 Chapters. Each chapter must have a Title and exactly 4 paragraphs (p1, p2, p3, p4).
Include a "Fun Facts" section with 3 interesting points for kids.
Include an introduction explaining why children will love reading this story.
Output the story strictly in JSON format as specified:
{{
  "title": "Story Title",
  "slug": "url-friendly-slug",
  "keyword": "focus keyword",
  "seo_title": "SEO Title",
  "seo_description": "SEO Description",
  "moral": "Moral of the story text",
  "fun_facts": ["fact 1", "fact 2", "fact 3"],
  "attraction_points": ["point 1", "point 2"],
  "chapters": {{
    "1": {{"title": "Ch 1 Title", "p1": "...", "p2": "...", "p3": "...", "p4": "...", "image_prompt": "Description prompt for AI image generator depicting this chapter's scene"}},
    ...
    "10": {{"title": "Ch 10 Title", "p1": "...", "p2": "...", "p3": "...", "p4": "...", "image_prompt": "Description prompt for AI image generator depicting this chapter's scene"}}
  }},
  "featured_image_prompt": "Description prompt for AI image generator depicting the main cover illustration of the story"
}}"""

    print("Generating story via Gemini...")
    max_retries = 3
    backoff_factor = 2
    story_data = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries} to generate story...")
            response = model.generate_content(prompt)
            text = response.text
            # Clean markdown wrappers if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            story_data = json.loads(text.strip())
            break  # Success
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                sleep_time = backoff_factor ** attempt
                print(f"Waiting {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            else:
                print("All story generation attempts failed.")
                return False
        
    print(f"Story successfully generated: '{story_data.get('title')}'")
    
    # 3. Generate first 5 images (Chapters 1 to 5)
    temp_dir = "/Users/raju/.gemini/antigravity-ide/Vani/backend/assets/temp_illustrations"
    os.makedirs(temp_dir, exist_ok=True)
    
    chapters_data = story_data.get("chapters", {})
    image_paths = {}
    
    for ch in range(1, 6):
        ch_str = str(ch)
        ch_data = chapters_data.get(ch_str, {})
        img_prompt = ch_data.get("image_prompt", f"Illustration for Chapter {ch}")
        output_file = os.path.join(temp_dir, f"ch_{ch}.webp")
        
        print(f"Generating Image {ch}...")
        path = generate_illustration(api_key, img_prompt, output_file, ch_data.get("title", f"Chapter {ch}"))
        image_paths[ch_str] = path
        
    # Save Sunday Draft
    draft = {
        "story": story_data,
        "image_paths": image_paths
    }
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=4)
        
    print("Saturday phase complete. Draft saved locally.")
    return True

def run_sunday_phase(db):
    print("RUNNING SUNDAY PHASE...")
    if not os.path.exists(draft_path):
        print(f"Error: Sunday Draft file not found at {draft_path}. Cannot publish.")
        return False
        
    with open(draft_path, "r", encoding="utf-8") as f:
        draft = json.load(f)
        
    story_data = draft.get("story", {})
    image_paths = draft.get("image_paths", {})
    
    api_key = db["credentials"]["gemini_api_key"]
    
    # 1. Generate remaining 5 images (Chapters 6 to 10) and Featured image
    temp_dir = "/Users/raju/.gemini/antigravity-ide/Vani/backend/assets/temp_illustrations"
    chapters_data = story_data.get("chapters", {})
    
    for ch in range(6, 11):
        ch_str = str(ch)
        ch_data = chapters_data.get(ch_str, {})
        img_prompt = ch_data.get("image_prompt", f"Illustration for Chapter {ch}")
        output_file = os.path.join(temp_dir, f"ch_{ch}.webp")
        
        print(f"Generating Image {ch}...")
        path = generate_illustration(api_key, img_prompt, output_file, ch_data.get("title", f"Chapter {ch}"))
        image_paths[ch_str] = path
        
    # Generate Featured Cover Image
    featured_prompt = story_data.get("featured_image_prompt", f"Cover illustration for {story_data.get('title')}")
    featured_file = os.path.join(temp_dir, "featured.webp")
    print("Generating Featured Image...")
    featured_path = generate_illustration(api_key, featured_prompt, featured_file, story_data.get("title"))
    image_paths["featured"] = featured_path
    
    # 2. Login to WordPress and upload WebPs
    login_url = f"{base_url}/wp-login.php"
    wp_user = db["credentials"].get("wp_username", "satyavanipl@gmail.com")
    wp_pass = db["credentials"].get("wp_password", "Satya@2501")
    
    if not login_wp(wp_user, wp_pass, login_url):
        print("Abort: WordPress login failed.")
        return False
        
    rest_nonce = get_rest_nonce()
    if not rest_nonce:
        print("Abort: REST Nonce could not be retrieved.")
        return False
        
    # Upload all images and map URLs
    uploaded_mapping = {}
    keyword = story_data.get("keyword", "bedtime stories for kids")
    
    for key, path in image_paths.items():
        if key == "featured":
            alt = f"{story_data.get('title')} featured cover - {keyword}"
        else:
            alt = f"{story_data.get('title')} Chapter {key} - {keyword}"
            
        url, attach_id = upload_webp_media(rest_nonce, path, alt)
        if url:
            uploaded_mapping[key] = {"url": url, "id": attach_id}
            
    if len(uploaded_mapping) < 11:
        print(f"Warning: Only {len(uploaded_mapping)}/11 images uploaded successfully.")
        
    # 3. Build Post HTML Content
    left_style = 'float: left !important; margin: 10px 25px 20px 0 !important; border-radius: 60px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'
    right_style = 'float: right !important; margin: 10px 0 20px 25px !important; border-radius: 60px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'
    
    post_title = story_data.get("title") + " 🌸"
    
    # Introduce story with Kid Attractive Points & Fun Facts box
    story_html = f"<p>Deep within a peaceful valley, a brand new adventure began. This is one of the most inspiring <strong>{keyword}</strong> that teaches children valuable lessons while letting them sleep peacefully.</p>"
    
    fun_facts_li = "".join([f"<li><strong>Fact:</strong> {f}</li>" for f in story_data.get("fun_facts", [])])
    attraction_li = "".join([f"<li><strong>Excitement:</strong> {a}</li>" for a in story_data.get("attraction_points", [])])
    
    story_html += f"""
<div class="story-intro-box" style="background-color: #f0f7f4; border-left: 5px solid #2ecc71; padding: 20px; border-radius: 8px; margin: 25px 0;">
    <h3 style="margin-top: 0 !important; color: #27ae60;">🌟 Fun Facts for Curious Kids!</h3>
    <ul>
        {fun_facts_li}
    </ul>
    <h3 style="color: #27ae60; margin-top: 20px !important;">🎒 Why You Will Love Reading This Story!</h3>
    <ul>
        {attraction_li}
    </ul>
</div>
"""

    # Build Chapters HTML
    for ch in range(1, 11):
        ch_str = str(ch)
        ch_data = chapters_data.get(ch_str, {})
        ch_title = ch_data.get("title", f"Chapter {ch}")
        p1 = ch_data.get("p1", "")
        p2 = ch_data.get("p2", "")
        p3 = ch_data.get("p3", "")
        p4 = ch_data.get("p4", "")
        
        # Load image mapping
        img_info = uploaded_mapping.get(ch_str, {"url": "", "id": ""})
        url = img_info["url"]
        style = left_style if ch % 2 == 1 else right_style
        
        alt_desc = f"{story_data.get('title')} Chapter {ch} illustration - {keyword}"
        img_tag = f'<img src="{url}" alt="{alt_desc}" class="alignnone size-medium" style="{style}" />' if url else ""
        
        story_html += f"""
<h2 style="clear: both !important; padding-top: 25px !important;">{ch_title}</h2>
{img_tag}
<p>{p1}</p>
<p>{p2}</p>
<p>{p3}</p>
<p>{p4}</p>
"""
        
    story_html += f"""
<h2 style="clear: both !important; padding-top: 25px !important;">Moral of the Story</h2>
<div class="story-moral" style="background: #fdf6e2; padding: 20px; border-left: 5px solid #ff9f43; border-radius: 8px; margin-top: 15px; font-style: italic;">
    {story_data.get("moral", "Sharing our blessings and being kind to others makes the whole world a much brighter and happier place.")}
</div>"""

    # 4. Publish post on WordPress (Live post)
    featured_img_id = uploaded_mapping.get("featured", {}).get("id", "")
    
    payload = {
        'title': post_title,
        'slug': story_data.get("slug"),
        'content': story_html,
        'status': 'publish',
        'categories': [1, 2, 11]
    }
    if featured_img_id:
        payload['featured_media'] = featured_img_id
        
    print("Publishing Sunday post on WordPress...")
    publish_url_endpoint = f"{base_url}/wp-json/wp/v2/posts"
    req = urllib.request.Request(
        publish_url_endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
        method='POST'
    )
    
    post_link = ""
    post_id = None
    try:
        with opener.open(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            post_id = res_data.get("id")
            post_link = res_data.get("link")
            print(f"SUCCESS: Post published successfully! ID: {post_id}, Link: {post_link}")
    except Exception as e:
        print(f"Failed to publish post content: {e}")
        return False
        
    # 5. Optimize AIOSEO Meta
    if post_id:
        print("Updating AIOSEO meta titles and focus keywords...")
        get_url = f"{base_url}/wp-json/aioseo/v1/post?postId={post_id}"
        get_req = urllib.request.Request(get_url)
        get_req.add_header('X-WP-Nonce', rest_nonce)
        
        current_post_data = None
        try:
            with opener.open(get_req) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                current_post_data = res_json.get("data", {}).get("currentPost", {})
        except Exception as e:
            print(f"Failed to fetch AIOSEO data: {e}")
            
        if current_post_data:
            seo_title = story_data.get("title") + f" (With Pictures)"
            current_post_data["title"] = seo_title
            current_post_data["description"] = story_data.get("seo_description", "")
            current_post_data["default"] = False
            
            if "keyphrases" not in current_post_data:
                current_post_data["keyphrases"] = {}
            if "focus" not in current_post_data["keyphrases"]:
                current_post_data["keyphrases"]["focus"] = {}
                
            current_post_data["keyphrases"]["focus"]["keyphrase"] = keyword
            
            post_data_payload = json.dumps(current_post_data).encode('utf-8')
            post_req = urllib.request.Request(aioseo_post_url, data=post_data_payload, method='POST')
            post_req.add_header('Content-Type', 'application/json; charset=utf-8')
            post_req.add_header('X-WP-Nonce', rest_nonce)
            
            try:
                with opener.open(post_req) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    if res_json.get("success"):
                        print(f"SUCCESS: Updated AIOSEO meta to: '{seo_title}'")
            except Exception as e:
                print(f"Failed to update AIOSEO: {e}")
                
    # 6. Blogger Syndication
    blogger_blog_id = db["credentials"].get("blogger_blog_id", "2765719046810157606")
    g_client_id = db["credentials"].get("google_client_id")
    g_client_secret = db["credentials"].get("google_client_secret")
    g_refresh_token = db["credentials"].get("google_refresh_token")
    
    g_access_token = get_google_access_token(g_client_id, g_client_secret, g_refresh_token)
    if g_access_token:
        print("Syndicating post to Blogger...")
        publish_to_blogger(blogger_blog_id, g_access_token, post_title, story_html)
        
    # 7. Pinterest Syndication
    p_access_token = db["credentials"].get("pinterest_access_token")
    p_board_url = db["credentials"].get("pinterest_board_url", "https://in.pinterest.com/satyavanipl/vani_bedtime-stories/")
    
    if p_access_token and p_board_url:
        print("Syndicating post to Pinterest...")
        board_id = get_pinterest_board_id(p_access_token, p_board_url)
        featured_url = uploaded_mapping.get("featured", {}).get("url", "")
        if board_id and featured_url and post_link:
            publish_to_pinterest(
                p_access_token,
                board_id,
                story_data.get("title"),
                story_data.get("seo_description"),
                post_link,
                featured_url
            )
            
    # Cleanup draft and temporary images
    if os.path.exists(draft_path):
        os.remove(draft_path)
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)
    print("Sunday phase complete. Cleanup done.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vani Online Scheduler")
    parser.add_argument("--phase", required=True, choices=["saturday", "sunday"], help="Scheduler Phase (saturday or sunday)")
    args = parser.parse_args()
    
    db = load_db()
    if not db:
        exit(1)
        
    if args.phase == "saturday":
        success = run_saturday_phase(db)
    else:
        success = run_sunday_phase(db)
        if success:
            # Flush LiteSpeed cache
            print("Flushing cache...")
            try:
                opener.open(f"{base_url}/?antigravity_action=flush_cache")
                print("Cache flushed successfully!")
            except Exception as e:
                print("Failed to flush cache:", e)
                
    print("Vani Scheduler execution finished.")
