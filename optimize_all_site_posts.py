import urllib.request
import urllib.parse
import http.cookiejar
import json
import re
import os
import io
from PIL import Image

username = "satyavanipl@gmail.com"
password = "Satya@2501"
base_url = "https://vanionline.com"
login_url = f"{base_url}/wp-login.php"
media_api_url = f"{base_url}/wp-json/wp/v2/media"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"

post_keywords = {
    715: "bedtime stories for kids",
    718: "moral stories for kids",
    719: "adventure stories for kids",
    720: "bedtime stories for kids",
    796: "bedtime stories for kids"
}

post_descriptions = {
    715: "A lovely bedtime stories for kids adventure about Bella the bunny and Leo the lion cub searching for magic flowers in a glowing forest. Perfect sleep story.",
    718: "An inspiring moral stories for kids adventure about a boy named Oliver whose drawings come to life. Teaches children the value of kindness and sharing.",
    719: "A delightful adventure stories for kids tale about Pippin the penguin who goes on a secret underwater quest to save a lost baby dolphin. Perfect moral story.",
    720: "A heartwarming bedtime stories for kids story about a little squirrel named Sammy who searches for a lost winter seed. Perfect sleep story teaching sharing.",
    796: "A heartwarming bedtime stories for kids story about Benny the Bear who helps a fallen star find its way back to the night sky. Perfect for peaceful sleep."
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

def download_image(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req) as response:
            return response.read()
    except Exception as e:
        print(f"  Failed to download image {url}: {e}")
        return None

def optimize_image_bytes(img_bytes):
    try:
        im = Image.open(io.BytesIO(img_bytes))
        im.thumbnail((800, 800))
        webp_io = io.BytesIO()
        im.save(webp_io, format="WEBP", quality=85)
        return webp_io.getvalue()
    except Exception as e:
        print(f"  Failed to optimize image: {e}")
        return None

def upload_webp_media(rest_nonce, webp_bytes, filename, alt_text):
    try:
        req = urllib.request.Request(media_api_url, data=webp_bytes, method='POST')
        req.add_header('Content-Type', 'image/webp')
        req.add_header('Content-Disposition', f'attachment; filename="{filename}"')
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
        print(f"  Failed to upload media {filename}: {e}")
    return None, None

def run_optimization():
    # Fetch REST Nonce
    print("Fetching REST nonce...")
    rest_nonce = None
    req = urllib.request.Request("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings")
    with opener.open(req) as response:
        html_content = response.read().decode('utf-8', errors='ignore')
        nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
        if nonce_match:
            rest_nonce = nonce_match.group(1)
            print(f"REST Nonce: {rest_nonce}")
        else:
            print("Could not find REST Nonce.")
            return False

    for pid in [715, 718, 719, 720, 796]:
        print(f"\n================ OPTIMIZING POST {pid} ================")
        
        # 1. Fetch post
        post_url = f"{base_url}/wp-json/wp/v2/posts/{pid}"
        post_req = urllib.request.Request(post_url)
        post_req.add_header('X-WP-Nonce', rest_nonce)
        
        try:
            with opener.open(post_req) as response:
                post_data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Failed to fetch post {pid}: {e}")
            continue
            
        title = post_data.get("title", {}).get("rendered", "")
        content = post_data.get("content", {}).get("rendered", "")
        print(f"Post Title: {title}")
        
        # Clean title for keyword mapping
        clean_title = re.sub(r'<[^>]+>', '', title)
        clean_title = clean_title.split(":")[0].strip() # get prefix
        
        keyword = post_keywords.get(pid, "moral stories for kids")
        
        # 2. Find all images in content
        img_tags = re.findall(r'<img[^>]+>', content, re.IGNORECASE)
        print(f"Found {len(img_tags)} images in post.")
        
        updated_content = content
        featured_image_id = post_data.get("featured_media")
        featured_url_new = None
        featured_id_new = None
        
        # We will loop through image tags and optimize any PNG images
        for idx, img in enumerate(img_tags):
            src_match = re.search(r'src="([^"]+)"', img, re.IGNORECASE)
            if not src_match:
                continue
            src_url = src_match.group(1)
            
            # Skip if it is not a PNG from vanionline.com
            if ".png" not in src_url or "vanionline.com" not in src_url:
                print(f"  Skipping image {idx+1}: {src_url} (not local PNG)")
                continue
                
            ch = idx + 1
            # Dynamic descriptive alt text based on post details
            alt_desc = ""
            if pid == 715:
                alt_desc = f"Bella and Leo magic forest hunt - Bedtime stories for kids (Chapter {ch})"
            elif pid == 718:
                alt_desc = f"Oliver drawing with magic paintbrush - Moral stories for kids (Chapter {ch})"
            elif pid == 719:
                alt_desc = f"Pippin the penguin underwater ocean adventure - Adventure stories for kids (Chapter {ch})"
            elif pid == 720:
                alt_desc = f"Sammy the squirrel searching for winter seeds - Bedtime stories for kids (Chapter {ch})"
            elif pid == 796:
                alt_desc = f"Benny the Bear helping the fallen star return to sky - Bedtime stories for kids (Chapter {ch})"
            else:
                alt_desc = f"Moral stories for kids: Chapter {ch} illustration"
                
            print(f"  Optimizing Image {ch}: {src_url}...")
            img_bytes = download_image(src_url)
            if not img_bytes:
                continue
                
            webp_bytes = optimize_image_bytes(img_bytes)
            if not webp_bytes:
                continue
                
            filename = os.path.basename(src_url).replace(".png", ".webp")
            # Avoid duplicate uploads of the same file
            new_url, attach_id = upload_webp_media(rest_nonce, webp_bytes, filename, alt_desc)
            if new_url:
                print(f"    SUCCESS: Converted & Uploaded! New URL: {new_url}")
                # Replace image tag in post
                # We will construct a clean image tag with correct styling and descriptive alt text
                old_style_match = re.search(r'style="([^"]+)"', img, re.IGNORECASE)
                old_style = old_style_match.group(1) if old_style_match else ""
                
                # Check aspect ratio / formatting
                if not old_style:
                    old_style = "max-width: 100% !important; height: auto !important; border-radius: 8px !important;"
                    
                new_img_tag = f'<img src="{new_url}" alt="{alt_desc}" class="alignnone size-medium" style="{old_style}" />'
                updated_content = updated_content.replace(img, new_img_tag)
                
                # Check if this image was the featured image
                # In WP, if filename matches the featured image filename, we can update it
                # Usually we can also upload a separate WebP for featured if needed
                if idx == 0:
                    featured_url_new = new_url
                    featured_id_new = attach_id
            
        # 3. Optimize heading outlines: Replace H3 with H2
        # First check if there are H3s
        h3_count = len(re.findall(r'<h3[^>]*>(.*?)</h3>', updated_content, re.IGNORECASE))
        if h3_count > 0:
            print(f"  Converting {h3_count} headings from H3 to H2 for correct SEO outline...")
            updated_content = re.sub(r'<h3([^>]*)>(.*?)</h3>', r'<h2\1>\2</h2>', updated_content, flags=re.IGNORECASE)
            
        # Format the moral section to have H2 header if not present
        if "Moral of the Story" in updated_content and "<h2>Moral of the Story" not in updated_content:
            print("  Adding proper H2 heading for Moral of the Story...")
            # If there is a moral div, prepend H2
            updated_content = re.sub(
                r'(<div class="story-moral"[^>]*>)\s*<strong>Moral of the Story:</strong>', 
                r'<h2>Moral of the Story</h2>\1', 
                updated_content, 
                flags=re.IGNORECASE
            )
            # fallback for simple strong moral
            if "<h2>Moral of the Story" not in updated_content:
                updated_content = re.sub(
                    r'<strong>Moral of the Story:</strong>', 
                    r'<h2>Moral of the Story</h2><strong>Moral of the Story:</strong>', 
                    updated_content, 
                    flags=re.IGNORECASE
                )
                
        # 4. Save updated content back to WordPress
        payload = {
            'content': updated_content
        }
        if featured_id_new:
            payload['featured_media'] = featured_id_new
            
        print("  Updating post content on WordPress...")
        update_req = urllib.request.Request(
            f"{base_url}/wp-json/wp/v2/posts/{pid}",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
            method='POST'
        )
        try:
            with opener.open(update_req) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                if res_data.get("id"):
                    print("  SUCCESS: Post content updated successfully!")
        except Exception as e:
            print(f"  Failed to update post content: {e}")
            
        # 5. Optimize AIOSEO meta
        print("  Updating AIOSEO meta titles and focus keywords...")
        get_url = f"{base_url}/wp-json/aioseo/v1/post?postId={pid}"
        get_req = urllib.request.Request(get_url)
        get_req.add_header('X-WP-Nonce', rest_nonce)
        
        current_post_data = None
        try:
            with opener.open(get_req) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                current_post_data = res_json.get("data", {}).get("currentPost", {})
        except Exception as e:
            print(f"  Failed to fetch AIOSEO data: {e}")
            continue
            
        if current_post_data:
            # CTR optimized title containing (With Pictures)
            seo_title = clean_title + f" | {keyword.title()} (With Pictures)"
            # Ensure it fits within 60 chars
            if len(seo_title) > 60:
                seo_title = clean_title + " (With Pictures)"
            if len(seo_title) > 60:
                seo_title = clean_title[:45] + "... (With Pictures)"
                
            current_post_data["title"] = seo_title
            current_post_data["description"] = post_descriptions.get(pid, current_post_data.get("description", ""))
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
                        print(f"  SUCCESS: Updated AIOSEO meta to: '{seo_title}'")
            except Exception as e:
                print(f"  Failed to update AIOSEO: {e}")

    return True

if __name__ == "__main__":
    if login():
        print("Login successful!")
        if run_optimization():
            # Flush cache
            print("\nFlushing LiteSpeed cache...")
            try:
                opener.open(f"{base_url}/?antigravity_action=flush_cache")
                print("SUCCESS: Cache flushed successfully!")
            except Exception as e:
                print("Failed to flush cache:", e)
            print("\nALL POSTS ARE FULLY OPTIMIZED!")
    else:
        print("Login failed.")
