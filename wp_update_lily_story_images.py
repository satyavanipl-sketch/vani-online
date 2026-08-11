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
publish_url = f"{base_url}/?antigravity_action=publish_story"
aioseo_post_url = f"{base_url}/wp-json/aioseo/v1/post"
media_api_url = f"{base_url}/wp-json/wp/v2/media"

brain_dir = "/Users/raju/.gemini/antigravity-ide/brain/85a95491-9f47-4ae9-aa42-cd01b33f5476"

images_to_upload = {
    "featured": {
        "path": os.path.join(brain_dir, "lily_featured_1785995463916.png"),
        "alt": "A little girl named Lily holding a glowing golden seed of kindness - Moral stories for kids"
    },
    1: {
        "path": os.path.join(brain_dir, "lily_ch1_1785995480445.png"),
        "alt": "A little girl named Lily holding a glowing seed of hope in her garden - Moral stories for kids"
    },
    2: {
        "path": os.path.join(brain_dir, "lily_ch2_1785995496416.png"),
        "alt": "A quiet dusty grey town in a peaceful valley representing a town without kindness - Bedtime stories for kids"
    },
    3: {
        "path": os.path.join(brain_dir, "lily_ch3_1785995591317.png"),
        "alt": "Lily washing mixing bowls and preparing warm tea to help her tired mother - Bedtime stories for kids"
    },
    4: {
        "path": os.path.join(brain_dir, "lily_ch4_1785995611765.png"),
        "alt": "Lily digging a small hole and planting her first golden seed near a park bench - Moral stories for kids"
    },
    5: {
        "path": os.path.join(brain_dir, "lily_ch5_1785995629885.png"),
        "alt": "Lily walking down the street helping elderly neighbor Mr. Harrison carry heavy grocery bags - Bedtime stories for kids"
    },
    6: {
        "path": os.path.join(brain_dir, "lily_ch6_1785995649677.png"),
        "alt": "A beautiful green sprout with shimmering golden leaves growing near the park bench - Moral stories for kids"
    },
    7: {
        "path": os.path.join(brain_dir, "lily_ch7_1785995673164.png"),
        "alt": "Lily helping neighbor Mrs. Higgins paint her wooden garden fence under the sun - Bedtime stories for kids"
    },
    8: {
        "path": os.path.join(brain_dir, "lily_ch8_1785995698110.png"),
        "alt": "Colorful flowers of pink, yellow, and blue blooming near doorways and walkways in Stonebrook - Sleep stories for kids"
    },
    9: {
        "path": os.path.join(brain_dir, "lily_ch9_1785995727296.png"),
        "alt": "Lily standing proudly on a festival stage while the townspeople cheer and thank her - Moral stories for kids"
    },
    10: {
        "path": os.path.join(brain_dir, "lily_ch10_1785995755123.png"),
        "alt": "The bright and colorful town of Stonebrook known as the Garden of Kindness - Sleep stories for kids"
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

def upload_images(rest_nonce):
    uploaded_mapping = {}
    
    for key, item in images_to_upload.items():
        img_path = item["path"]
        alt_text = item["alt"]
        
        if not os.path.exists(img_path):
            print(f"Image not found: {img_path}")
            continue
            
        # Load, resize, and convert to WebP in memory
        print(f"Optimizing image: {img_path} to WebP...")
        try:
            im = Image.open(img_path)
            im.thumbnail((800, 800))
            
            webp_io = io.BytesIO()
            im.save(webp_io, format="WEBP", quality=85)
            img_data = webp_io.getvalue()
            
            # Update filename to have .webp extension
            filename = os.path.basename(img_path).replace(".png", ".webp")
        except Exception as img_err:
            print(f"Image optimization failed: {img_err}. Using original PNG.")
            with open(img_path, 'rb') as f:
                img_data = f.read()
            filename = os.path.basename(img_path)
            
        print(f"Uploading {key} ({filename})...")
        
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
                
                print(f"  SUCCESS: Uploaded! ID: {attachment_id}")
                
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
                    print(f"  SUCCESS: Set Alt Text to: '{alt_text}'")
                    
                uploaded_mapping[key] = {
                    "id": attachment_id,
                    "url": source_url
                }
        except Exception as e:
            print(f"Error uploading {key}: {e}")
            
    return uploaded_mapping

def update_lily_post(uploaded_mapping):
    left_style = 'float: left !important; margin: 10px 25px 20px 0 !important; border-radius: 60px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'
    right_style = 'float: right !important; margin: 10px 0 20px 25px !important; border-radius: 60px !important; aspect-ratio: 3/2 !important; object-fit: cover !important; width: 100% !important; max-width: 380px !important; border: 4px solid #fff !important; box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;'
    
    keyword = "moral stories for kids"
    post_title = "Moral Stories for Kids: Lily’s Seeds of Kindness 🌸🌱"
    
    story_html = f"<p>Deep within a peaceful valley, a brand new adventure began for a little girl named Lily. This is one of the most inspiring <strong>{keyword}</strong> that teaches children how small acts of kindness can bloom into the most beautiful miracles.</p>"
    
    story_html += """
<div class="story-intro-box" style="background-color: #f0f7f4; border-left: 5px solid #2ecc71; padding: 20px; border-radius: 8px; margin: 25px 0;">
    <h3 style="margin-top: 0 !important; color: #27ae60;">🌟 Fun Facts for Curious Kids!</h3>
    <ul>
        <li><strong>Sleeping Seeds:</strong> Did you know some seeds can sleep in dry soil for years before they sprout? They wait for the perfect rain to wake them up!</li>
        <li><strong>Following the Sun:</strong> Sunflowers can grow up to 10 feet tall, and they turn their flower heads to follow the sun across the sky every single day!</li>
        <li><strong>Kindness is Magical:</strong> Doing a kind deed actually makes your brain release happy chemicals that make you feel warm and calm. Kindness is scientifically magical!</li>
    </ul>
    <h3 style="color: #27ae60; margin-top: 20px !important;">🎒 Why You Will Love Reading This Story!</h3>
    <p style="margin-bottom: 0 !important;">Are you ready to explore a town where magical flowers grow from kind words? Join young Lily as she receives a bag of glowing golden seeds from a mysterious traveler and learns how one simple smile can change everything. Let's start reading!</p>
</div>
"""

    lily_chapters = {
        1: {
            'title': 'The Quiet Town of Stonebrook',
            'p1': 'Lily was a seven-year-old girl with bright green eyes and a cheerful smile. She lived in a small, quiet town called Stonebrook. The town was peaceful, but the people who lived there rarely spoke to each other, and the streets were grey and dusty without any colorful flowers.',
            'p2': 'Every day, Lily would walk to school, wishing the town could be a little brighter and friendlier. She loved looking at pictures of beautiful gardens in her books, dreaming of planting her own some day.',
            'p3': 'Her father worked in the local woodmill, and her mother baked fresh bread for the small bakery. Although they were busy, they always taught Lily that a kind heart was the most important thing a person could have.',
            'p4': 'She kept their words close, hoping that she could find a way to bring joy to the quiet streets of Stonebrook. Little did she know, her wish was about to come true in a very magical way.'
        },
        2: {
            'title': 'The Mysterious Visitor',
            'p1': 'One sunny morning, an old gardener with a wheelbarrow full of clay pots arrived in the town square. He wore a patched green coat and had a long, silver beard that caught the sunlight. He looked like he had walked from a distant land.',
            'p2': 'He noticed Lily watching him with curious eyes and called her over with a warm, gentle wave. As Lily walked over, she saw that the pots in his wheelbarrow were empty, containing only rich, dark soil.',
            'p3': 'The traveler smiled, his eyes twinkling like stars. "You have a very bright spirit, little one," he said softly. He reached into his deep coat pocket and pulled out a small cloth bag tied with a golden ribbon.',
            'p4': 'He handed it to Lily, whispering, "These are the seeds of kindness. They will grow into beautiful, magical flowers, but only if you plant them with a kind and helpful deed. Remember, the seed is only the beginning."'
        },
        3: {
            'title': 'The Gift of Golden Seeds',
            'p1': 'Lily held the bag carefully, feeling a soft warmth coming from the cloth. She opened it to find ten tiny, glowing golden seeds that shone like little stars. They looked far too beautiful to be ordinary garden seeds.',
            'p2': 'She wanted to plant them right away, but she remembered the gardener\'s words: they needed a kind deed to grow. She spent the rest of the day thinking about how she could help someone.',
            'p3': 'She saw her mother looking tired after a long day of baking. Lily quietly washed all the mixing bowls, swept the kitchen floor, and prepared a warm cup of herbal tea for her.',
            'p4': 'Her mother smiled and hugged her, her tiredness fading. Lily knew she had performed her first kind deed, and she was ready to plant her first seed.'
        },
        4: {
            'title': 'The First Act of Kindness',
            'p1': 'The next morning, Lily went to the quiet park in the middle of Stonebrook. The park had a single wooden bench under a dry, leafless oak tree. It was a very grey place where no one ever sat.',
            'p2': 'Lily dug a tiny hole in the soil near the park bench. She took one golden seed from her bag, placed it gently in the earth, and covered it with soft, dark soil.',
            'p3': 'As she smoothed the ground, she whispered a small wish: "Grow well, little seed, and bring a smile to whoever sits on this bench." She watered it with a small tin can she brought from home.',
            'p4': 'She sat back and watched, but nothing happened. Lily smiled, knowing that magic takes time. She decided to keep looking for ways to help her neighbors.'
        },
        5: {
            'title': 'Watering the Seed',
            'p1': 'Later that afternoon, Lily saw Mr. Harrison, an elderly neighbor who lived alone. He was walking slowly down the street, carrying two heavy bags of groceries, looking very tired.',
            'p2': 'Mr. Harrison watched the little girl and asked what she was doing. Lily walked over, smiled warmly, and offered to help him carry his heavy bags of groceries to his house. "It\'s a sunny day, and I would love to walk with you," she said.',
            'p3': 'Mr. Harrison was surprised by her kindness, but he accepted with a grateful nod. As they walked down the street, Lily talked about her school and her books, and Mr. Harrison shared stories of his youth.',
            'p4': 'By the time they reached his doorstep, the elderly man was smiling broadly, his lonely look completely gone. He thanked Lily and gave her a sweet red apple to show his gratitude.'
        },
        6: {
            'title': 'The Golden Sprout',
            'p1': 'Lily felt happy inside, realizing that helping others was just as sweet as any candy. She waved goodbye and ran back toward the park.',
            'p2': 'The next morning, Lily woke up early and ran back to the park bench. To her absolute amazement, a beautiful green sprout had appeared where she had planted the seed. It had tiny golden leaves that shimmered like gold leaf in the morning sun.',
            'p3': 'A soft, pleasant fragrance of honey and roses spread from the tiny sprout, making the air around the park bench feel warm and cozy. Mr. Harrison was already sitting on the bench, looking at the sprout in wonder.',
            'p4': '"I haven\'t smelled anything this beautiful in years, Lily," he said, his eyes bright with joy. He looked healthier and happier than yesterday, holding a watering can to keep the sprout fresh.'
        },
        7: {
            'title': 'Spreading the Magic',
            'p1': 'Lily realized that the old gardener\'s words were true. Her kind deed had watered the seed, and the magic was real.',
            'p2': 'Excited by the golden sprout, Lily decided to plant more seeds around the town. The next day, she saw Mrs. Higgins trying to paint her old wooden garden fence all by herself, looking very tired under the hot sun.',
            'p3': 'Lily ran over, picked up a brush, and helped Mrs. Higgins paint the lower boards. They laughed and sang songs together, making the work fast and fun. Before leaving, Lily secretly planted a golden seed near the fence.',
            'p4': 'A day later, at school, a new boy named Leo sat alone in the schoolyard because he was shy. Lily walked over, shared her fresh strawberry jam sandwich with him, and invited him to play tag.'
        },
        8: {
            'title': 'The Town Begins to Bloom',
            'p1': 'While Leo was running happily, Lily gently pushed another golden seed into the soil under the large oak tree, wishing for Leo to make many new friends.',
            'p2': 'Within a week, the golden seeds began to sprout all over Stonebrook. Beautiful, colorful flowers of pink, yellow, and blue started growing near the doorways, walkways, and park benches. The streets looked like a living rainbow.',
            'p3': 'The sweet scent of the blossoms filled the air, making the people of the town feel happy and light. People who used to walk in silence now stopped to admire the flowers and talk to each other.',
            'p4': 'Neighbors began helping neighbors, sharing fresh vegetables from their gardens and offering helping hands to fix old roofs. The grey, dusty town was transforming into a warm, cheerful community.'
        },
        9: {
            'title': 'The Festival of Kindness',
            'p1': 'Lily watched the change with a happy heart, her cloth bag growing lighter as she planted more seeds of joy.',
            'p2': 'The townspeople soon noticed the beautiful flowers and realized that young Lily was the one planting them. Inspired by her simple acts, the mayor decided to organize a grand autumn festival in the town square.',
            'p3': 'Everyone contributed to the festival. Mr. Harrison baked sweet apple pies, Mrs. Higgins brought colorful banners, and Leo\'s family set up a fun game booth. The square was filled with music, laughter, and light.',
            'p4': 'Lily was invited to the stage, where the townspeople cheered and thanked her for bringing color and warmth back to Stonebrook. She stood proudly, holding her yellow garden boots.'
        },
        10: {
            'title': 'The Garden of Stonebrook',
            'p1': 'The festival was the happiest day the town had ever seen, bringing everyone together as one big family.',
            'p2': 'Stonebrook was no longer grey and quiet. It was now the brightest, most colorful town in the valley, known far and wide as the Garden of Kindness. Visitors came from other villages just to walk its fragrant streets.',
            'p3': 'Lily looked at the beautiful town and realized that the traveler was right: kindness is the most magical seed of all. It doesn\'t take much to make a big difference—just a warm heart and a willingness to help.',
            'p4': 'She tucked her empty cloth bag into her wooden drawer, knowing she didn\'t need golden seeds anymore. The real magic was now growing in the hearts of everyone in Stonebrook.'
        }
    }

    for ch in range(1, 11):
        ch_title = lily_chapters[ch]['title']
        p1 = lily_chapters[ch]['p1']
        p2 = lily_chapters[ch]['p2']
        p3 = lily_chapters[ch]['p3']
        p4 = lily_chapters[ch]['p4']
        
        url = uploaded_mapping[ch]["url"]
        style = left_style if ch % 2 == 1 else right_style
        
        # Use descriptive alt text for on-page SEO
        ch_alt = images_to_upload[ch]["alt"]
        img_tag = f'<img src="{url}" alt="{ch_alt}" class="alignnone size-medium" style="{style}" />'
        
        # Correct heading outline: Use H2 instead of H3 for story chapters
        story_html += f"""
<h2 style="clear: both !important; padding-top: 25px !important;">{ch_title}</h2>
{img_tag}
<p>{p1}</p>
<p>{p2}</p>
<p>{p3}</p>
<p>{p4}</p>
"""
        
    # Add a proper H2 heading for Moral of the Story to keep outline semantic
    story_html += f"""
<h2 style="clear: both !important; padding-top: 25px !important;">Moral of the Story</h2>
<div class="story-moral" style="background: #fdf6e2; padding: 20px; border-left: 5px solid #ff9f43; border-radius: 8px; margin-top: 15px; font-style: italic;">
    Small acts of kindness have a magical way of growing, making the world a much brighter and happier place for everyone.
</div>"""

    payload = {
        'post_id': 802,
        'title': post_title,
        'slug': 'moral-stories-for-kids-lilys-seeds-kindness',
        'content': story_html,
        'post_status': 'future',
        'featured_image_id': uploaded_mapping["featured"]["id"]
    }
    
    print("Updating Lily post on WordPress...")
    req = urllib.request.Request(
        publish_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with opener.open(req) as res:
        response_data = json.loads(res.read().decode('utf-8'))
        print("Update Post Response:", response_data)
        if response_data.get('success', False):
            print("SUCCESS: Lily post 802 updated successfully!")
            return True
            
    return False

def update_aioseo_meta(rest_nonce):
    print("Fetching current settings for AIOSEO...")
    get_url = f"{base_url}/wp-json/aioseo/v1/post?postId=802"
    get_req = urllib.request.Request(get_url)
    get_req.add_header('X-WP-Nonce', rest_nonce)
    
    current_post_data = None
    try:
        with opener.open(get_req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            current_post_data = res_json.get("data", {}).get("currentPost", {})
    except Exception as e:
        print("Failed to fetch AIOSEO data:", e)
        return False
        
    if not current_post_data:
        print("No post SEO structure returned.")
        return False
        
    current_post_data["title"] = "Moral Stories for Kids: Lily’s Seeds of Kindness (With Pictures)"
    current_post_data["description"] = "Discover how a little girl named Lily changes her town in this lovely moral stories for kids. Learn the magical power of kindness and sharing."
    current_post_data["default"] = False
    
    if "keyphrases" not in current_post_data:
        current_post_data["keyphrases"] = {}
    if "focus" not in current_post_data["keyphrases"]:
        current_post_data["keyphrases"]["focus"] = {}
        
    current_post_data["keyphrases"]["focus"]["keyphrase"] = "moral stories for kids"
    
    print("Sending POST request to update AIOSEO data...")
    post_data = json.dumps(current_post_data).encode('utf-8')
    post_req = urllib.request.Request(aioseo_post_url, data=post_data, method='POST')
    post_req.add_header('Content-Type', 'application/json; charset=utf-8')
    post_req.add_header('X-WP-Nonce', rest_nonce)
    
    try:
        with opener.open(post_req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            if res_json.get("success"):
                print("SUCCESS: AIOSEO settings updated successfully!")
                return True
            else:
                print("Failed to update AIOSEO:", res_json)
    except Exception as e:
        print("Error during AIOSEO update:", e)
        
    return False

if __name__ == "__main__":
    if login():
        print("Login successful!")
        
        # Fetch REST Nonce
        rest_nonce = None
        req = urllib.request.Request("https://vanionline.com/wp-admin/admin.php?page=googlesitekit-settings")
        with opener.open(req) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            nonce_match = re.search(r'["\']nonce["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html_content)
            if nonce_match:
                rest_nonce = nonce_match.group(1)
                print(f"REST Nonce: {rest_nonce}")
                
        if rest_nonce:
            uploaded_mapping = upload_images(rest_nonce)
            if len(uploaded_mapping) == len(images_to_upload):
                if update_lily_post(uploaded_mapping):
                    update_aioseo_meta(rest_nonce)
                    
                    # Flush cache
                    print("Flushing cache...")
                    try:
                        opener.open(f"{base_url}/?antigravity_action=flush_cache")
                        print("Cache flushed successfully!")
                    except Exception as e:
                        print("Failed to flush cache:", e)
                    print("ALL DONE!")
            else:
                print("Not all images were uploaded successfully. Aborting post update.")
    else:
        print("Login failed.")
