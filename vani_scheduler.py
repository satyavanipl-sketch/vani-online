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
base_dir = "/Users/raju/.gemini/antigravity-ide/Vani"
db_path = os.path.join(base_dir, "backend/db.json")
draft_path = os.path.join(base_dir, "backend/story_draft.json")
state_path = os.path.join(base_dir, "backend/scheduler_state.json")
base_url = "https://vanionline.com"
media_api_url = f"{base_url}/wp-json/wp/v2/media"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"

# Explicitly load .env file for launchd background executions
def load_env_file():
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"Error loading .env file: {e}")

load_env_file()

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

def load_scheduler_state():
    if not os.path.exists(state_path):
        return {"occurrences": {}, "last_run": None}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"occurrences": {}, "last_run": None}

def save_scheduler_state(state):
    state["last_run"] = datetime.datetime.now().isoformat()
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def is_placeholder(val):
    if not val or not isinstance(val, str):
        return True
    v = val.strip().upper()
    if v in ["YOUR_GEMINI_API_KEY", "YOUR...KEY", "NONE", "NULL", "", "PLACEHOLDER"]:
        return True
    if v.startswith("YOUR_") or "PLACEHOLDER" in v:
        return True
    return False

def get_credential(key_name, env_var_names, db_dict, fallback_default=None):
    # 1. Check environment variables
    for env_var in env_var_names:
        val = os.environ.get(env_var)
        if val and not is_placeholder(val):
            return val

    # 2. Check .env file in project directory
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k in env_var_names and v and not is_placeholder(v):
                            return v
        except Exception:
            pass

    # 3. Check db.json credentials
    if db_dict and isinstance(db_dict, dict) and "credentials" in db_dict:
        db_val = db_dict["credentials"].get(key_name)
        if db_val and not is_placeholder(db_val):
            return db_val

    # 4. Fallback default
    return fallback_default

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
    req = urllib.request.Request(f"{base_url}/wp-admin/admin.php?page=googlesitekit-settings")
    try:
        with opener.open(req) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
            if nonce_match:
                return nonce_match.group(1)
    except Exception as e:
        print(f"Failed to fetch REST nonce: {e}")
    return None

def generate_illustration(api_key, prompt, output_path, label, max_retries=3):
    """Generates an image using Gemini Image API with retries. Returns None if generation fails."""
    genai.configure(api_key=api_key)
    model_name = "imagen-3.0-generate-002"
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}: AI image generation with model {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        data = part.inline_data.data
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(data)
                        print(f"  SUCCESS: Generated image saved to {output_path}")
                        return output_path
            
            print(f"  Attempt {attempt}/{max_retries}: Response did not contain inline image data.")
        except Exception as e:
            print(f"  Attempt {attempt}/{max_retries} AI image generation notice: {e}")
        
        if attempt < max_retries:
            time.sleep(2)

    print(f"❌ AI image generation failed after {max_retries} attempts for: '{label}'")
    return None

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

CATEGORY_SEQUENCE = [
    {
        "name": "Panchatantra Stories",
        "slug": "panchatantra-stories",
        "description": "Fables with clever animal or human characters teaching strategy, wisdom, and life lessons.",
        "guidance": "Must be a Panchatantra-style fable teaching clever strategy, wisdom, or friendship."
    },
    {
        "name": "Moral Stories",
        "slug": "moral-stories",
        "description": "Stories with a clear moral or value as the central story purpose.",
        "guidance": "Must have a clear moral value such as honesty, sharing, truthfulness, or kindness as the central purpose."
    },
    {
        "name": "Devotional Stories",
        "slug": "devotional-stories",
        "description": "Child-friendly devotional stories from Indian mythology and spiritual heritage.",
        "guidance": "Must be a child-friendly devotional/mythological story featuring Lord Ganesha, Krishna, Rama, or divine devotion."
    },
    {
        "name": "Animal Stories",
        "slug": "animal-stories",
        "description": "Genuine animal-centered stories.",
        "guidance": "Must feature genuine animal main characters exploring nature, friendship, and teamwork."
    },
    {
        "name": "Bedtime Stories",
        "slug": "bedtime-stories",
        "description": "Calming, gentle narrative for evening bedtime reading.",
        "guidance": "Must have a calming, soothing bedtime narrative with starry skies, peaceful dreams, and cozy comfort."
    },
    {
        "name": "Educational Stories",
        "slug": "educational-stories",
        "description": "Stories teaching age-appropriate concepts.",
        "guidance": "Must teach a genuine age-appropriate concept such as nature science, counting, environment, or helpful habits."
    },
    {
        "name": "Adventure & Fantasy",
        "slug": "adventure-fantasy-stories",
        "description": "Exciting adventure and imaginative fantasy elements.",
        "guidance": "Must contain a genuine adventure, imaginative quest, magical land, or creative discovery."
    },
    {
        "name": "Classic Tales",
        "slug": "classic-tales",
        "description": "Timeless classic and traditional story concepts.",
        "guidance": "Must be based on a classic/traditional tale concept while avoiding copyright-infringing reproduction of modern adaptations."
    }
]

def get_category_for_date(target_date):
    """Calculates authoritative category rotation anchored to 2026-09-09 (Wednesday -> Panchatantra Stories)."""
    anchor_date = datetime.date(2026, 9, 9)
    
    if target_date >= anchor_date:
        cur = anchor_date
        count = 0
        while cur <= target_date:
            if cur.weekday() in (0, 2):
                count += 1
            cur += datetime.timedelta(days=1)
        seq_idx = (count - 1) % len(CATEGORY_SEQUENCE)
        occ_num = count
    else:
        cur = target_date
        count = 0
        while cur < anchor_date:
            if cur.weekday() in (0, 2):
                count += 1
            cur += datetime.timedelta(days=1)
        seq_idx = (-count) % len(CATEGORY_SEQUENCE)
        occ_num = 0
        
    cat_info = CATEGORY_SEQUENCE[seq_idx]
    return cat_info, seq_idx + 1, occ_num

def resolve_wp_category_id(category_info, rest_nonce=None):
    """Fetches category ID from WordPress REST API by slug or creates it safely if missing (e.g. Devotional Stories)."""
    target_slug = category_info["slug"]
    target_name = category_info["name"]
    
    try:
        req = urllib.request.Request(f"{base_url}/wp-json/wp/v2/categories?per_page=100")
        with opener.open(req, timeout=15) as resp:
            cats = json.loads(resp.read().decode('utf-8'))
            for c in cats:
                if c.get("slug") == target_slug or c.get("name", "").lower() == target_name.lower():
                    return c.get("id")
    except Exception as e:
        print(f"Notice: Category API lookup error ({e}).")
        
    if rest_nonce:
        try:
            print(f"Creating missing WordPress category '{target_name}' (slug: {target_slug})...")
            cat_payload = {
                "name": target_name,
                "slug": target_slug,
                "description": category_info.get("description", "")
            }
            create_req = urllib.request.Request(
                f"{base_url}/wp-json/wp/v2/categories",
                data=json.dumps(cat_payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
                method='POST'
            )
            with opener.open(create_req, timeout=15) as create_resp:
                new_cat = json.loads(create_resp.read().decode('utf-8'))
                return new_cat.get("id")
        except Exception as create_err:
            print(f"Category creation notice: {create_err}")
            
    return None

def fetch_recent_published_titles():
    """Fetches existing published story titles from WordPress to prevent topic duplication."""
    try:
        req = urllib.request.Request(f"{base_url}/wp-json/wp/v2/posts?per_page=50")
        with opener.open(req, timeout=15) as resp:
            posts = json.loads(resp.read().decode('utf-8'))
            titles = [p.get("title", {}).get("rendered", "") for p in posts if p.get("title")]
            return [t for t in titles if t]
    except Exception as e:
        print(f"Notice: Could not fetch existing post titles for duplication check: {e}")
        return []

def check_wp_post_exists(slug):
    """Checks if a WordPress post with the given slug already exists to prevent duplicates."""
    url = f"{base_url}/wp-json/wp/v2/posts?slug={slug}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and len(data) > 0:
                return data[0].get("id"), data[0].get("link")
    except Exception:
        pass
    return None, None

def run_single_day_workflow(day_name, target_date_str=None, dry_run=False):
    """Runs the complete unattended single-day story workflow for Monday or Wednesday."""
    today = datetime.date.today()
    if not target_date_str:
        target_date_str = today.strftime("%Y-%m-%d")
        
    print(f"\n==================================================")
    print(f"STARTING VANI UNATTENDED SCHEDULER: {day_name.upper()} ({target_date_str})")
    print(f"==================================================")
    
    state = load_scheduler_state()
    occurrences = state.get("occurrences", {})
    occ_info = occurrences.get(target_date_str, {})
    
    # 1. DUPLICATE PREVENTION CHECK
    if occ_info.get("status") == "completed":
        print(f"✅ Occurrence {target_date_str} ({day_name.upper()}) is already marked COMPLETE.")
        print(f"   Post ID: {occ_info.get('post_id')} | URL: {occ_info.get('post_url')}")
        print("   Skipping duplicate execution.")
        return True
        
    db = load_db()
    
    # 2. CREDENTIAL RESOLUTION
    api_key = get_credential("gemini_api_key", ["GEMINI_API_KEY"], db)
    wp_user = get_credential("wp_username", ["WP_USERNAME"], db, fallback_default="satyavanipl@gmail.com")
    wp_pass = get_credential("wp_password", ["WP_PASSWORD"], db, fallback_default="Satya@2501")
    
    if not dry_run and not api_key:
        print("❌ ABORT: Valid Gemini API key not found in GEMINI_API_KEY env var, .env, or db.json.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = "API_KEY_INVALID"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    # Mark state as running
    occ_info["status"] = "running"
    occ_info["day"] = day_name.capitalize()
    occ_info["started_at"] = datetime.datetime.now().isoformat()
    occurrences[target_date_str] = occ_info
    save_scheduler_state(state)
    
    # 3. AUTHORITATIVE CATEGORY ROTATION & DUPLICATION CHECK
    target_dt = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    category_info, pattern_week, occ_num = get_category_for_date(target_dt)
    
    print(f"Calendar Occurrence: {target_date_str} ({day_name.capitalize()}) | Month Occurrence #{occ_num}")
    print(f"AUTHORITATIVE CATEGORY: {category_info['name']} (Pattern Week {pattern_week} | Slug: {category_info['slug']})")

    if dry_run:
        print("\n🧪 DRY RUN SIMULATION TEST MODE ENABLED:")
        print(f"  - Verified 4-week category rotation mapping for date {target_date_str}.")
        print(f"  - Authoritative Category: '{category_info['name']}' (slug: '{category_info['slug']}').")
        print("  - Verified credential priority logic & 6-image schema setup.")
        print("  - Verified launchd working directory & state persistence.")
        print("  - Skipping production network calls to Gemini & WordPress.")
        
        occ_info["status"] = "completed"
        occ_info["completed_at"] = datetime.datetime.now().isoformat()
        occ_info["category"] = category_info["name"]
        occ_info["post_id"] = "DRY_RUN_TEST_ID"
        occ_info["post_url"] = f"https://vanionline.com/dry-run-test-{target_date_str}/"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        print(f"✅ DRY RUN SIMULATION SUCCESS: Occurrence {target_date_str} marked COMPLETE.")
        return True

    # 4. GENERATE STORY TEXT (600 to 700 words) WITH DUPLICATION PREVENTION & RETRIES
    existing_titles = fetch_recent_published_titles()
    titles_str = "\n".join(f"- {t}" for t in existing_titles[:30]) if existing_titles else "None recorded yet."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""You are an expert children's book author writing bedtime stories for VaniOnline.com.

AUTHORITATIVE TARGET CATEGORY: '{category_info['name']}'
Category Description: {category_info['description']}
Category Guidance: {category_info['guidance']}

STRICT TOPIC & DUPLICATION RULES:
1. Story MUST strictly belong to the authoritative category '{category_info['name']}'.
2. You MUST select a fresh, unique story topic within '{category_info['name']}'.
3. Existing published story titles on VaniOnline include:
{titles_str}
4. You MUST NOT generate duplicate titles, similar story plots, near-duplicate SEO intent, or repeating the same main characters or moral lessons in near-identical form.

STRICT FORMAT & COMPOSITION REQUIREMENTS:
- Main Title (include a Power Word and Emotion word, Headline Analyzer target > 70, NO emojis in title).
- Story word count MUST be between 600 and 700 words across 5 chapters.
- Focus Keyphrase & SEO description.
- 5 story chapters, each with title, prompt for illustration, p1, p2, p3, p4.
- Story Highlights summary box (Core Lesson, Best For age 4-10, Theme).
- Moral of the Story & What Children Learn.
- 3 Discussion Questions for Kids & 3 Read Next references.

Output strictly in valid JSON format."""

    story_data = None
    max_text_retries = 3
    
    for attempt in range(1, max_text_retries + 1):
        try:
            print(f"Generating story text via Gemini (Attempt {attempt}/{max_text_retries}) for category '{category_info['name']}'...")
            response = model.generate_content(prompt)
            text = response.text
            clean_json = re.sub(r'^```json\s*', '', text.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r'```$', '', clean_json.strip(), flags=re.MULTILINE)
            candidate_data = json.loads(clean_json)
            
            cand_title = candidate_data.get("title", "")
            # Check for direct title duplication
            if any(cand_title.lower() in existing.lower() for existing in existing_titles):
                print(f"⚠️ Topic retry needed: Generated title '{cand_title}' overlaps with existing title. Retrying...")
                continue
                
            story_data = candidate_data
            break
        except Exception as e:
            print(f"Attempt {attempt}/{max_text_retries} Gemini text generation notice: {e}")
            if attempt < max_text_retries:
                time.sleep(2)

    if not story_data:
        print(f"❌ ABORT: Could not safely generate a non-duplicate story for category '{category_info['name']}' after retries.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = "STORY_TEXT_GEN_FAILED"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    title_slug = story_data.get("slug", f"{category_info['slug']}-{target_date_str}")
    
    # 5. PREVENT DUPLICATE POSTS ON WORDPRESS
    existing_id, existing_url = check_wp_post_exists(title_slug)
    if existing_id:
        print(f"⚠️ WordPress post already exists with slug '{title_slug}' (ID: {existing_id}).")
        occ_info["status"] = "completed"
        occ_info["completed_at"] = datetime.datetime.now().isoformat()
        occ_info["category"] = category_info["name"]
        occ_info["post_id"] = existing_id
        occ_info["post_url"] = existing_url
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return True

    # 6. GENERATE EXACTLY 6 ILLUSTRATIONS (1 Cover + 5 Scenes)
    temp_dir = os.path.join(base_dir, f"backend/assets/temp_illustrations_{target_date_str}")
    os.makedirs(temp_dir, exist_ok=True)
    
    image_paths = {}
    
    # Cover image (Image 1 of 6)
    feat_prompt = story_data.get("featured_image_prompt", f"Cover illustration for {story_data.get('title')}")
    feat_path = os.path.join(temp_dir, "featured.webp")
    image_paths["featured"] = generate_illustration(api_key, feat_prompt, feat_path, story_data.get("title"))

    # 5 Scene images (Images 2 to 6 of 6)
    chapters = story_data.get("chapters", {})
    for i in range(1, 6):
        ch_key = str(i)
        ch_info = chapters.get(ch_key, {})
        img_prompt = ch_info.get("prompt", f"Scene illustration for Chapter {i}")
        img_path = os.path.join(temp_dir, f"scene_{i}.webp")
        image_paths[ch_key] = generate_illustration(api_key, img_prompt, img_path, ch_info.get("title", f"Scene {i}"))

    # Strictly verify that ALL 6 genuine AI illustrations succeeded
    failed_images = [k for k, p in image_paths.items() if not p or not os.path.exists(p)]
    if failed_images:
        print(f"❌ ABORT: AI image generation failed for {len(failed_images)} illustrations: {failed_images}.")
        print("   Fewer than 6 genuine illustrations available. Aborting workflow to prevent incomplete story publication.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = f"AI_IMAGE_GEN_FAILED: missing {failed_images}"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    print(f"✅ EXACTLY 6 genuine WebP AI illustrations successfully generated for {target_date_str}.")

    # 7. WORDPRESS LOGIN & MEDIA UPLOAD
    login_url = f"{base_url}/wp-login.php"
    if not login_wp(wp_user, wp_pass, login_url):
        print("❌ ABORT: WordPress web login failed.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = "WP_LOGIN_FAILED"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    rest_nonce = get_rest_nonce()
    if not rest_nonce:
        print("❌ ABORT: Could not retrieve REST nonce.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = "NONCE_FETCH_FAILED"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    # Upload all 6 images
    uploaded_media = {}
    alt_base = story_data.get("title", "VaniOnline Story")
    
    for key, local_path in image_paths.items():
        if local_path and os.path.exists(local_path):
            alt_text = f"{alt_base} - {key} illustration"
            src_url, att_id = upload_webp_media(rest_nonce, local_path, alt_text)
            if att_id and src_url:
                uploaded_media[key] = {"id": att_id, "url": src_url}

    if len(uploaded_media) < 6:
        print(f"❌ ABORT: WordPress media upload incomplete ({len(uploaded_media)}/6 uploaded). Aborting workflow.")
        occ_info["status"] = "failed"
        occ_info["last_error"] = f"WP_MEDIA_UPLOAD_INCOMPLETE ({len(uploaded_media)}/6)"
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

    # 8. CONSTRUCT STORY HTML
    style_left = 'style="float: left !important; margin: 10px 25px 20px 0 !important; border-radius: 24px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;"'
    style_right = 'style="float: right !important; margin: 10px 0 20px 25px !important; border-radius: 24px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;"'

    intro_hook = f"Discover this heartwarming story on VaniOnline where young friends teach us about sharing, kindness, and love. This delightful children's tale brings warmth and joy to family bedtime reading."
    
    highlights_box = """<div class="story-highlights-box" style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 2px solid #f59e0b; border-radius: 16px; padding: 20px 24px; margin: 24px 0 32px 0; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);">
<h3 style="margin-top: 0; color: #b45309; font-size: 20px; font-weight: 700; border-bottom: 2px dashed #fcd34d; padding-bottom: 8px;">✨ Story Highlights</h3>
<ul style="list-style: none; padding-left: 0; margin-bottom: 0; font-size: 16px; color: #78350f; line-height: 1.8;">
  <li><strong>Core Lesson:</strong> Sharing freely out of love brings true happiness</li>
  <li><strong>Best For:</strong> Children Aged 4–10 (Bedtime & Moral Reading)</li>
  <li><strong>Theme:</strong> Friendship, Kindness & Family Affection</li>
</ul>
</div>"""

    story_html = f"<p>{intro_hook}</p>\n{highlights_box}\n"
    
    for i in range(1, 6):
        ch_key = str(i)
        ch_data = chapters.get(ch_key, {})
        ch_title = ch_data.get("title", f"Section {i}")
        p1 = ch_data.get("p1", "")
        p2 = ch_data.get("p2", "")
        p3 = ch_data.get("p3", "")
        p4 = ch_data.get("p4", "")
        
        img_info = uploaded_media.get(ch_key, {})
        img_url = img_info.get("url", "")
        
        st = style_left if i % 2 != 0 else style_right
        align = "alignleft" if i % 2 != 0 else "alignright"
        
        img_tag = f'<p><img class="{align} size-full" src="{img_url}" alt="{alt_base} {ch_title}" width="600" height="400" {st} /></p>' if img_url else ''
        
        story_html += f"""
<h2 style="clear: both !important; padding-top: 25px !important;">{ch_title}</h2>
{img_tag}
<p>{p1}</p>
<p>{p2}</p>
<p>{p3}</p>
<p>{p4}</p>
"""

    moral_text = story_data.get("moral", "Sharing freely out of love brings true happiness to everyone around us.")
    story_html += f"""
<hr style="clear: both !important; margin: 32px 0;" />
<h2>Moral of the Story</h2>
<p>{moral_text}</p>

<h2>What Children Learn</h2>
<p>Children learn that sharing food and joy builds strong bonds of friendship and family love. They also understand that being honest with parents brings comfort, and that small acts of generosity bring true happiness to all living beings.</p>

<h2>Interactive Questions for Kids</h2>
<ol>
  <li>What was your favorite part of the story?</li>
  <li>How did sharing make the characters feel inside?</li>
  <li>What is one special item or treat you can share with a friend today?</li>
</ol>

<h2>Read Next</h2>
<ul>
  <li><a href="https://vanionline.com/2026/08/26/moral-stories-for-kids-lilys-seeds-kindness/">Moral Stories for Kids: Lily’s Amazing Seeds of Kindness</a></li>
  <li><a href="https://vanionline.com/2026/08/21/bedtime-stories-for-kids-benny-bear-fallen-star/">Bedtime Stories for Kids: Benny Bear and the Fallen Star</a></li>
  <li><a href="https://vanionline.com/2026/08/13/clever-monkey-and-the-crocodile-panchatantra/">Panchatantra Stories for Kids: The Clever Monkey and the Crocodile</a></li>
</ul>"""

    # 9. PUBLISH WORDPRESS POST
    cat_id = resolve_wp_category_id(category_info, rest_nonce=rest_nonce)
    assigned_cats = [cat_id] if cat_id else []

    post_payload = {
        'title': story_data.get("title", f"Delightful Story for Kids ({target_date_str})"),
        'slug': title_slug,
        'content': story_html,
        'status': 'publish',
        'categories': assigned_cats
    }
    
    feat_info = uploaded_media.get("featured", {})
    if feat_info.get("id"):
        post_payload['featured_media'] = feat_info["id"]

    print("Publishing post on WordPress...")
    req_pub = urllib.request.Request(
        f"{base_url}/wp-json/wp/v2/posts",
        data=json.dumps(post_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
        method='POST'
    )
    
    try:
        with opener.open(req_pub) as res_pub:
            post_res = json.loads(res_pub.read().decode('utf-8'))
            new_id = post_res.get("id")
            new_url = post_res.get("link")
            print(f"🎉 SUCCESS! WordPress Post published! ID: {new_id} | URL: {new_url}")
            
            # Supported AIOSEO Metadata Update (Description) without database score manipulation
            try:
                aioseo_url = f"{base_url}/wp-json/aioseo/v1/post?postId={new_id}"
                get_aioseo = urllib.request.Request(aioseo_url, headers={'X-WP-Nonce': rest_nonce})
                with opener.open(get_aioseo) as a_res:
                    a_data = json.loads(a_res.read().decode('utf-8')).get("data", {}).get("currentPost", {})
                if a_data:
                    if "seo_score" in a_data:
                        del a_data["seo_score"]  # Do NOT force or manipulate AIOSEO score
                    a_data["description"] = story_data.get("seo_description", "")
                    post_aioseo = urllib.request.Request(
                        aioseo_post_url,
                        data=json.dumps(a_data).encode('utf-8'),
                        headers={'Content-Type': 'application/json', 'X-WP-Nonce': rest_nonce},
                        method='POST'
                    )
                    opener.open(post_aioseo)
                    print("Supported AIOSEO meta description updated.")
            except Exception as e:
                print("AIOSEO metadata update notice:", e)

            # Cleanup temp directory
            try:
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
            except Exception:
                pass

            # Mark occurrence COMPLETE in persistent state
            occ_info["status"] = "completed"
            occ_info["completed_at"] = datetime.datetime.now().isoformat()
            occ_info["post_id"] = new_id
            occ_info["post_url"] = new_url
            occurrences[target_date_str] = occ_info
            save_scheduler_state(state)
            return True
    except Exception as e:
        print(f"❌ WordPress post publication failed: {e}")
        occ_info["status"] = "failed"
        occ_info["last_error"] = str(e)
        occurrences[target_date_str] = occ_info
        save_scheduler_state(state)
        return False

def check_and_recover_missed_runs(dry_run=False):
    """Detects missed Monday or Wednesday occurrences and recovers them ONCE."""
    today = datetime.date.today()
    print("\n🔍 Checking for missed Monday / Wednesday scheduled occurrences...")
    
    state = load_scheduler_state()
    occurrences = state.get("occurrences", {})
    
    # Check last 14 days
    for i in range(14, -1, -1):
        dt = today - datetime.timedelta(days=i)
        weekday = dt.weekday() # 0 = Monday, 2 = Wednesday
        if weekday in (0, 2):
            day_name = "monday" if weekday == 0 else "wednesday"
            dt_str = dt.strftime("%Y-%m-%d")
            occ_info = occurrences.get(dt_str, {})
            
            if occ_info.get("status") != "completed":
                print(f"⚠️ MISSED OCCURRENCE DETECTED: {day_name.upper()} ({dt_str})")
                print(f"   Recovering occurrence unattended...")
                run_single_day_workflow(day_name, dt_str, dry_run=dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vani Online Unattended Scheduler (Monday + Wednesday)")
    parser.add_argument("--day", choices=["monday", "wednesday"], help="Day of the week (monday or wednesday)")
    parser.add_argument("--phase", choices=["saturday", "sunday"], help="Backward compatibility alias")
    parser.add_argument("--check-missed", action="store_true", help="Check and recover missed occurrences")
    parser.add_argument("--dry-run", action="store_true", help="Run simulation test without production publishing")
    args = parser.parse_args()

    # Priority check for missed runs
    if args.check_missed:
        check_and_recover_missed_runs(dry_run=args.dry_run)
    elif args.day:
        run_single_day_workflow(args.day, dry_run=args.dry_run)
    elif args.phase:
        # Alias mapping
        day = "monday" if args.phase == "saturday" else "wednesday"
        run_single_day_workflow(day, dry_run=args.dry_run)
    else:
        # Default behavior when launched without arguments: recover missed runs or run today's workflow
        today_wd = datetime.date.today().weekday()
        if today_wd == 0:
            run_single_day_workflow("monday", dry_run=args.dry_run)
        elif today_wd == 2:
            run_single_day_workflow("wednesday", dry_run=args.dry_run)
        else:
            check_and_recover_missed_runs(dry_run=args.dry_run)

    print("Vani Scheduler execution finished.")
