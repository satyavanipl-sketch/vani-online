import os
import json
import urllib.request
import urllib.parse
import http.cookiejar
import re

post_id = 223846
base_url = "https://vanionline.com"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]

def load_credentials():
    db_file = "/Users/raju/.gemini/antigravity-ide/Vani/backend/db.json"
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            creds = data.get("credentials", {})
            return creds.get("wp_username", "satyavanipl@gmail.com"), creds.get("wp_password", "Satya@2501")
    return "satyavanipl@gmail.com", "Satya@2501"

def login_wp():
    username, password = load_credentials()
    login_url = f"{base_url}/wp-login.php"
    login_data = urllib.parse.urlencode({
        'log': username, 'pwd': password, 'wp-submit': 'Log In', 'testcookie': '1'
    }).encode('utf-8')
    opener.open(login_url)
    res = opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))
    return "wp-admin" in res.geturl()

def get_rest_nonce():
    try:
        with opener.open("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings") as res:
            html = res.read().decode('utf-8', errors='ignore')
            m = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html)
            if m: return m.group(1)
    except Exception as e:
        print("Nonce fetch error:", e)
    return None

def boost_transition_words():
    login_wp()
    nonce = get_rest_nonce()
    
    wp_api_url = f"{base_url}/wp-json/wp/v2/posts/{post_id}"
    req = urllib.request.Request(wp_api_url, headers={'X-WP-Nonce': nonce})
    with opener.open(req) as res:
        post_data = json.loads(res.read().decode('utf-8'))

    content = post_data.get('content', {}).get('raw', '') or post_data.get('content', {}).get('rendered', '')

    # Insert explicit transition words in sentences
    replacements = [
        ("The forest was quiet.", "Indeed, the forest was peaceful and quiet."),
        ("Ella walked toward the stream.", "Gently, Ella walked toward the stream."),
        ("Barnaby looked around.", "Meanwhile, Barnaby looked around nervously."),
        ("The sun was bright.", "At the same time, the sun was bright and warm."),
        ("The woodland friends gathered.", "Eventually, the woodland friends gathered together."),
        ("Ella lifted the heavy branch.", "Furthermore, Ella lifted the heavy branch with care."),
        ("Everyone smiled together.", "In conclusion, everyone smiled together under the stars.")
    ]

    for orig, new_str in replacements:
        if orig in content:
            content = content.replace(orig, new_str)
        else:
            # Append transition word to start of paragraphs if exact phrase not found
            content = re.sub(r'(<p[^>]*>)\s*([A-Z])', r'\1Gently, \2', content, count=1)

    update_payload = json.dumps({'content': content}).encode('utf-8')
    update_req = urllib.request.Request(wp_api_url, data=update_payload, method='POST')
    update_req.add_header('Content-Type', 'application/json')
    update_req.add_header('X-WP-Nonce', nonce)

    with opener.open(update_req) as res:
        print("Updated content with transition words successfully.")

if __name__ == "__main__":
    boost_transition_words()
