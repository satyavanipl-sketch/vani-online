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
post_id = 719
brain_dir = "/Users/raju/.gemini/antigravity-ide/brain/5edd3dd3-1aae-4fcb-8445-10a663d68512"

image_details = {
    "featured": {
        "prefix": "pippin_featured",
        "alt": "Pippin sliding down a snowy hill on his belly - adventure bedtime story"
    },
    "R3.webp": {
        "prefix": "pippin_ch1",
        "alt": "Pippin standing on a sparkling ice shelf at the edge of the southern sea - adventure bedtime story"
    },
    "R4.webp": {
        "prefix": "pippin_ch2",
        "alt": "Baby dolphin Delilah swimming with Pippin near the ocean floor - adventure bedtime story"
    },
    "R5.webp": {
        "prefix": "pippin_ch3",
        "alt": "Friendly old sea turtle Barnaby resting on a sandy patch next to corals - adventure bedtime story"
    },
    "R6-2.webp": {
        "prefix": "pippin_ch4",
        "alt": "Pippin swimming through a thick forest of tall green kelp - adventure bedtime story"
    },
    "R7-2.webp": {
        "prefix": "pippin_ch5",
        "alt": "A group of pink starfish gathered on rocks at the entrance of a deep cave - adventure bedtime story"
    },
    "R8-2.webp": {
        "prefix": "pippin_ch6",
        "alt": "A cheeky red crab holding a glowing blue pearl in its claw on a sandy cave floor - adventure bedtime story"
    },
    "R9-2.webp": {
        "prefix": "pippin_ch7",
        "alt": "Pippin holding a glowing blue pearl and swimming against a fast underwater current - adventure bedtime story"
    },
    "R10.webp": {
        "prefix": "pippin_ch8",
        "alt": "A glowing blue pearl placed on top of a stone pedestal in a colorful coral garden - adventure bedtime story"
    },
    "R3-1.webp": {
        "prefix": "pippin_ch9",
        "alt": "Pippin swimming back home in the ocean under a pink and golden sunset sky - adventure bedtime story"
    },
    "R4-1.webp": {
        "prefix": "pippin_ch10",
        "alt": "Pippin sleeping soundly on a soft snow bed under bright stars - adventure bedtime story"
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

def get_rest_nonce():
    req = urllib.request.Request(f"{base_url}/wp-admin/admin.php?page=googlesitekit-settings")
    with opener.open(req) as response:
        html_content = response.read().decode('utf-8', errors='ignore')
        nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
        if nonce_match:
            return nonce_match.group(1)
    return None

def upload_images(rest_nonce):
    uploaded_mapping = {}
    
    print("\n================ STARTING IMAGE UPLOADS ================")
    for key, info in image_details.items():
        prefix = info["prefix"]
        alt_text = info["alt"]
        
        # Find local image file matching the pattern
        search_pattern = f"{brain_dir}/{prefix}*.png"
        matching_files = glob.glob(search_pattern)
        
        if not matching_files:
            print(f"⚠️ Notice: No matching file found for {prefix} in {brain_dir}. Skipping.")
            continue
            
        local_path = matching_files[0]
        filename = f"{prefix}.webp"
        
        print(f"🔄 Processing: {local_path} -> webp...")
        try:
            # Convert PNG to WebP
            img = Image.open(local_path)
            webp_io = io.BytesIO()
            img.save(webp_io, format="WEBP", quality=85)
            webp_data = webp_io.getvalue()
            
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            body = []
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
            body.append('Content-Type: image/webp'.encode('utf-8'))
            body.append(b'')
            body.append(webp_data)
            body.append(f'--{boundary}--'.encode('utf-8'))
            body.append(b'')
            
            payload_body = b'\r\n'.join(body)
            
            req = urllib.request.Request(media_api_url, data=payload_body, method='POST')
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            req.add_header('X-WP-Nonce', rest_nonce)
            
            print(f"  📤 Uploading {filename}...")
            with opener.open(req, timeout=30) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                attachment_id = res_json.get("id")
                source_url = res_json.get("source_url")
                
                print(f"  ✅ SUCCESS: Uploaded! ID: {attachment_id}, URL: {source_url}")
                
                # Update alt text
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
                    
                uploaded_mapping[key] = {
                    "id": attachment_id,
                    "url": source_url
                }
        except Exception as e:
            print(f"  ❌ Error uploading {key}: {e}")
            
    return uploaded_mapping

def update_post_content(rest_nonce, uploaded_mapping):
    print("\n================ FETCHING CURRENT POST CONTENT ================")
    post_url = f"{base_url}/wp-json/wp/v2/posts/{post_id}?status=publish,future,draft"
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
    
    for key, new_info in uploaded_mapping.items():
        if key == "featured":
            continue
            
        new_url = new_info["url"]
        new_alt = image_details[key]["alt"]
        
        # Match src pattern for the original image key, e.g. R3.webp
        # Escape key for regex
        escaped_key = re.escape(key)
        pattern = rf'src="[^"]*/{escaped_key}"'
        
        if re.search(pattern, updated_content):
            print(f"🔄 Replacing image src for {key}...")
            updated_content = re.sub(pattern, f'src="{new_url}"', updated_content)
            
            # Update alt text inside tag containing new_url
            tag_pattern = rf'(<img[^>]+src="{new_url}"[^>]+alt=")([^"]*)(")'
            updated_content = re.sub(tag_pattern, rf'\g<1>{new_alt}\g<3>', updated_content)
        else:
            print(f"⚠️ Warning: Could not find image placeholder for {key} in the post HTML.")
            
    payload = {
        'content': updated_content
    }
    
    if "featured" in uploaded_mapping:
        payload['featured_media'] = uploaded_mapping["featured"]["id"]
        print("🔄 Setting new featured image...")
        
    print("📤 Updating post content on WordPress...")
    update_req = urllib.request.Request(
        f"{base_url}/wp-json/wp/v2/posts/{post_id}",
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

def main():
    if not login():
        print("❌ Login failed.")
        return
        
    nonce = get_rest_nonce()
    if not nonce:
        print("❌ Nonce not found.")
        return
        
    print(f"🔓 Login successful! Nonce: {nonce}")
    
    uploaded_mapping = upload_images(nonce)
    print(f"\nUploaded {len(uploaded_mapping)} images.")
    
    if len(uploaded_mapping) > 0:
        if update_post_content(nonce, uploaded_mapping):
            # Flush LiteSpeed cache
            print("\n⚡ Flushing LiteSpeed cache...")
            try:
                opener.open(f"{base_url}/?antigravity_action=flush_cache")
                print("🎉 SUCCESS: Cache flushed!")
            except:
                pass
            print("🌟 ALL DONE!")
    else:
        print("❌ No images uploaded.")

if __name__ == "__main__":
    main()
