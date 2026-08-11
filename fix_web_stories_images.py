import urllib.request
import urllib.parse
import http.cookiejar
import json
import re
import uuid

username = "satyavanipl@gmail.com"
password = "Satya@2501"
base_url = "https://vanionline.com"
login_url = f"{base_url}/wp-login.php"
posts_api_url = f"{base_url}/wp-json/wp/v2/posts"
web_stories_api_url = f"{base_url}/wp-json/web-stories/v1/web-story"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]

# Mapping of Web Stories to their source posts
stories_to_posts = {
    968: 802,  # Lily
    969: 907,  # Bridge of Books
    970: 923,  # Clockwork Heart
    975: 718,  # Oliver
    976: 719,  # Pippin
    977: 796   # Magic Forest
}

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

def fetch_media_details(rest_nonce, media_id):
    if not media_id:
        return None
    url = f"{base_url}/wp-json/wp/v2/media/{media_id}"
    req = urllib.request.Request(url)
    req.add_header('X-WP-Nonce', rest_nonce)
    try:
        with opener.open(req) as res:
            return json.loads(res.read().decode('utf-8'))
    except:
        return None

# Cache for media details to avoid querying the same image multiple times
media_cache = {}

def get_media_resource_details(rest_nonce, img_url):
    if img_url in media_cache:
        return media_cache[img_url]
        
    filename = img_url.split("/")[-1].split(".")[0]
    filename = re.sub(r'-\d+x\d+$', '', filename)
    
    print(f"    Searching Media Library for: {filename}...")
    search_url = f"{base_url}/wp-json/wp/v2/media?search={urllib.parse.quote(filename)}"
    req = urllib.request.Request(search_url)
    req.add_header('X-WP-Nonce', rest_nonce)
    
    try:
        with opener.open(req) as res:
            media_list = json.loads(res.read().decode('utf-8'))
            if media_list:
                match = media_list[0]
                
                # Fetch full sizes dictionary
                sizes = {}
                wp_sizes = match.get("media_details", {}).get("sizes", {})
                for sz_name, sz_info in wp_sizes.items():
                    sizes[sz_name] = {
                        "file": sz_info.get("file"),
                        "width": sz_info.get("width"),
                        "height": sz_info.get("height"),
                        "mimeType": sz_info.get("mime_type", "image/webp"),
                        "sourceUrl": sz_info.get("source_url")
                    }
                    
                resource = {
                    "type": "image",
                    "mimeType": match.get("mime_type", "image/webp"),
                    "width": match.get("media_details", {}).get("width", 800),
                    "height": match.get("media_details", {}).get("height", 800),
                    "src": match.get("source_url"),
                    "id": match.get("id"),
                    "alt": match.get("alt_text", ""),
                    "local": False,
                    "provider": "local",
                    "isExternal": False,
                    "isPlaceholder": False,
                    "needsProxy": False,
                    "baseColor": "#131516",
                    "blurHash": "",
                    "sizes": sizes
                }
                media_cache[img_url] = resource
                return resource
    except Exception as e:
        print(f"    Error searching media for {filename}: {e}")
        
    fallback = {
        "type": "image",
        "mimeType": "image/webp",
        "width": 800,
        "height": 800,
        "src": img_url,
        "id": 0,
        "alt": "",
        "local": False,
        "provider": "local",
        "isExternal": False,
        "isPlaceholder": False,
        "needsProxy": False,
        "baseColor": "#131516",
        "blurHash": "",
        "sizes": {}
    }
    media_cache[img_url] = fallback
    return fallback

def parse_post_to_slides(post_title, post_content, featured_image_url):
    slides = []
    
    # Cover Slide
    slides.append({
        "title": post_title,
        "text": "A beautiful bedtime story for kids",
        "image_url": featured_image_url
    })
    
    parts = re.split(r'(<h2[^>]*>.*?</h2>)', post_content)
    
    for i in range(1, len(parts), 2):
        header_html = parts[i]
        body_html = parts[i+1] if i+1 < len(parts) else ""
        
        header_text = re.sub(r'<[^>]+>', '', header_html).strip()
        if any(keyword in header_text.lower() for keyword in ["moral", "fun facts", "love reading", "about the author", "author biography"]):
            continue
            
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body_html)
        image_url = img_match.group(1) if img_match else featured_image_url
        
        body_text = re.sub(r'<[^>]+>', ' ', body_html)
        body_text = re.sub(r'\s+', ' ', body_text).strip()
        
        if len(body_text) > 180:
            body_text = body_text[:177] + "..."
            
        if header_text and body_text:
            slides.append({
                "title": header_text,
                "text": body_text,
                "image_url": image_url
            })
            
    return slides

def build_web_story_payload(rest_nonce, post_title, slides, featured_media_id, featured_image_url, post_status, post_date, post_date_gmt):
    # Base layout uses a solid dark background color for the page
    html_prefix = '<html amp="" lang="en"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1"/><script async="" src="https://cdn.ampproject.org/v0.js"></script><script async="" src="https://cdn.ampproject.org/v0/amp-story-1.0.js" custom-element="amp-story"></script><link href="https://fonts.googleapis.com/css2?display=swap&amp;family=Roboto%3Awght%40400%3B700" rel="stylesheet"/><style amp-boilerplate="">body{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}@-webkit-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-moz-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-ms-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-o-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}</style><noscript><style amp-boilerplate="">body{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}</style></noscript><style amp-custom="">h1, h2, h3 { font-weight: normal; } amp-story-page { background-color: #131516; } amp-story-grid-layer { overflow: visible; }</style></head><body><amp-story standalone="" publisher="Satyavani" publisher-logo-src="" title="' + post_title + '" poster-portrait-src="' + featured_image_url + '">'
    
    html_suffix = '</amp-story></body></html>'
    
    html_pages_body = ""
    json_pages = []
    
    for idx, slide in enumerate(slides):
        page_uuid = str(uuid.uuid4())
        img_id = str(uuid.uuid4())
        card_id = str(uuid.uuid4())
        bg_shape_id = str(uuid.uuid4())
        
        title_text = slide["title"]
        desc_text = slide["text"]
        img_url = slide["image_url"]
        
        # Fetch full media resource details from WordPress API
        resource = get_media_resource_details(rest_nonce, img_url)
        
        # Compile HTML representation: 
        # Image is rendered at the top, vertical grid layer naturally flows text below it without overlapping.
        slide_html = f'<amp-story-page id="{page_uuid}" auto-advance-after="7s"><amp-story-grid-layer template="fill"><div style="background-color: #131516; width: 100%; height: 100%;"></div></amp-story-grid-layer><amp-story-grid-layer template="vertical" style="padding: 0;"><amp-img src="{img_url}" width="412" height="412" layout="responsive" alt="{title_text}"></amp-img><div style="padding: 24px 32px; text-align: center; color: #ffffff;"><h2 style="margin: 10px 0 12px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 20px; font-weight: bold; color: #ffffff; line-height: 1.2;">{title_text}</h2><p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; line-height: 1.4; color: #e5e5e5;">{desc_text}</p></div></amp-story-grid-layer></amp-story-page>'
        
        html_pages_body += slide_html
        
        # Compile JSON page model
        json_page = {
            "id": page_uuid,
            "backgroundColor": {
                "color": { "r": 19, "g": 21, "b": 22 }
            },
            # Default background shape is stored at page-level in defaultBackgroundElement
            "defaultBackgroundElement": {
                "opacity": 100,
                "flip": {
                    "vertical": False,
                    "horizontal": False
                },
                "rotationAngle": 0,
                "lockAspectRatio": True,
                "backgroundColor": {
                    "color": {
                        "r": 19,
                        "g": 21,
                        "b": 22
                    }
                },
                "x": 1,
                "y": 1,
                "width": 1,
                "height": 1,
                "mask": {
                    "type": "rectangle"
                },
                "isBackground": True,
                "isDefaultBackground": True,
                "type": "shape",
                "id": bg_shape_id
            },
            "animations": [],
            "elements": [
                # Top Half Image (regular element: isBackground = False, height = 412, y = 0)
                {
                    "opacity": 100,
                    "flip": {
                        "vertical": False,
                        "horizontal": False
                    },
                    "rotationAngle": 0,
                    "lockAspectRatio": False,
                    "scale": 100,
                    "focalX": 50,
                    "focalY": 50,
                    "type": "image",
                    "x": 0,
                    "y": 0,
                    "width": 412,
                    "height": 412,
                    "mask": {
                        "type": "rectangle",
                        "showInLibrary": True,
                        "name": "Rectangle",
                        "path": "M 0,0 1,0 1,1 0,1 0,0 Z",
                        "ratio": 1,
                        "supportsBorder": True
                    },
                    "resource": resource,
                    "id": img_id
                },
                # Bottom Half Text Card (regular element: backgroundTextMode = NONE, y = 430)
                {
                    "opacity": 100,
                    "flip": {
                        "vertical": False,
                        "horizontal": False
                    },
                    "rotationAngle": 0,
                    "lockAspectRatio": True,
                    "backgroundTextMode": "NONE",
                    "font": {
                        "family": "Roboto"
                    },
                    "fontSize": 15,
                    "lineHeight": 1.4,
                    "textAlign": "center",
                    "padding": {
                        "locked": True,
                        "hasHiddenPadding": False,
                        "horizontal": 0,
                        "vertical": 0
                    },
                    "backgroundColor": {
                        "color": { "r": 19, "g": 21, "b": 22 }
                    },
                    "content": f'<span style="color: #ffffff; font-weight: 700; font-size: 20px; line-height: 1.2;">{title_text}</span><br/><br/><span style="color: #e5e5e5; font-size: 15px; line-height: 1.4;">{desc_text}</span>',
                    "x": 30,
                    "y": 440,
                    "width": 352,
                    "height": 240,
                    "borderRadius": {
                        "locked": True,
                        "topLeft": 0,
                        "topRight": 0,
                        "bottomRight": 0,
                        "bottomLeft": 0
                    },
                    "type": "text",
                    "id": card_id
                }
            ]
        }
        json_pages.append(json_page)
        
    full_html = html_prefix + html_pages_body + html_suffix
    full_html = re.sub(r'[\r\n]+', ' ', full_html)
    full_html = re.sub(r'\s+', ' ', full_html)
    
    # Registered Roboto font configuration and metrics dictionary
    roboto_font = {
        "family": "Roboto",
        "fallbacks": ["sans-serif"],
        "weights": [100, 200, 300, 400, 500, 600, 700, 800, 900],
        "styles": ["regular", "italic"],
        "variants": [[0, 100], [0, 200], [0, 300], [0, 400], [0, 500], [0, 600], [0, 700], [0, 800], [0, 900], [1, 100], [1, 200], [1, 300], [1, 400], [1, 500], [1, 600], [1, 700], [1, 800], [1, 900]],
        "service": "fonts.google.com",
        "metrics": {
            "upm": 2048, "asc": 1900, "des": -500, "tAsc": 1536, "tDes": -512, "tLGap": 102,
            "wAsc": 1946, "wDes": 512, "xH": 1082, "capH": 1456, "yMin": -555, "yMax": 2163,
            "hAsc": 1900, "hDes": -500, "lGap": 0
        }
    }
    
    payload = {
        "title": post_title,
        "status": post_status,
        "content": full_html,
        "story_data": {
            "version": 47,  # Explicitly targeting schema v47
            "pages": json_pages,
            "fonts": {
                "Roboto": roboto_font
            },
            "autoAdvance": True,
            "defaultPageDuration": 7,
            "currentStoryStyles": {
                "colors": []
            }
        },
        "featured_media": featured_media_id
    }
    if post_date:
        payload["date"] = post_date
    if post_date_gmt:
        payload["date_gmt"] = post_date_gmt
        
    return payload

def main():
    if not login():
        print("❌ Login failed.")
        return
        
    nonce = get_rest_nonce()
    if not nonce:
        print("❌ Nonce not found.")
        return
        
    print(f"🔓 Login successful! Nonce: {nonce}")
    
    # Process all 6 Web Stories
    for story_id, post_id in stories_to_posts.items():
        print(f"\n================ PATCHING WEB STORY ID {story_id} (Post ID {post_id}) ================")
        
        url = f"{posts_api_url}/{post_id}?status=publish,future,draft"
        req = urllib.request.Request(url)
        req.add_header('X-WP-Nonce', nonce)
        try:
            with opener.open(req) as res:
                post = json.loads(res.read().decode('utf-8'))
                title = post["title"]["rendered"]
                content = post["content"]["rendered"]
                feat_media_id = post.get("featured_media")
                status = post.get("status", "publish")
                date = post.get("date")
                date_gmt = post.get("date_gmt")
        except Exception as e:
            print(f"❌ Failed to fetch post {post_id}: {e}")
            continue
            
        feat_img_url = ""
        if feat_media_id:
            media = fetch_media_details(nonce, feat_media_id)
            if media:
                feat_img_url = media.get("source_url", "")
                
        print(f"  Title: {title}")
        print(f"  Featured Image: {feat_img_url}")
        
        slides = parse_post_to_slides(title, content, feat_img_url)
        print(f"  Generated {len(slides)} slides.")
        
        payload = build_web_story_payload(nonce, title, slides, feat_media_id, feat_img_url, status, date, date_gmt)
        
        target_url = f"{web_stories_api_url}/{story_id}"
        data = json.dumps(payload).encode('utf-8')
        post_req = urllib.request.Request(target_url, data=data, method='POST')
        post_req.add_header('Content-Type', 'application/json; charset=utf-8')
        post_req.add_header('X-WP-Nonce', nonce)
        
        try:
            with opener.open(post_req) as res:
                res_json = json.loads(res.read().decode('utf-8'))
                print(f"  🎉 SUCCESS: Story {story_id} updated. Link: {res_json.get('link')}")
        except Exception as e:
            print(f"  ❌ Failed to update story {story_id}: {e}")
            
    # Flush Cache
    print("\n⚡ Flushing LiteSpeed cache...")
    try:
        opener.open(f"{base_url}/?antigravity_action=flush_cache")
        print("🎉 SUCCESS: Cache flushed!")
    except:
        pass

if __name__ == "__main__":
    main()
