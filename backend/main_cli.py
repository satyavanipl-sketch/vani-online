import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load env variables
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

from content_generator import generate_post_content, create_quote_card
from publisher import publish_to_linkedin

LOG_FILE = os.path.join(os.path.dirname(__file__), "autoposter.log")

def write_log(message):
    """Appends an execution message with a timestamp to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    print(log_entry.strip())

def main():
    parser = argparse.ArgumentParser(description="Autonomous LinkedIn Post Generator & Publisher")
    parser.add_argument(
        "--test-generation", 
        action="store_true", 
        help="Generate text and the visual card locally without publishing to LinkedIn"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Verify environment keys and run generation but do not publish to LinkedIn"
    )
    args = parser.parse_args()

    write_log("▶️ Autoposter execution started.")

    try:
        # 1. Generate text and graphical quote card content
        post_data = generate_post_content()
        commentary = post_data["commentary"]
        card_text = post_data["card_text"]

        write_log(f"📝 Content generated: '{card_text}'")

        # 2. Draw card image
        image_path = create_quote_card(card_text)
        write_log(f"🎨 Graphical card saved to: {image_path}")

        if args.test_generation:
            write_log("✨ Test-generation complete. Skipping LinkedIn publishing as requested.")
            print("\n--- GENERATED POST COMMENTARY ---")
            print(commentary)
            print("---------------------------------\n")
            return

        # 3. Check credentials for publication
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = os.getenv("LINKEDIN_PERSON_URN")

        if not token or not person_urn:
            write_log("❌ Error: LinkedIn credentials not found in .env.")
            print("\nPlease run 'python3 auth.py' to authenticate with LinkedIn first.")
            sys.exit(1)

        if args.dry_run:
            write_log("✨ Dry-run complete. Credentials validated, skipping LinkedIn publishing.")
            print("\n--- GENERATED POST COMMENTARY ---")
            print(commentary)
            print("---------------------------------\n")
            return

        # 4. Publish to LinkedIn
        post_urn = publish_to_linkedin(commentary, image_path)
        write_log(f"🚀 Success! Posted to LinkedIn. URN: {post_urn}")

    except Exception as e:
        error_msg = f"💥 Execution failed with error: {e}"
        write_log(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
