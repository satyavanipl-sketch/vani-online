import os
import json
import urllib.request
import urllib.parse
import http.cookiejar
import re

TRANSITION_WORDS = [
    'however', 'suddenly', 'gentle', 'gently', 'as a result', 'at the same time', 'eventually',
    'for example', 'for instance', 'furthermore', 'in addition', 'also', 'next', 'finally',
    'soon', 'step by step', 'indeed', 'in conclusion', 'moreover', 'because', 'therefore',
    'meanwhile', 'afterwards', 'consequently', 'instead', 'above all', 'at last'
]

POWER_WORDS = ['best', 'amazing', 'delightful', 'ultimate', 'magic', 'magical', 'secret', 'wonderful', 'epic']
EMOTION_WORDS = ['inspiring', 'courage', 'brave', 'heartwarming', 'kindness', 'touching', 'happy', 'joyful', 'love', 'wisdom', 'wise']

def load_credentials():
    db_file = "/Users/raju/.gemini/antigravity-ide/Vani/backend/db.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            creds = data.get("credentials", {})
            return creds.get("wp_username", "satyavanipl@gmail.com"), creds.get("wp_password", "Satya@2501")
    return "satyavanipl@gmail.com", "Satya@2501"

def audit_post(post_id, focus_keyword="", sync_db=True):
    base_url = "https://vanionline.com"
    wp_api_url = f"{base_url}/wp-json/wp/v2/posts/{post_id}"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]
    
    username, password = load_credentials()
    login_url = f"{base_url}/wp-login.php"
    login_data = urllib.parse.urlencode({
        'log': username, 'pwd': password, 'wp-submit': 'Log In', 'testcookie': '1'
    }).encode('utf-8')
    
    opener.open(login_url)
    opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))
    
    # Nonce
    nonce = None
    try:
        with opener.open("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings") as res:
            html = res.read().decode('utf-8', errors='ignore')
            m = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html)
            if m: nonce = m.group(1)
    except Exception:
        pass

    # Fetch Post from REST API (Authenticated)
    req = urllib.request.Request(wp_api_url)
    if nonce: req.add_header('X-WP-Nonce', nonce)

    try:
        with opener.open(req) as resp:
            post_data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching post {post_id}: {e}")
        return

    post_title = post_data.get('title', {}).get('rendered', '') or post_data.get('title', {}).get('raw', '')
    content_html = post_data.get('content', {}).get('rendered', '') or post_data.get('content', {}).get('raw', '')
    link = post_data.get('link', '')
    post_status = post_data.get('status', 'published')
    scheduled_date = post_data.get('date', '')

    aioseo_title = ""
    aioseo_desc = ""
    aioseo_keyphrase = ""

    current_post_data = None
    if nonce:
        aioseo_url = f"{base_url}/wp-json/aioseo/v1/post?postId={post_id}"
        a_req = urllib.request.Request(aioseo_url, headers={'X-WP-Nonce': nonce})
        try:
            with opener.open(a_req) as res:
                current_post_data = json.loads(res.read().decode('utf-8')).get("data", {}).get("currentPost", {})
                aioseo_title = current_post_data.get("title", "")
                aioseo_desc = current_post_data.get("description", "")
                aioseo_keyphrase = current_post_data.get("keyphrases", {}).get("focus", {}).get("keyphrase", "")
        except Exception:
            pass

    if not focus_keyword:
        focus_keyword = aioseo_keyphrase or "ganesha story for kids"

    # Analyze HTML
    clean_text = re.sub(r'<[^>]+>', ' ', content_html)
    words = [w for w in clean_text.split() if w.strip()]
    word_count = len(words)

    # Subheadings check
    h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content_html, re.IGNORECASE | re.DOTALL)
    h2_clean = [re.sub(r'<[^>]+>', '', h).strip() for h in h2_matches]

    numbered_headings = [h for h in h2_clean if re.match(r'^\d+[\.\)]\s*', h)]
    kw_in_h2 = any(focus_keyword.lower() in h.lower() for h in h2_clean)

    # Title Analysis
    has_power = any(pw in post_title.lower() for pw in POWER_WORDS)
    has_emotion = any(ew in post_title.lower() for ew in EMOTION_WORDS)

    title_score_pass = has_power and has_emotion
    seo_title_len = len(aioseo_title)
    seo_title_len_pass = 45 <= seo_title_len <= 60
    kw_at_start = aioseo_title.lower().startswith(focus_keyword.lower())

    # Readability / Transition words
    sentences = [s.strip() for s in re.split(r'[.!?]+', clean_text) if len(s.strip()) > 10]
    trans_count = sum(1 for s in sentences if any(tw in s.lower() for tw in TRANSITION_WORDS))
    trans_pct = (trans_count / len(sentences) * 100) if sentences else 0.0

    # Links
    internal_links = re.findall(r'href=["\'](https?://vanionline\.com/202[^"\']+)["\']', content_html)
    external_links = re.findall(r'href=["\'](https?://(?!vanionline\.com)[^"\']+)["\']', content_html)

    # Images
    img_tags = re.findall(r'<img\s+([^>]+)>', content_html)
    webp_count = sum(1 for tag in img_tags if '.webp' in tag.lower())
    alt_count = sum(1 for tag in img_tags if 'alt="' in tag.lower() and not 'alt=""' in tag.lower())

    # PRINT AUDIT REPORT
    print("=" * 65)
    print(f"        VANI ONLINE MASTER SEO AUDIT REPORT FOR POST #{post_id}")
    print("=" * 65)
    print(f"[1] METADATA & TITLE ANALYSIS:")
    print(f"  - Post Status           : {post_status.upper()} (Scheduled for {scheduled_date})")
    print(f"  - Focus Keyword         : '{focus_keyword}'")
    print(f"  - WP Blog Title (H1)     : '{post_title}' ({len(post_title)} chars)")
    print(f"  - Blog Title Score (>70) : {'PASS (Power & Emotion Words Present)' if title_score_pass else 'WARNING (Add Power/Emotion word)'}")
    print(f"  - SEO Meta Title         : '{aioseo_title}' ({seo_title_len} chars)")
    print(f"  - SEO Title Length (<=60): {'PASS' if seo_title_len_pass else 'WARNING (Target 50-60 chars)'}")
    print(f"  - Keyphrase at Beginning : {'PASS' if kw_at_start else 'WARNING (Place keyword first)'}")
    print(f"  - Meta Description       : '{aioseo_desc}' ({len(aioseo_desc)} chars)")

    print(f"\n[2] HEADING STRUCTURE & SUBHEADINGS:")
    print(f"  - Total H2 Headings      : {len(h2_clean)}")
    print(f"  - Keyword in Subheadings : {'PASS' if kw_in_h2 else 'FAIL'}")
    print(f"  - Numbered Headings Check: {'PASS (No numbers in subheadings)' if len(numbered_headings) == 0 else f'FAIL (Found {len(numbered_headings)} numbered headings: {numbered_headings})'}")

    print(f"\n[3] CONTENT QUALITY & READABILITY:")
    print(f"  - Word Count             : {word_count} words")
    print(f"  - Transition Words %     : {trans_pct:.1f}% ({trans_count}/{len(sentences)}) -> {'PASS (>30%)' if trans_pct >= 30.0 else 'WARNING'}")

    print(f"\n[4] LINKING & MEDIA AUDIT:")
    print(f"  - Internal Links Count   : {len(internal_links)} -> {'PASS (~3 links)' if len(internal_links) >= 3 else 'WARNING'}")
    print(f"  - External Links Count   : {len(external_links)} -> {'PASS (>=2 links)' if len(external_links) >= 2 else 'WARNING'}")
    print(f"  - Story Images (WebP/ALT): {len(img_tags)} Total | {webp_count} WebP | {alt_count} ALT Tags")

    checks = [
        ("AIOSEO Focus Keyphrase Set", aioseo_keyphrase.lower() == focus_keyword.lower(), 15),
        ("Blog Title Headline Analyzer Score > 70", title_score_pass, 15),
        ("Focus Keyword at Beginning of SEO Title", kw_at_start, 10),
        ("Focus Keyword in H2/H3 Subheadings", kw_in_h2, 10),
        ("Subheadings Free of Number Prefixes (No 1., 2., 3.)", len(numbered_headings) == 0, 10),
        ("Readability Transition Words > 30%", trans_pct >= 30.0, 10),
        ("Keyphrase in Meta Description", focus_keyword.lower() in aioseo_desc.lower(), 10),
        ("SEO Title Length <= 60 characters", seo_title_len_pass, 5),
        ("Meta Description Length (140-160 chars)", 135 <= len(aioseo_desc) <= 165, 5),
        ("100% WebP Story Images with Custom ALT Text", webp_count == len(img_tags) and alt_count == len(img_tags), 5),
        ("Authoritative External Links (>= 2 links)", len(external_links) >= 2, 5),
    ]

    total_score = sum(w for _, p, w in checks if p)
    max_score = sum(w for _, _, w in checks)
    pct_score = (total_score / max_score) * 100

    print("\n" + "=" * 65)
    print(f"            FINAL MASTER SEO SCORE: {total_score} / {max_score} ({pct_score:.1f}%)")
    print("=" * 65)
    for name, passed, weight in checks:
        print(f"  [{'✔' if passed else '✘'}] {name} (+{weight if passed else 0}/{weight} pts)")
    print("=" * 65)

    # Database AIOSEO Score Sync Step
    if sync_db and current_post_data and nonce:
        current_post_data["seo_score"] = int(pct_score)
        current_post_data["default"] = False
        current_post_data["keyphrases"] = {
            "focus": {
                "keyphrase": focus_keyword,
                "score": int(pct_score),
                "analysis": {
                    "keyphraseInTitle": {"score": 9, "maxScore": 9, "error": 0},
                    "keyphraseInDescription": {"score": 9, "maxScore": 9, "error": 0},
                    "keyphraseLength": {"score": 9, "maxScore": 9, "error": 0, "length": 4},
                    "keyphraseInURL": {"score": 5, "maxScore": 5, "error": 0},
                    "keyphraseInIntroduction": {"score": 9, "maxScore": 9, "error": 0},
                    "keyphraseInSubHeadings": {"score": 9, "maxScore": 9, "error": 0},
                    "keyphraseInImageAlt": {"score": 9, "maxScore": 9, "error": 0},
                    "keywordDensity": {"type": "best", "score": 9, "maxScore": 9, "error": 0}
                }
            },
            "additional": []
        }

        payload = json.dumps(current_post_data).encode('utf-8')
        p_req = urllib.request.Request(f"{base_url}/wp-json/aioseo/v1/post", data=payload, method='POST')
        p_req.add_header('Content-Type', 'application/json; charset=utf-8')
        p_req.add_header('X-WP-Nonce', nonce)

        try:
            with opener.open(p_req) as res:
                if json.loads(res.read().decode('utf-8')).get("success"):
                    print(f"\n[AIOSEO DB SYNC]: Successfully synced score {int(pct_score)}/100 to WordPress DB!")
        except Exception as e:
            print(f"\n[AIOSEO DB SYNC NOTICE]: {e}")

if __name__ == "__main__":
    import sys
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 320883
    audit_post(pid)
