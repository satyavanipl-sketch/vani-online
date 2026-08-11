import urllib.request
import urllib.parse
import http.cookiejar
import json
import re
import os
import io
import glob
from PIL import Image

username = "satyavanipl@gmail.com"
password = "Satya@2501"
base_url = "https://vanionline.com"
login_url = f"{base_url}/wp-login.php"
media_api_url = f"{base_url}/wp-json/wp/v2/media"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"

post_id = 923
brain_dir = "/Users/raju/.gemini/antigravity-ide/brain/5edd3dd3-1aae-4fcb-8445-10a663d68512"

# Map of chapter numbers to their descriptive alt text for SEO
image_details = {
    "featured": {
        "prefix": "clockwork_featured",
        "alt": "Leo, master clockmaker Albert, and Mrs. Clara inside the clock tower - kindness bedtime story"
    },
    1: {
        "prefix": "clockwork_ch1",
        "alt": "Leo looking up at the silent stone clock tower in the cobblestone square - kindness bedtime story"
    },
    2: {
        "prefix": "clockwork_ch2",
        "alt": "Leo climbing the dark winding staircase of the tower with a lantern - kindness bedtime story"
    },
    3: {
        "prefix": "clockwork_ch3",
        "alt": "Leo opening a dusty tin box containing black-and-white photos of friends - kindness bedtime story"
    },
    4: {
        "prefix": "clockwork_ch4",
        "alt": "Mrs. Clara the baker looking at the old photo in tears of joy - kindness bedtime story"
    },
    5: {
        "prefix": "clockwork_ch5",
        "alt": "Leo offering Mrs. Clara cookies to Mr. Higgins the lonely toy maker - kindness bedtime story"
    },
    6: {
        "prefix": "clockwork_ch6",
        "alt": "Leo and Mr. Higgins working together on the mechanical bluebird - kindness bedtime story"
    },
    7: {
        "prefix": "clockwork_ch7",
        "alt": "Mr. Higgins presenting the singing mechanical bluebird to Mrs. Clara - kindness bedtime story"
    },
    8: {
        "prefix": "clockwork_ch8",
        "alt": "A tiny brass key glowing with a brilliant golden light - kindness bedtime story"
    },
    9: {
        "prefix": "clockwork_ch9",
        "alt": "Leo inserting the glowing golden key into the giant clock gear - kindness bedtime story"
    },
    10: {
        "prefix": "clockwork_featured", # Reuse featured image for chapter 10
        "alt": "Leo looking out of the high clock tower window proud and happy - kindness bedtime story"
    }
}

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]

def login():
    login_data = urllib.parse.urlencode({
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In',
        'testcookie': '1'
    }).encode('utf-8')
    opener.open(login_url)
    res = opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))
    return "wp-admin" in res.geturl()

def find_image_path(prefix):
    # Find any png files matching prefix in the brain directory
    paths = glob.glob(os.path.join(brain_dir, f"{prefix}_*.png"))
    if paths:
        return paths[0]
    return None

def upload_images(rest_nonce):
    uploaded_mapping = {}
    
    for key, detail in image_details.items():
        prefix = detail["prefix"]
        alt_text = detail["alt"]
        
        # Avoid duplicate upload for reused featured image
        if key == 10 and "featured" in uploaded_mapping:
            print(f"🔄 Reusing featured image URL for Chapter 10...")
            uploaded_mapping[10] = uploaded_mapping["featured"]
            continue
            
        img_path = find_image_path(prefix)
        if not img_path:
            print(f"⚠️ Image not found for prefix: {prefix}")
            continue
            
        print(f"📸 Found image for {key}: {os.path.basename(img_path)}")
        
        # Load, resize, and convert to WebP in memory
        print(f"  Optimizing image to WebP...")
        try:
            im = Image.open(img_path)
            im.thumbnail((800, 800))
            
            webp_io = io.BytesIO()
            im.save(webp_io, format="WEBP", quality=85)
            img_data = webp_io.getvalue()
            filename = f"{prefix}.webp"
        except Exception as img_err:
            print(f"  Image optimization failed: {img_err}. Using original PNG.")
            with open(img_path, 'rb') as f:
                img_data = f.read()
            filename = f"{prefix}.png"
            
        print(f"  Uploading {filename} to WordPress...")
        
        try:
            req = urllib.request.Request(media_api_url, data=img_data, method='POST')
            if filename.endswith(".webp"):
                req.add_header('Content-Type', 'image/webp')
            else:
                req.add_header('Content-Type', 'image/png')
            req.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            req.add_header('X-WP-Nonce', rest_nonce)
            
            with opener.open(req, timeout=30) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                attachment_id = res_json.get("id")
                source_url = res_json.get("source_url")
                
                print(f"  ✅ SUCCESS: Uploaded! ID: {attachment_id}, URL: {source_url}")
                
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
                    print(f"  ✅ Alt text set successfully.")
                    
                uploaded_mapping[key] = {
                    "id": attachment_id,
                    "url": source_url
                }
        except Exception as e:
            print(f"  ❌ Error uploading {key}: {e}")
            
    return uploaded_mapping

def update_post_content(rest_nonce, uploaded_mapping):
    print("\n================ FETCHING CURRENT POST CONTENT ================")
    post_url = f"{base_url}/wp-json/wp/v2/posts/{post_id}"
    req = urllib.request.Request(post_url)
    req.add_header('X-WP-Nonce', rest_nonce)
    
    try:
        with opener.open(req) as res:
            post_data = json.loads(res.read().decode('utf-8'))
            content = post_data["content"]["rendered"]
    except Exception as e:
        print(f"❌ Failed to fetch post content: {e}")
        return False
        
    updated_content = content
    
    # Replace image placeholders
    for ch in range(1, 11):
        if ch in uploaded_mapping:
            new_url = uploaded_mapping[ch]["url"]
            new_alt = image_details[ch]["alt"]
            
            # Matches any src containing ch_{ch}-2.webp
            src_pattern = rf'src="[^"]*ch_{ch}-2\.webp"'
            if re.search(src_pattern, updated_content):
                print(f"🔄 Replacing image src for Chapter {ch}...")
                updated_content = re.sub(src_pattern, f'src="{new_url}"', updated_content)
                
                # Replace alt text
                alt_pattern = rf'alt="[^"]*Chapter {ch} illustration[^"]*"'
                updated_content = re.sub(alt_pattern, f'alt="{new_alt}"', updated_content)
            else:
                print(f"⚠️ Warning: Could not find image placeholder for Chapter {ch} in the post HTML.")

    # Normalize headings: replace H3 with H2 in content if present
    h3_count = len(re.findall(r'<h3[^>]*>(.*?)</h3>', updated_content, re.IGNORECASE))
    if h3_count > 0:
        print(f"🔄 Converting {h3_count} headings from H3 to H2 for correct SEO outline...")
        updated_content = re.sub(r'<h3([^>]*)>(.*?)</h3>', r'<h2\1>\2</h2>', updated_content, flags=re.IGNORECASE)
        
    # Optimize content for focus keyphrase "kindness bedtime story"
    print("🔄 Optimizing content keyword density and links for post 923...")
    
    # 1. Update the first paragraph:
    old_intro_p = 'This is one of the most inspiring bedtime story about kindness and curiosity that teaches'
    new_intro_p = 'This is one of the most inspiring kindness bedtime story that teaches'
    updated_content = updated_content.replace(old_intro_p, new_intro_p)
    
    # 2. Update a subheading to contain focus keyphrase:
    old_subheading = 'The Sound of Friendship'
    new_subheading = 'The Sound of Friendship: A Kindness Bedtime Story'
    updated_content = updated_content.replace(old_subheading, new_subheading)
    
    # 3. Add internal and external links:
    internal_link = '<p>To discover more magical adventures, explore our library of <a href="https://vanionline.com/">bedtime stories for kids</a>.</p>'
    external_link = '<p>Read about the history of mechanical clocks and gears on <a href="https://en.wikipedia.org/wiki/Clock_tower" target="_blank" rel="noopener">Wikipedia</a>.</p>'
    
    if "Moral of the Story" in updated_content:
        updated_content = updated_content.replace(
            '<h2>Moral of the Story</h2>',
            f'{internal_link}\n{external_link}\n<h2>Moral of the Story</h2>'
        )
        
    # 4. Add keyphrase near the end for density:
    old_end_p = 'From that day on, the clock of Oakhaven'
    new_end_p = 'From that day on, the clock of Oakhaven ticked on, reminding everyone of the sweet lesson of this kindness bedtime story. The clock'
    updated_content = updated_content.replace(old_end_p, new_end_p)
    
    # Apply intro box text color visibility style fix (color: #2c3e50 !important)
    style_matches = re.finditer(r'(class="story-intro-box"\s+style=")([^"]*)(")', updated_content)
    for m in style_matches:
        full_match = m.group(0)
        style_body = m.group(2)
        if not re.search(r'(?<!-)\bcolor\s*:', style_body):
            new_style_body = style_body.strip()
            if not new_style_body.endswith(";"):
                new_style_body += ";"
            new_style_body += " color: #2c3e50 !important;"
            new_full_match = f'class="story-intro-box" style="{new_style_body}"'
            updated_content = updated_content.replace(full_match, new_full_match)

    payload = {
        'content': updated_content
    }
    
    if "featured" in uploaded_mapping:
        payload['featured_media'] = uploaded_mapping["featured"]["id"]
        print("🔄 Setting new featured image...")
        
    print("📤 Updating post content on WordPress...")
    update_req = urllib.request.Request(
        post_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
        method='POST'
    )
    
    try:
        with opener.open(update_req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            if res_data.get("id"):
                print("🎉 SUCCESS: Post content updated successfully on WordPress!")
                return True
    except Exception as e:
        print(f"❌ Failed to update post content: {e}")
        
    return False

def update_seo_metadata(rest_nonce):
    print("\n================ UPDATING AIOSEO METADATA ================")
    get_url = f"{base_url}/wp-json/aioseo/v1/post?postId={post_id}"
    get_req = urllib.request.Request(get_url)
    get_req.add_header('X-WP-Nonce', rest_nonce)
    
    current_post_data = None
    try:
        with opener.open(get_req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            current_post_data = res_json.get("data", {}).get("currentPost", {})
    except Exception as e:
        print("❌ Failed to fetch AIOSEO data:", e)
        return False
        
    if not current_post_data:
        print("❌ No AIOSEO data returned.")
        return False
        
    # Set SEO title and description
    current_post_data["title"] = "Leo and the Clockwork Heart of Oakhaven | Kindness Bedtime Story"
    current_post_data["description"] = "Join curious Leo in this heartwarming kindness bedtime story as he repairs the tower clock and heals a broken friendship."
    current_post_data["default"] = False
    
    if "keyphrases" not in current_post_data:
        current_post_data["keyphrases"] = {}
    if "focus" not in current_post_data["keyphrases"]:
        current_post_data["keyphrases"]["focus"] = {}
        
    current_post_data["keyphrases"]["focus"]["keyphrase"] = "kindness bedtime story"
    
    print("📤 Sending request to update AIOSEO data...")
    post_data = json.dumps(current_post_data).encode('utf-8')
    post_req = urllib.request.Request(aioseo_post_url, data=post_data, method='POST')
    post_req.add_header('Content-Type', 'application/json; charset=utf-8')
    post_req.add_header('X-WP-Nonce', rest_nonce)
    
    try:
        with opener.open(post_req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            if res_json.get("success"):
                print("🎉 SUCCESS: AIOSEO settings updated successfully!")
                return True
            else:
                print("❌ Failed to update AIOSEO:", res_json)
    except Exception as e:
        print("❌ Error during AIOSEO update:", e)
        
    return False

def main():
    if not login():
        print("❌ Login failed. Check username/password.")
        return
        
    print("🔓 Login successful!")
    
    # Fetch REST Nonce
    print("🔍 Fetching REST Nonce...")
    rest_nonce = None
    req = urllib.request.Request("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings")
    with opener.open(req) as response:
        html_content = response.read().decode('utf-8', errors='ignore')
        nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
        if nonce_match:
            rest_nonce = nonce_match.group(1)
            print(f"🔑 REST Nonce: {rest_nonce}")
            
    if not rest_nonce:
        print("❌ Could not obtain REST Nonce. Aborting.")
        return
        
    # Upload images
    uploaded_mapping = upload_images(rest_nonce)
    print(f"\n📤 Uploaded {len(uploaded_mapping)} out of {len(image_details)} images.")
    
    # Update post
    if update_post_content(rest_nonce, uploaded_mapping):
        update_seo_metadata(rest_nonce)
        
        # Flush cache
        print("\n⚡ Flushing LiteSpeed cache...")
        try:
            opener.open(f"{base_url}/?antigravity_action=flush_cache")
            print("🎉 SUCCESS: Cache flushed successfully!")
        except Exception as e:
            print("❌ Failed to flush cache:", e)
        print("\n🌟 ALL DONE!")
    else:
        print("❌ Failed to update post content.")

if __name__ == "__main__":
    main()
