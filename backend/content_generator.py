import os
import random
import json
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# High-quality fallback posts if Gemini is not configured
FALLBACK_POSTS = [
    {
        "layout_type": "infographic",
        "commentary": (
            "🚀 Write clean code, not clever code.\n\n"
            "Many developers fall into the trap of writing complex, compressed code to solve simple problems. "
            "But clever code is hard to maintain, debug, and scale. Real senior engineering is about making "
            "the complex feel simple.\n\n"
            "Keep it simple. Your future self (and team) will thank you!\n\n"
            "#SoftwareEngineering #CleanCode #ProgrammingTips #WebDevelopment #Coding"
        ),
        "card_category": "SOFTWARE ENGINEERING",
        "card_title": "Write Clean Code, Not Clever Code",
        "card_subtitle": "3 rules that save weeks of debugging",
        "card_points": [
            {"title": "Readability over brevity", "description": "Write code for human readers first."},
            {"title": "Self-documenting variables", "description": "Choose descriptive names over shorthand."},
            {"title": "Standard patterns", "description": "Avoid ad-hoc, overly complex shortcuts."}
        ],
        "card_takeaway": "Senior engineering is about making the complex feel simple.",
        "primary_color": "#143CDC",
        "secondary_color": "#5832E2",
        "background_color": "#F8F9FC",
        "illustration_icon": "💻"
    },
    {
        "layout_type": "infographic",
        "commentary": (
            "🧠 The secret to productivity isn't time management—it's energy management.\n\n"
            "We all have the same 24 hours, but we don't have the same level of focus. Pushing through code blocks "
            "when your brain is exhausted leads to bugs, frustration, and technical debt.\n\n"
            "Align your tasks with your energy levels to build faster and avoid burnout!\n\n"
            "#Productivity #DeveloperLife #CareerGrowth #WorkLifeBalance #Programming"
        ),
        "card_category": "PRODUCTIVITY",
        "card_title": "Manage Energy, Not Just Time",
        "card_subtitle": "3 levels of developers' cognitive focus",
        "card_points": [
            {"title": "High energy focus", "description": "Deep work, core architecture, algorithms."},
            {"title": "Medium energy tasks", "description": "Code reviews, minor features, planning."},
            {"title": "Low energy chores", "description": "Styling, documentation, checking emails."}
        ],
        "card_takeaway": "Align tasks with your mental batteries for peak output.",
        "primary_color": "#059669",
        "secondary_color": "#0D9488",
        "background_color": "#F0FDF4",
        "illustration_icon": "🧠"
    }
]

def generate_post_content(gemini_key=None, topic=None):
    """Generates the post text and card quote using Gemini if available, otherwise falls back to templates."""
    gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
    
    def format_output(post_data):
        if "layout_type" not in post_data:
            post_data["layout_type"] = "infographic"
            
        card_fields = {
            "layout_type": post_data.get("layout_type", "infographic"),
            "commentary": post_data.get("commentary", ""),
            "card_title": post_data.get("card_title", post_data.get("title", "")),
            "card_takeaway": post_data.get("card_takeaway", post_data.get("takeaway", "")),
            "primary_color": post_data.get("primary_color", ""),
            "secondary_color": post_data.get("secondary_color", ""),
            "background_color": post_data.get("background_color", ""),
            "illustration_icon": post_data.get("illustration_icon", "💡"),
            
            # infographic fields
            "card_category": post_data.get("card_category", post_data.get("category", "DAILY INSIGHT")),
            "card_subtitle": post_data.get("card_subtitle", post_data.get("subtitle", "")),
            "card_points": post_data.get("card_points", post_data.get("points", [])),
            
            # code_snippet fields
            "code_title": post_data.get("code_title", ""),
            "code_content": post_data.get("code_content", ""),
            "code_explanation": post_data.get("code_explanation", ""),
            
            # chart_graph fields
            "chart_title": post_data.get("chart_title", ""),
            "chart_type": post_data.get("chart_type", "bar"),
            "chart_labels": post_data.get("chart_labels", []),
            "chart_values": post_data.get("chart_values", []),
            
            # comparison_table fields
            "table_headers": post_data.get("table_headers", []),
            "table_rows": post_data.get("table_rows", [])
        }
        return {
            "commentary": post_data["commentary"],
            "card_text": json.dumps(card_fields, indent=2)
        }

    if not gemini_key or gemini_key == "your_api_key_here":
        print("ℹ️ Gemini API key not found. Using high-quality local templates.")
        if topic:
            topic_lower = topic.lower()
            matched = [p for p in FALLBACK_POSTS if topic_lower in p["commentary"].lower() or topic_lower in p["card_title"].lower()]
            if matched:
                return format_output(random.choice(matched))
        return format_output(random.choice(FALLBACK_POSTS))
    
    topic_desc = f"specifically on the topic of '{topic}'" if topic else "about a modern software engineering topic, AI, coding practice, system design, or productivity hack"
    print(f"🔮 Querying Gemini for professional LinkedIn post about: {topic or 'Random Tech Topic'}...")
    
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-pro-exp"
    ]
    
    def clean_and_parse_json(raw_text):
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
            
        bracket_count = 0
        first_brace_idx = cleaned.find("{")
        if first_brace_idx != -1:
            for idx in range(first_brace_idx, len(cleaned)):
                char = cleaned[idx]
                if char == "{":
                    bracket_count += 1
                elif char == "}":
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_candidate = cleaned[first_brace_idx : idx + 1]
                        try:
                            return json.loads(json_candidate)
                        except json.JSONDecodeError:
                            break
        raise ValueError("Could not parse JSON from response")

    prompt = (
        f"Write a highly engaging, professional LinkedIn post {topic_desc}.\n\n"
        "Pick the latest 2026 industry trend or hot topic in software engineering, AI, developer productivity, or web development "
        "if the topic is general. Always research and prioritize the latest context.\n\n"
        "Select the most appropriate visual layout type from the following 4 options:\n"
        "1. 'code_snippet': Best when explaining code concepts, React hooks, system functions, or design patterns. Requires showing actual code.\n"
        "2. 'chart_graph': Best when illustrating statistics, trends, comparison metrics, scaling, or performance benchmarks.\n"
        "3. 'comparison_table': Best when comparing framework features, database types, tool suites, or 'before vs after' practices.\n"
        "4. 'infographic': Best when illustrating general concepts, tips, guides, listicles, or rules (this is a multi-point list card).\n\n"
        "Return the output in a JSON object with the following fields depending on the selected layout_type:\n\n"
        "COMMON FIELDS:\n"
        "- 'layout_type': The selected layout ('code_snippet', 'chart_graph', 'comparison_table', or 'infographic').\n"
        "- 'commentary': The full markdown text of the post to copy-paste (under 150 words).\n"
        "- 'card_title': A bold headline for the card (under 45 characters).\n"
        "- 'card_takeaway': A final key takeaway message (under 80 characters).\n"
        "- 'primary_color': Hex code representing the main theme color for this specific topic (e.g. Canva purple '#7D2AE8', Redis red '#D82C20', React blue '#00D2FF', growth green '#059669', business gold '#B25E00', general tech blue '#143CDC').\n"
        "- 'secondary_color': Hex code representing a matching secondary accent color.\n"
        "- 'background_color': Hex code representing a light background color that compliments the theme (e.g., '#F8F5FC' for Canva, '#FDF4F3' for Redis, '#F0FDF4' for green, '#F0F9FF' for blue).\n"
        "- 'illustration_icon': A single Unicode emoji symbol representing the specific topic (e.g. '🎨' for design/Canva, '⚡' for performance/speed, '🔒' for security/encryption, '🚀' for growth/launch, '🧠' for AI/productivity, '📈' for metrics, '💻' for coding, '💰' for finance, '⚙️' for engineering).\n\n"
        "FIELDS IF layout_type IS 'code_snippet':\n"
        "- 'code_title': Small title header for the code window (under 30 characters).\n"
        "- 'code_content': The actual programming code block to display (keep under 12 lines, clean syntax).\n"
        "- 'code_explanation': A caption explaining the code snippet (under 80 characters).\n\n"
        "FIELDS IF layout_type IS 'chart_graph':\n"
        "- 'chart_title': Title of the chart.\n"
        "- 'chart_type': One of ['bar', 'line'].\n"
        "- 'chart_labels': List of 3 to 5 strings for x-axis categories.\n"
        "- 'chart_values': List of corresponding numerical values (e.g. [80, 45, 10]).\n\n"
        "FIELDS IF layout_type IS 'comparison_table':\n"
        "- 'table_headers': List of 2 or 3 column header strings.\n"
        "- 'table_rows': List of lists of strings representing cell values. Max 4 rows. Columns must match headers length.\n\n"
        "FIELDS IF layout_type IS 'infographic':\n"
        "- 'card_category': A general category header under 30 characters.\n"
        "- 'card_subtitle': A punchy list introduction under 50 characters.\n"
        "- 'card_points': A list of exactly 4 or 5 points. Each point is a JSON object with 'title' (bold title, under 30 characters) and 'description' (short explanation, under 50 characters).\n\n"
        "CRITICAL: The output MUST be a valid JSON. Do not include unescaped double quotes inside string values. "
        "Use single quotes if you need to wrap terms inside description or title strings."
    )

    try:
        genai.configure(api_key=gemini_key)
        for model_name in models_to_try:
            try:
                print(f"🔮 Attempting Content Generation with model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                post_data = clean_and_parse_json(response.text)
                if "commentary" in post_data and ("card_title" in post_data or "title" in post_data):
                    print(f"✅ Success! Content generated using: {model_name}")
                    return format_output(post_data)
            except Exception as model_err:
                print(f"⚠️ Model {model_name} failed: {model_err}. Retrying next available model...")
                continue
                
        raise RuntimeError("All configured Gemini models failed or exceeded quota.")
    except Exception as e:
        print(f"⚠️ Gemini API failure across all models: {e}. Falling back to templates.")
        
    if topic:
        topic_lower = topic.lower()
        matched = [p for p in FALLBACK_POSTS if topic_lower in p["commentary"].lower() or topic_lower in p["card_title"].lower()]
        if matched:
            return format_output(random.choice(matched))
    return format_output(random.choice(FALLBACK_POSTS))

def draw_gradient_background(draw, width, height, color1, color2):
    """Draws a smooth linear gradient background."""
    for y in range(height):
        ratio = y / height
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def find_font(size, style="regular"):
    """Tries to find a specific style of Arial on Mac, falling back to PIL default font."""
    mac_fonts = {
        "regular": [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "Arial.ttf"
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "Arial-Bold.ttf"
        ],
        "italic": [
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "Arial-Italic.ttf"
        ]
    }
    
    paths = mac_fonts.get(style, mac_fonts["regular"])
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width):
    """Wraps text so it fits within a maximum pixel width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_logo_badge(size, is_dark_mode=False):
    """Loads and resizes the persistent brand logo image from assets, fallback to drawing if missing."""
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    logo_path = os.path.join(assets_dir, "logo.jpg")
    
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            
            # Auto-crop excessive white margins around the circular logo badge
            from PIL import ImageOps
            gray = ImageOps.grayscale(logo_img.convert("RGB"))
            inverted = ImageOps.invert(gray)
            bbox = inverted.getbbox()
            if bbox:
                # Add small padding around the cropped logo
                pad = 10
                bx1 = max(0, bbox[0] - pad)
                by1 = max(0, bbox[1] - pad)
                bx2 = min(logo_img.width, bbox[2] + pad)
                by2 = min(logo_img.height, bbox[3] + pad)
                logo_img = logo_img.crop((bx1, by1, bx2, by2))
                
            # Convert near-white background pixels to alpha = 0 (transparent)
            datas = logo_img.getdata()
            newData = []
            for item in datas:
                # If pixel is near-white (channels > 240)
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            logo_img.putdata(newData)
            
            # Return resized logo
            return logo_img.resize((size, size), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"⚠️ Error loading custom logo image: {e}")
            
    # Fallback to drawing if logo file is missing
    logo_size = size * 2
    overlay = Image.new("RGBA", (logo_size, logo_size), (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    
    if is_dark_mode:
        bg_color = (22, 27, 34, 255)
        content_color = (121, 192, 255, 255)
        border_color = (121, 192, 255, 255)
    else:
        bg_color = (255, 255, 255, 255)
        content_color = (20, 60, 220, 255)
        border_color = (20, 60, 220, 255)
        
    border_w = max(2, int(logo_size * 0.06))
    ol_draw.ellipse([(border_w//2, border_w//2), (logo_size - border_w//2, logo_size - border_w//2)], fill=bg_color, outline=border_color, width=border_w)
    
    font_size = int(logo_size * 0.45)
    font = find_font(font_size, style="bold")
    text = "RD"
    text_bbox = font.getbbox(text)
    w = text_bbox[2] - text_bbox[0]
    h = text_bbox[3] - text_bbox[1]
    
    tx = (logo_size - w) // 2 - int(logo_size * 0.05)
    ty = (logo_size - h) // 2 - int(logo_size * 0.08)
    ol_draw.text((tx, ty), text, fill=content_color, font=font)
    
    arrow_w = int(logo_size * 0.08)
    ax1, ay1 = int(logo_size * 0.75), int(logo_size * 0.75)
    ax2, ay2 = int(logo_size * 0.9), int(logo_size * 0.25)
    ol_draw.line([(ax1, ay1), (ax2, ay2)], fill=content_color, width=arrow_w)
    
    ol_draw.polygon([
        (ax2, ay2),
        (ax2 - int(logo_size*0.2), ay2),
        (ax2, ay2 + int(logo_size*0.2))
    ], fill=content_color)
    
    return overlay.resize((size, size), Image.Resampling.LANCZOS)

def parse_hex_color(hex_str, default=(20, 60, 220)):
    """Converts hex color string to RGB tuple."""
    if not hex_str:
        return default
    hex_str = hex_str.strip().lstrip("#")
    try:
        if len(hex_str) == 6:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        elif len(hex_str) == 3:
            return (int(hex_str[0]*2, 16), int(hex_str[1]*2, 16), int(hex_str[2]*2, 16))
    except Exception:
        pass
    return default

def draw_abstract_header(img, width, height, primary_color, secondary_color, icon_text):
    """Draws a premium, modern abstract header with a custom gradient, geometric waves, and a central topic icon."""
    draw = ImageDraw.Draw(img)
    
    # 1. Draw smooth linear gradient background on base image
    for y in range(height):
        ratio = y / height
        r = int(primary_color[0] + (secondary_color[0] - primary_color[0]) * ratio)
        g = int(primary_color[1] + (secondary_color[1] - primary_color[1]) * ratio)
        b = int(primary_color[2] + (secondary_color[2] - primary_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # 2. Draw overlay shapes with alpha blending
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    
    circle_color = (255, 255, 255, 30) # translucent white
    ol_draw.arc([-200, -200, 600, 600], start=0, end=360, fill=circle_color, width=2)
    ol_draw.arc([-100, -100, 500, 500], start=0, end=360, fill=circle_color, width=4)
    ol_draw.arc([400, -200, 1200, 600], start=0, end=360, fill=circle_color, width=3)
    ol_draw.arc([300, -100, 1100, 500], start=0, end=360, fill=circle_color, width=5)
    
    grid_color = (255, 255, 255, 12)
    for x in range(0, width, 50):
        ol_draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 50):
        ol_draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
    # 3. Draw a glowing central circle badge
    cx, cy = width // 2, height // 2
    r = 75
    ol_draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(255, 255, 255, 240))
    ol_draw.ellipse([(cx - r - 8, cy - r - 8), (cx + r + 8, cy + r + 8)], outline=(255, 255, 255, 80), width=4)
    
    # Paste overlay
    img.paste(overlay, (0, 0), overlay)
    
    # 4. Draw symbol inside circle using Apple Color Emoji if available, fallback to Arial
    if not icon_text:
        icon_text = "💡"
        
    emoji_paths = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc"
    ]
    font = None
    is_emoji = False
    
    for p in emoji_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 96) # Apple Color Emoji requires specific bitmap sizes like 96
                is_emoji = True
                break
            except Exception:
                continue
                
    if not font:
        font = find_font(85, style="regular")
        
    bbox = font.getbbox(icon_text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    main_draw = ImageDraw.Draw(img)
    if is_emoji:
        # Use embedded_color=True to render full-color emoji bitmaps from the font file
        main_draw.text((cx - w//2 - 2, cy - h//2 - 10), icon_text, font=font, embedded_color=True)
    else:
        main_draw.text((cx - w//2 - 2, cy - h//2 - 10), icon_text, fill=(17, 28, 58), font=font)

def draw_structured_infographic(data, output_filename):
    """Draws a multi-point structured infographic with dynamic height and custom color theme."""
    width = 1000
    
    # Parse theme colors
    p_color = parse_hex_color(data.get("primary_color", ""), default=(20, 60, 220))
    s_color = parse_hex_color(data.get("secondary_color", ""), default=(88, 50, 226))
    bg_color = parse_hex_color(data.get("background_color", ""), default=(248, 249, 252))
    icon = data.get("illustration_icon", "💡")
    
    # 1. Calculate height dynamically
    title_text = data.get("card_title", "")
    title_font = find_font(34, style="bold")
    title_lines = wrap_text(title_text, title_font, 800)
    title_h = len(title_lines) * 42
    
    points_start_y = 525 + title_h + 55
    points = data.get("card_points", [])
    points_h = len(points) * 65
    points_end_y = points_start_y + points_h
    
    takeaway_text = data.get("card_takeaway", "")
    takeaway_val_font = find_font(15, style="italic")
    takeaway_lines = wrap_text(takeaway_text, takeaway_val_font, 740)
    takeaway_h = 38 + len(takeaway_lines) * 22 + 20 if takeaway_text else 0
    
    takeaway_y = points_end_y + 30
    takeaway_end_y = takeaway_y + takeaway_h if takeaway_text else points_end_y
    
    footer_y = takeaway_end_y + 40
    height = footer_y + 100
    
    # Create Canvas
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw dynamic abstract header
    draw_abstract_header(img, width, 450, p_color, s_color, icon)
        
    # Draw Category Header
    cat_text = data.get("card_category", "DAILY INSIGHT").upper()
    cat_font = find_font(18, style="bold")
    cat_bbox = cat_font.getbbox(cat_text)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.text(((width - cat_w) // 2, 490), cat_text, fill=p_color, font=cat_font)
    
    # Draw Main Title
    curr_y = 525
    for t_line in title_lines:
        line_bbox = title_font.getbbox(t_line)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_w) // 2, curr_y), t_line, fill=(17, 28, 58), font=title_font)
        curr_y += 42
        
    # Draw Subtitle
    sub_text = data.get("card_subtitle", "")
    sub_font = find_font(22, style="bold")
    draw.text((100, curr_y + 15), sub_text, fill=s_color, font=sub_font)
    
    # Draw Points
    p_title_font = find_font(19, style="bold")
    p_desc_font = find_font(15, style="regular")
    curr_y = points_start_y
    
    for i, pt in enumerate(points):
        circle_d = 30
        cx, cy = 100, curr_y
        draw.ellipse([(cx, cy), (cx + circle_d, cy + circle_d)], outline=p_color, width=2)
        
        num_str = str(i + 1)
        num_bbox = p_title_font.getbbox(num_str)
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text((cx + (circle_d - num_w)//2, cy + (circle_d - num_h)//2 - 2), num_str, fill=p_color, font=p_title_font)
        
        draw.text((150, curr_y), pt.get("title", ""), fill=(17, 28, 58), font=p_title_font)
        draw.text((150, curr_y + 24), pt.get("description", ""), fill=(110, 124, 156), font=p_desc_font)
        curr_y += 65
        
    # Draw Takeaway Box
    if takeaway_text:
        draw.rounded_rectangle([(100, takeaway_y), (900, takeaway_y + takeaway_h - 10)], radius=6, fill=(255, 255, 255))
        draw.line([(100, takeaway_y), (100, takeaway_y + takeaway_h - 10)], fill=p_color, width=6)
        
        takeaway_lbl_font = find_font(14, style="bold")
        draw.text((120, takeaway_y + 15), "KEY TAKEAWAY", fill=p_color, font=takeaway_lbl_font)
        
        ty = takeaway_y + 38
        for t_val_line in takeaway_lines:
            draw.text((120, ty), t_val_line, fill=(17, 28, 58), font=takeaway_val_font)
            ty += 22
            
    # Branded Footer
    draw.line([(100, footer_y), (900, footer_y)], fill=(225, 230, 235), width=1)
    
    site_font = find_font(17, style="bold")
    draw.text((100, footer_y + 35), "ratnamdigital.com", fill=p_color, font=site_font)
    
    logo_lbl_font = find_font(15, style="bold")
    logo_sub_font = find_font(10, style="regular")
    draw.text((680, footer_y + 30), "RATNAM DIGITAL", fill=(17, 28, 58), font=logo_lbl_font)
    draw.text((680, footer_y + 48), "AI · AUTOMATION · GROWTH", fill=(110, 124, 156), font=logo_sub_font)
    
    logo_img = draw_logo_badge(45)
    img.paste(logo_img, (855, footer_y + 20), logo_img.convert("RGBA"))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    img.save(output_path, "PNG")
    return output_path

def draw_syntax_highlighted_code(draw, font_reg, font_bold, text, start_x, start_y):
    """Renders programming code inside the Carbon window with syntax coloring."""
    keywords = {"def", "class", "import", "from", "return", "const", "let", "function", "var", "if", "else", "for", "while", "in", "import", "as", "async", "await", "try", "except"}
    lines = text.split("\n")
    curr_y = start_y
    line_h = font_reg.getbbox("A")[3] - font_reg.getbbox("A")[1] + 8
    
    for i, line in enumerate(lines):
        # Draw line number
        num_str = f"{i+1:2d} "
        draw.text((start_x - 50, curr_y), num_str, fill=(72, 79, 88), font=font_reg)
        
        words = line.split(" ")
        curr_x = start_x
        
        for w in words:
            if w.strip().startswith("#") or w.strip().startswith("//"):
                comment_part = " ".join(words[words.index(w):])
                draw.text((curr_x, curr_y), comment_part, fill=(139, 148, 158), font=font_reg)
                break
                
            clean_w = w.strip("():,;[]{}'\"")
            if clean_w in keywords:
                draw.text((curr_x, curr_y), w + " ", fill=(255, 123, 114), font=font_bold)
            elif w.startswith('"') or w.startswith("'") or w.endswith('"') or w.endswith("'"):
                draw.text((curr_x, curr_y), w + " ", fill=(126, 231, 135), font=font_reg)
            elif clean_w.isdigit():
                draw.text((curr_x, curr_y), w + " ", fill=(121, 192, 255), font=font_reg)
            else:
                draw.text((curr_x, curr_y), w + " ", fill=(230, 237, 243), font=font_reg)
                
            w_bbox = font_reg.getbbox(w + " ")
            w_width = w_bbox[2] - w_bbox[0]
            curr_x += w_width
            
        curr_y += line_h

def draw_code_snippet(data, output_filename):
    """Draws a Carbon-style IDE window displaying code snippets with dynamic height and dynamic accents."""
    width = 1000
    p_color = parse_hex_color(data.get("primary_color", ""), default=(121, 192, 255))
    
    # 1. Precalculate heights
    code_text = data.get("code_content", "")
    code_font_reg = find_font(18, style="regular")
    line_h = code_font_reg.getbbox("A")[3] - code_font_reg.getbbox("A")[1] + 8
    num_lines = len(code_text.split("\n"))
    
    code_h = num_lines * line_h + 110
    wy1 = 180
    wy2 = wy1 + code_h
    
    explanation = data.get("code_explanation", "")
    exp_font = find_font(18, style="regular")
    exp_lines = wrap_text(explanation, exp_font, 760)
    exp_h = len(exp_lines) * 26 if explanation else 0
    exp_y = wy2 + 40
    exp_end_y = exp_y + exp_h if explanation else wy2
    
    takeaway_text = data.get("card_takeaway", "")
    takeaway_val_font = find_font(15, style="italic")
    takeaway_lines = wrap_text(takeaway_text, takeaway_val_font, 740)
    takeaway_h = 38 + len(takeaway_lines) * 22 + 20 if takeaway_text else 0
    
    takeaway_y = exp_end_y + 30
    takeaway_end_y = takeaway_y + takeaway_h if takeaway_text else exp_end_y
    
    footer_y = takeaway_end_y + 40
    height = footer_y + 100
    
    # Create Canvas
    img = Image.new("RGB", (width, height), (13, 17, 23))
    draw = ImageDraw.Draw(img)
    
    # Draw Title
    title_font = find_font(34, style="bold")
    title_text = data.get("card_title", "Code Implementation")
    title_bbox = title_font.getbbox(title_text)
    tw = title_bbox[2] - title_bbox[0]
    draw.text(((width - tw) // 2, 80), title_text, fill=(230, 237, 243), font=title_font)
    
    # Draw Code Window Outline
    wx1, wx2 = 100, 900
    draw.rounded_rectangle([(wx1, wy1), (wx2, wy2)], radius=8, fill=(22, 27, 34), outline=(48, 54, 62), width=1)
    
    # Window Header Bar
    draw.rounded_rectangle([(wx1, wy1), (wx2, wy1 + 60)], radius=8, fill=(33, 38, 45))
    draw.rectangle([(wx1, wy1 + 45), (wx2, wy1 + 60)], fill=(33, 38, 45))
    
    # Header Dots (Red, Yellow, Green)
    dot_radius = 6
    dot_y = wy1 + 30
    draw.ellipse([(wx1 + 25 - dot_radius, dot_y - dot_radius), (wx1 + 25 + dot_radius, dot_y + dot_radius)], fill=(255, 95, 87))
    draw.ellipse([(wx1 + 45 - dot_radius, dot_y - dot_radius), (wx1 + 45 + dot_radius, dot_y + dot_radius)], fill=(255, 189, 46))
    draw.ellipse([(wx1 + 65 - dot_radius, dot_y - dot_radius), (wx1 + 65 + dot_radius, dot_y + dot_radius)], fill=(39, 201, 63))
    
    # Header Text
    header_font = find_font(16, style="regular")
    header_text = data.get("code_title", "main.py")
    h_bbox = header_font.getbbox(header_text)
    hw = h_bbox[2] - h_bbox[0]
    draw.text(((width - hw) // 2, wy1 + 20), header_text, fill=(139, 148, 158), font=header_font)
    
    # Draw Code Content
    code_font_bold = find_font(18, style="bold")
    draw_syntax_highlighted_code(draw, code_font_reg, code_font_bold, code_text, wx1 + 80, wy1 + 90)
    
    # Draw Caption Box
    if explanation:
        curr_y = exp_y
        for line in exp_lines:
            line_bbox = exp_font.getbbox(line)
            lw = line_bbox[2] - line_bbox[0]
            draw.text(((width - lw) // 2, curr_y), line, fill=(139, 148, 158), font=exp_font)
            curr_y += 26
            
    # Draw Takeaway
    if takeaway_text:
        draw.rounded_rectangle([(100, takeaway_y), (900, takeaway_y + takeaway_h - 10)], radius=6, fill=(25, 30, 45), outline=(48, 54, 62), width=1)
        draw.line([(100, takeaway_y), (100, takeaway_y + takeaway_h - 10)], fill=p_color, width=6)
        
        takeaway_lbl_font = find_font(14, style="bold")
        draw.text((120, takeaway_y + 15), "KEY TAKEAWAY", fill=p_color, font=takeaway_lbl_font)
        
        ty = takeaway_y + 38
        for t_val_line in takeaway_lines:
            draw.text((120, ty), t_val_line, fill=(230, 237, 243), font=takeaway_val_font)
            ty += 22
            
    # Branded Footer
    draw.line([(100, footer_y), (900, footer_y)], fill=(48, 54, 62), width=1)
    
    site_font = find_font(17, style="bold")
    draw.text((100, footer_y + 35), "ratnamdigital.com", fill=p_color, font=site_font)
    
    logo_lbl_font = find_font(15, style="bold")
    logo_sub_font = find_font(10, style="regular")
    draw.text((680, footer_y + 30), "RATNAM DIGITAL", fill=(230, 237, 243), font=logo_lbl_font)
    draw.text((680, footer_y + 48), "AI · AUTOMATION · GROWTH", fill=(139, 148, 158), font=logo_sub_font)
    
    logo_img = draw_logo_badge(45, is_dark_mode=True)
    img.paste(logo_img, (855, footer_y + 20), logo_img.convert("RGBA"))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    img.save(output_path, "PNG")
    return output_path

def draw_chart_graph(data, output_filename):
    """Draws a vertical vector chart with dynamic height and custom color theme."""
    width = 1000
    
    p_color = parse_hex_color(data.get("primary_color", ""), default=(20, 60, 220))
    s_color = parse_hex_color(data.get("secondary_color", ""), default=(88, 50, 226))
    bg_color = parse_hex_color(data.get("background_color", ""), default=(248, 249, 252))
    icon = data.get("illustration_icon", "📈")
    
    # 1. Precalculate height
    title_text = data.get("card_title", "Performance Analysis")
    title_font = find_font(34, style="bold")
    title_lines = wrap_text(title_text, title_font, 800)
    title_h = len(title_lines) * 42
    
    chart_y = 525 + title_h + 60
    chart_h = 420
    ax_y = chart_y + chart_h
    
    takeaway_text = data.get("card_takeaway", "")
    takeaway_val_font = find_font(15, style="italic")
    takeaway_lines = wrap_text(takeaway_text, takeaway_val_font, 740)
    takeaway_h = 38 + len(takeaway_lines) * 22 + 20 if takeaway_text else 0
    
    takeaway_y = ax_y + 40
    takeaway_end_y = takeaway_y + takeaway_h if takeaway_text else ax_y + 20
    
    footer_y = takeaway_end_y + 40
    height = footer_y + 100
    
    # Create Canvas
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw top header
    draw_abstract_header(img, width, 450, p_color, s_color, icon)
    
    # Draw Category Header
    cat_text = "DATA INSIGHT"
    cat_font = find_font(18, style="bold")
    cat_bbox = cat_font.getbbox(cat_text)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.text(((width - cat_w) // 2, 490), cat_text, fill=p_color, font=cat_font)
    
    # Draw Title
    for i, t_line in enumerate(title_lines):
        line_bbox = title_font.getbbox(t_line)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_w) // 2, 525 + i * 42), t_line, fill=(17, 28, 58), font=title_font)
        
    # Setup Axes
    ax_x = 200
    ax_w = 700
    
    draw.line([(ax_x, chart_y), (ax_x, ax_y)], fill=(110, 124, 156), width=2)
    draw.line([(ax_x, ax_y), (ax_x + ax_w, ax_y)], fill=(110, 124, 156), width=2)
    
    labels = data.get("chart_labels", [])
    values = data.get("chart_values", [])
    
    if not values:
        labels, values = ["Sample A", "Sample B", "Sample C"], [50, 80, 30]
        
    max_val = max(values) if values else 100
    scale = (chart_h - 100) / max_val
    
    # Grid lines
    y_font = find_font(14, style="regular")
    for val_step in [0, max_val * 0.25, max_val * 0.5, max_val * 0.75, max_val]:
        step_y = ax_y - int(val_step * scale)
        draw.line([(ax_x, step_y), (ax_x + ax_w, step_y)], fill=(225, 230, 235), width=1)
        draw.text((ax_x - 60, step_y - 8), f"{int(val_step)}", fill=(110, 124, 156), font=y_font)
        
    chart_type = data.get("chart_type", "bar")
    if chart_type == "line":
        num_points = len(values)
        pt_gap = ax_w // (num_points - 1) if num_points > 1 else ax_w
        coords = []
        for i, val in enumerate(values):
            coords.append((ax_x + i * pt_gap, ax_y - int(val * scale)))
            
        if len(coords) > 1:
            draw.line(coords, fill=p_color, width=4)
            
        pt_font = find_font(15, style="bold")
        for i, ((px, py), lbl, val) in enumerate(zip(coords, labels, values)):
            r = 6
            draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=s_color, outline=(255, 255, 255), width=2)
            
            val_str = str(val)
            val_bbox = pt_font.getbbox(val_str)
            vw = val_bbox[2] - val_bbox[0]
            draw.text((px - vw//2, py - 25), val_str, fill=(17, 28, 58), font=pt_font)
            
            lbl_bbox = pt_font.getbbox(lbl)
            lw = lbl_bbox[2] - lbl_bbox[0]
            draw.text((px - lw//2, ax_y + 15), lbl, fill=(110, 124, 156), font=pt_font)
    else:
        num_bars = len(values)
        bar_gap = 40
        total_gaps_w = bar_gap * (num_bars + 1)
        bar_w = (ax_w - total_gaps_w) // num_bars
        
        lbl_font = find_font(15, style="bold")
        val_font = find_font(15, style="bold")
        
        for i, (lbl, val) in enumerate(zip(labels, values)):
            bx1 = ax_x + bar_gap + i * (bar_w + bar_gap)
            bx2 = bx1 + bar_w
            by1 = ax_y - int(val * scale)
            by2 = ax_y
            
            color = p_color if val == max_val else s_color
            draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=4, fill=color)
            
            val_str = str(val)
            val_bbox = val_font.getbbox(val_str)
            vw = val_bbox[2] - val_bbox[0]
            draw.text((bx1 + (bar_w - vw)//2, by1 - 25), val_str, fill=(17, 28, 58), font=val_font)
            
            lbl_lines = wrap_text(lbl, lbl_font, bar_w + 20)
            ly = ax_y + 15
            for line in lbl_lines:
                line_bbox = lbl_font.getbbox(line)
                lw = line_bbox[2] - line_bbox[0]
                draw.text((bx1 + (bar_w - lw)//2, ly), line, fill=(110, 124, 156), font=lbl_font)
                ly += 20
                
    # Draw Takeaway
    if takeaway_text:
        draw.rounded_rectangle([(100, takeaway_y), (900, takeaway_y + takeaway_h - 10)], radius=6, fill=(255, 255, 255))
        draw.line([(100, takeaway_y), (100, takeaway_y + takeaway_h - 10)], fill=p_color, width=6)
        
        takeaway_lbl_font = find_font(14, style="bold")
        draw.text((120, takeaway_y + 15), "KEY TAKEAWAY", fill=p_color, font=takeaway_lbl_font)
        
        ty = takeaway_y + 38
        for t_val_line in takeaway_lines:
            draw.text((120, ty), t_val_line, fill=(17, 28, 58), font=takeaway_val_font)
            ty += 22
            
    # Footer
    draw.line([(100, footer_y), (900, footer_y)], fill=(225, 230, 235), width=1)
    
    site_font = find_font(17, style="bold")
    draw.text((100, footer_y + 35), "ratnamdigital.com", fill=p_color, font=site_font)
    
    logo_lbl_font = find_font(15, style="bold")
    logo_sub_font = find_font(10, style="regular")
    draw.text((680, footer_y + 30), "RATNAM DIGITAL", fill=(17, 28, 58), font=logo_lbl_font)
    draw.text((680, footer_y + 48), "AI · AUTOMATION · GROWTH", fill=(110, 124, 156), font=logo_sub_font)
    
    logo_img = draw_logo_badge(45)
    img.paste(logo_img, (855, footer_y + 20), logo_img.convert("RGBA"))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    img.save(output_path, "PNG")
    return output_path

def draw_comparison_table(data, output_filename):
    """Draws a clean comparison table card with dynamic height and custom color theme."""
    width = 1000
    
    p_color = parse_hex_color(data.get("primary_color", ""), default=(20, 60, 220))
    s_color = parse_hex_color(data.get("secondary_color", ""), default=(88, 50, 226))
    bg_color = parse_hex_color(data.get("background_color", ""), default=(248, 249, 252))
    icon = data.get("illustration_icon", "📊")
    
    # 1. Precalculate dynamic height
    title_text = data.get("card_title", "Comparison Analysis")
    title_font = find_font(34, style="bold")
    title_lines = wrap_text(title_text, title_font, 800)
    title_h = len(title_lines) * 42
    
    table_y = 525 + title_h + 60
    rows = data.get("table_rows", [["Performance", "Slower", "10x Faster"]])
    row_h = 70
    table_h = row_h * (len(rows) + 1)
    table_end_y = table_y + table_h
    
    takeaway_text = data.get("card_takeaway", "")
    takeaway_val_font = find_font(15, style="italic")
    takeaway_lines = wrap_text(takeaway_text, takeaway_val_font, 740)
    takeaway_h = 38 + len(takeaway_lines) * 22 + 20 if takeaway_text else 0
    
    takeaway_y = table_end_y + 30
    takeaway_end_y = takeaway_y + takeaway_h if takeaway_text else table_end_y
    
    footer_y = takeaway_end_y + 40
    height = footer_y + 100
    
    # Create Canvas
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw top header
    draw_abstract_header(img, width, 450, p_color, s_color, icon)
    
    # Draw Category Header
    cat_text = "COMPARATIVE DEEP DIVE"
    cat_font = find_font(18, style="bold")
    cat_bbox = cat_font.getbbox(cat_text)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.text(((width - cat_w) // 2, 490), cat_text, fill=p_color, font=cat_font)
    
    # Draw Title
    for i, t_line in enumerate(title_lines):
        line_bbox = title_font.getbbox(t_line)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_w) // 2, 525 + i * 42), t_line, fill=(17, 28, 58), font=title_font)
        
    # Table Outline
    start_x = 100
    table_w = 800
    headers = data.get("table_headers", ["Feature", "Standard", "Optimized"])
    
    num_cols = len(headers)
    col_w = table_w // num_cols
    
    # Header Row Fill with primary color
    draw.rectangle([(start_x, table_y), (start_x + table_w, table_y + row_h)], fill=p_color)
    
    h_font = find_font(18, style="bold")
    for col_idx, h_text in enumerate(headers):
        cx1 = start_x + col_idx * col_w
        h_bbox = h_font.getbbox(h_text)
        hw = h_bbox[2] - h_bbox[0]
        hh = h_bbox[3] - h_bbox[1]
        draw.text((cx1 + (col_w - hw)//2, table_y + (row_h - hh)//2), h_text, fill=(255, 255, 255), font=h_font)
        
    body_font = find_font(16, style="regular")
    bold_body_font = find_font(16, style="bold")
    curr_y = table_y + row_h
    
    for row_idx, r_data in enumerate(rows):
        row_bg = (255, 255, 255) if row_idx % 2 == 0 else bg_color
        draw.rectangle([(start_x, curr_y), (start_x + table_w, curr_y + row_h)], fill=row_bg)
        
        for col_idx, cell_val in enumerate(r_data):
            if col_idx >= num_cols:
                break
            cx1 = start_x + col_idx * col_w
            
            cell_font = bold_body_font if col_idx == 0 else body_font
            cell_color = (17, 28, 58)
            
            cell_lines = wrap_text(cell_val, cell_font, col_w - 30)
            text_h = len(cell_lines) * 20
            ty = curr_y + (row_h - text_h)//2
            
            for line in cell_lines:
                line_bbox = cell_font.getbbox(line)
                lw = line_bbox[2] - line_bbox[0]
                tx = cx1 + 15 if col_idx == 0 else cx1 + (col_w - lw)//2
                draw.text((tx, ty), line, fill=cell_color, font=cell_font)
                ty += 20
                
        draw.line([(start_x, curr_y + row_h), (start_x + table_w, curr_y + row_h)], fill=(225, 230, 235), width=1)
        curr_y += row_h
        
    # Vertical grid dividers
    for col_idx in range(1, num_cols):
        cx = start_x + col_idx * col_w
        draw.line([(cx, table_y), (cx, curr_y)], fill=(225, 230, 235), width=1)
        
    # Draw Takeaway
    if takeaway_text:
        draw.rounded_rectangle([(100, takeaway_y), (900, takeaway_y + takeaway_h - 10)], radius=6, fill=(255, 255, 255))
        draw.line([(100, takeaway_y), (100, takeaway_y + takeaway_h - 10)], fill=p_color, width=6)
        
        takeaway_lbl_font = find_font(14, style="bold")
        draw.text((120, takeaway_y + 15), "KEY TAKEAWAY", fill=p_color, font=takeaway_lbl_font)
        
        ty = takeaway_y + 38
        for t_val_line in takeaway_lines:
            draw.text((120, ty), t_val_line, fill=(17, 28, 58), font=takeaway_val_font)
            ty += 22
            
    # Footer
    draw.line([(100, footer_y), (900, footer_y)], fill=(225, 230, 235), width=1)
    
    site_font = find_font(17, style="bold")
    draw.text((100, footer_y + 35), "ratnamdigital.com", fill=p_color, font=site_font)
    
    logo_lbl_font = find_font(15, style="bold")
    logo_sub_font = find_font(10, style="regular")
    draw.text((680, footer_y + 30), "RATNAM DIGITAL", fill=(17, 28, 58), font=logo_lbl_font)
    draw.text((680, footer_y + 48), "AI · AUTOMATION · GROWTH", fill=(110, 124, 156), font=logo_sub_font)
    
    logo_img = draw_logo_badge(45)
    img.paste(logo_img, (855, footer_y + 20), logo_img.convert("RGBA"))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    img.save(output_path, "PNG")
    return output_path

def draw_single_quote_infographic(text, output_filename):
    """Draws a simple quote template graphic fallback with dynamic height."""
    width = 1000
    
    content_font = find_font(34, style="bold")
    max_text_width = 750
    lines = wrap_text(text, content_font, max_text_width)
    line_spacing = 15
    line_height = content_font.getbbox("A")[3] - content_font.getbbox("A")[1]
    total_text_height = (len(lines) * line_height) + ((len(lines) - 1) * line_spacing)
    
    text_start_y = 500
    text_end_y = text_start_y + total_text_height + 40
    
    box_y = text_end_y + 20
    box_h = 110
    
    footer_y = box_y + box_h + 40
    height = footer_y + 100
    
    # Create Canvas
    img = Image.new("RGB", (width, height), (248, 249, 252))
    draw = ImageDraw.Draw(img)
    
    draw_abstract_header(img, width, 450, (20, 60, 220), (88, 50, 226), "💡")
        
    cat_text = "DAILY INSIGHT"
    cat_font = find_font(18, style="bold")
    cat_bbox = cat_font.getbbox(cat_text)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.text(((width - cat_w) // 2, 500), cat_text, fill=(20, 60, 220), font=cat_font)
    
    quote_font = find_font(260, style="bold")
    draw.text((100, 530), "“", fill=(225, 230, 245), font=quote_font)
    
    start_y = text_start_y
    for i, line in enumerate(lines):
        line_bbox = content_font.getbbox(line)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_w) // 2, start_y + i * (line_height + line_spacing)), line, fill=(17, 28, 58), font=content_font)
        
    draw.rounded_rectangle([(100, box_y), (900, box_y + box_h - 10)], radius=6, fill=(255, 255, 255))
    draw.line([(100, box_y), (100, box_y + box_h - 10)], fill=(20, 60, 220), width=6)
    
    takeaway_lbl_font = find_font(14, style="bold")
    draw.text((120, box_y + 15), "KEY TAKEAWAY", fill=(20, 60, 220), font=takeaway_lbl_font)
    
    takeaway_val_font = find_font(15, style="italic")
    takeaway_lines = wrap_text("Social media rewards consistency and genuine value.", takeaway_val_font, 740)
    ty = box_y + 38
    for t_val_line in takeaway_lines:
        draw.text((120, ty), t_val_line, fill=(17, 28, 58), font=takeaway_val_font)
        ty += 22
        
    draw.line([(100, footer_y), (900, footer_y)], fill=(225, 230, 235), width=1)
    
    site_font = find_font(17, style="bold")
    draw.text((100, footer_y + 35), "ratnamdigital.com", fill=(20, 60, 220), font=site_font)
    
    logo_lbl_font = find_font(15, style="bold")
    logo_sub_font = find_font(10, style="regular")
    draw.text((680, footer_y + 30), "RATNAM DIGITAL", fill=(17, 28, 58), font=logo_lbl_font)
    draw.text((680, footer_y + 48), "AI · AUTOMATION · GROWTH", fill=(110, 124, 156), font=logo_sub_font)
    
    logo_img = draw_logo_badge(45)
    img.paste(logo_img, (855, footer_y + 20), logo_img.convert("RGBA"))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
    img.save(output_path, "PNG")
    return output_path

def create_quote_card(text, output_filename="temp_post_image.png"):
    """Generates a professional infographic, code snippet, chart, table, or fallback card."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            layout = data.get("layout_type", "infographic")
            if layout == "code_snippet":
                return draw_code_snippet(data, output_filename)
            elif layout == "chart_graph":
                return draw_chart_graph(data, output_filename)
            elif layout == "comparison_table":
                return draw_comparison_table(data, output_filename)
            elif layout == "infographic":
                return draw_structured_infographic(data, output_filename)
    except Exception as e:
        print(f"ℹ️ Single quote format fallback (failed to parse layout): {e}")
        
    return draw_single_quote_infographic(text, output_filename)

if __name__ == "__main__":
    test_code = {
        "layout_type": "code_snippet",
        "card_title": "React performance optimizer",
        "code_title": "optimizeRenders.js",
        "code_content": (
            "import React, { useMemo } from 'react';\n\n"
            "const ComplexComponent = ({ items, filter }) => {\n"
            "  // Caching filtered list to avoid re-runs\n"
            "  const filteredItems = useMemo(() => {\n"
            "    return items.filter(item => item.includes(filter));\n"
            "  }, [items, filter]);\n\n"
            "  return <ul>{filteredItems.map(x => <li>{x}</li>)}</ul>;\n"
            "};\n"
        ),
        "code_explanation": "Use useMemo hook to cache arrays/objects and prevent deep execution loops."
    }
    create_quote_card(json.dumps(test_code), "temp_test_code.png")
