import os
import requests
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

def get_headers(token):
    """Generates the standard headers required for LinkedIn's Versioned REST API."""
    return {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202607",  # REST API Version
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

def publish_to_linkedin(commentary, image_path, token=None, person_urn=None):
    """
    Publishes a text commentary and an image to the authenticated member's LinkedIn feed.
    Follows the modern 3-step Images API and Posts API flow.
    """
    token = token or os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = person_urn or os.getenv("LINKEDIN_PERSON_URN")
    
    if not token or not person_urn:
        raise ValueError(
            "❌ Missing LinkedIn credentials.\n"
            "Please authenticate with LinkedIn first via the dashboard."
        )
        
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Image file not found at: {image_path}")

    # =========================================================================
    # STEP 1: Initialize Image Upload
    # =========================================================================
    print("🎬 Step 1: Initializing image upload on LinkedIn...")
    init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    init_payload = {
        "initializeUploadRequest": {
            "owner": person_urn
        }
    }
    
    try:
        init_response = requests.post(init_url, headers=get_headers(token), json=init_payload)
        init_response.raise_for_status()
        init_data = init_response.json()
        
        value = init_data.get("value", {})
        upload_url = value.get("uploadUrl")
        if not upload_url:
            upload_url = value.get("uploadMechanism", {}).get(
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
            ).get("uploadUrl")
        image_urn = value.get("image")
        
        if not upload_url or not image_urn:
            raise ValueError(f"Failed to parse upload URL or image URN from response: {init_data}")
            
        print(f"✅ Image upload initialized. URN: {image_urn}")
        
    except requests.exceptions.RequestException as e:
        print("❌ Error initializing upload. Check if token is valid or expired.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.status_code} - {e.response.text}")
        raise e

    # =========================================================================
    # STEP 2: Upload Binary Image
    # =========================================================================
    print("📤 Step 2: Uploading image binary...")
    try:
        with open(image_path, "rb") as img_file:
            binary_data = img_file.read()
            
        # LinkedIn binary upload requires PUT, Authorization header and content-type
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/png"
        }
        
        upload_response = requests.put(upload_url, headers=upload_headers, data=binary_data)
        upload_response.raise_for_status()
        print("✅ Image binary uploaded successfully.")
        
    except requests.exceptions.RequestException as e:
        print("❌ Error uploading image binary.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.status_code} - {e.response.text}")
        raise e

    # =========================================================================
    # STEP 3: Create the LinkedIn Post
    # =========================================================================
    print("📝 Step 3: Creating the post feed share...")
    post_url = "https://api.linkedin.com/rest/posts"
    post_payload = {
        "author": person_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED"
        },
        "content": {
            "media": {
                "id": image_urn,
                "altText": "Automated professional insights graphic card"
            }
        },
        "lifecycleState": "PUBLISHED"
    }
    
    try:
        post_response = requests.post(post_url, headers=get_headers(token), json=post_payload)
        post_response.raise_for_status()
        
        # In RestLi, successful POST returns 201 Created and the URN is in 'x-restli-id' header
        post_urn = post_response.headers.get("x-restli-id", "Unknown URN")
        print("\n" + "="*60)
        print("🎉 POST PUBLISHED SUCCESSFULLY TO LINKEDIN!")
        print("="*60)
        print(f"Post URN: {post_urn}")
        print("="*60)
        return post_urn
        
    except requests.exceptions.RequestException as e:
        print("❌ Error creating post.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.status_code} - {e.response.text}")
        raise e
