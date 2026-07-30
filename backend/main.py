import os
import sys
import json
import uuid
import base64
import asyncio
import urllib.parse
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Body, responses
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_post_content, create_quote_card
from publisher import publish_to_linkedin

app = FastAPI(
    title="LinkedIn Autoposter Web App API",
    description="Backend service managing credentials, adhoc drafting, post styling, schedules, and publication logs."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.json")

# =========================================================================
# Database Managers
# =========================================================================

def load_db():
    if not os.path.exists(DB_PATH):
        initial_data = {
            "credentials": {
                "linkedin_client_id": "",
                "linkedin_client_secret": "",
                "linkedin_redirect_uri": "http://localhost:8002/api/callback",
                "linkedin_access_token": "",
                "linkedin_person_urn": "",
                "linkedin_member_name": "",
                "gemini_api_key": ""
            },
            "schedules": [],
            "logs": []
        }
        save_db(initial_data)
        return initial_data
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "credentials": {},
            "schedules": [],
            "logs": []
        }

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

# =========================================================================
# Pydantic Schemas
# =========================================================================

class ConfigModel(BaseModel):
    linkedin_client_id: Optional[str] = ""
    linkedin_client_secret: Optional[str] = ""
    gemini_api_key: Optional[str] = ""
    linkedin_person_urn: Optional[str] = ""
    linkedin_member_name: Optional[str] = ""

class DraftRequest(BaseModel):
    topic: str
    commentary: Optional[str] = None
    card_text: Optional[str] = None

class PublishAdhocRequest(BaseModel):
    commentary: str
    card_text: str

class CreateScheduleRequest(BaseModel):
    topic: str
    scheduled_time: str # ISO string
    commentary: Optional[str] = None
    card_text: Optional[str] = None

class UpdateScheduleRequest(BaseModel):
    scheduled_time: str
    commentary: str
    card_text: str

# =========================================================================
# REST Endpoints
# =========================================================================

@app.get("/api/status")
def get_status():
    db = load_db()
    creds = db.get("credentials", {})
    schedules = db.get("schedules", [])
    
    return {
        "status": "online",
        "linkedin_connected": bool(creds.get("linkedin_access_token")),
        "linkedin_member_name": creds.get("linkedin_member_name", ""),
        "linkedin_person_urn": creds.get("linkedin_person_urn", ""),
        "gemini_configured": bool(creds.get("gemini_api_key")),
        "client_id_configured": bool(creds.get("linkedin_client_id")),
        "client_secret_configured": bool(creds.get("linkedin_client_secret")),
        "active_schedules_count": len([s for s in schedules if s["status"] == "pending"])
    }

@app.post("/api/config")
def save_config(config: ConfigModel):
    db = load_db()
    if config.linkedin_client_id and config.linkedin_client_id.strip():
        db["credentials"]["linkedin_client_id"] = config.linkedin_client_id.strip()
    if config.linkedin_client_secret and config.linkedin_client_secret.strip():
        db["credentials"]["linkedin_client_secret"] = config.linkedin_client_secret.strip()
    if config.gemini_api_key and config.gemini_api_key.strip():
        db["credentials"]["gemini_api_key"] = config.gemini_api_key.strip()
    
    db["credentials"]["linkedin_person_urn"] = config.linkedin_person_urn.strip()
    db["credentials"]["linkedin_member_name"] = config.linkedin_member_name.strip()
    save_db(db)
    return {"status": "success", "message": "Configuration saved successfully."}

@app.get("/api/auth-url")
def get_auth_url(redirect_back: Optional[str] = "http://localhost:5173", scope_mode: Optional[str] = "openid"):
    db = load_db()
    creds = db.get("credentials", {})
    client_id = creds.get("linkedin_client_id")
    redirect_uri = creds.get("linkedin_redirect_uri", "http://localhost:8002/api/callback")
    
    if not client_id:
        raise HTTPException(status_code=400, detail="LinkedIn Client ID not configured in settings.")
        
    # Store the frontend url and scope mode to use after oauth callback
    db["credentials"]["linkedin_redirect_back"] = redirect_back
    db["credentials"]["linkedin_scope_mode"] = scope_mode
    save_db(db)
    
    scope = "w_member_social"
    if scope_mode == "openid":
        scope = "w_member_social openid profile"
        
    import secrets
    state = secrets.token_hex(16)
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(auth_params)}"
    return {"auth_url": url}

@app.get("/api/callback")
async def oauth_callback(code: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None, state: Optional[str] = None):
    if error or not code:
        err_msg = error_description or error or "Missing authorization code from LinkedIn."
        return responses.HTMLResponse(content=f"<h2>LinkedIn Authorization Failed</h2><p>{err_msg}</p>", status_code=400)

    db = load_db()
    creds = db.get("credentials", {})
    client_id = creds.get("linkedin_client_id")
    client_secret = creds.get("linkedin_client_secret")
    redirect_uri = creds.get("linkedin_redirect_uri", "http://localhost:8002/api/callback")
    scope_mode = creds.get("linkedin_scope_mode", "openid")
    
    if not client_id or not client_secret:
        return responses.HTMLResponse(content="<h2>Error: Missing Client ID/Secret in DB configuration.</h2>", status_code=400)
        
    # Exchange authorization code for access token
    import requests
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        resp = requests.post(token_url, data=token_data, timeout=10)
        resp.raise_for_status()
        token_info = resp.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            return responses.HTMLResponse(content="<h2>Error: Access token not found in token exchange response.</h2>", status_code=400)
            
        person_id = ""
        full_name = ""
        need_urn = True
        
        if scope_mode == "openid":
            try:
                # Fetch profile details using standard OpenID Connect userinfo endpoint
                userinfo_url = "https://api.linkedin.com/v2/userinfo"
                userinfo_headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                
                userinfo_resp = requests.get(userinfo_url, headers=userinfo_headers, timeout=10)
                userinfo_resp.raise_for_status()
                userinfo_info = userinfo_resp.json()
                
                person_id = userinfo_info.get("sub", "")
                full_name = userinfo_info.get("name", "LinkedIn User")
                if person_id:
                    need_urn = False
            except Exception as e:
                print(f"⚠️ OIDC Profile fetch failed: {e}. Falling back to manual URN.")
                
        # Save credentials to db
        db["credentials"]["linkedin_access_token"] = access_token
        if person_id:
            db["credentials"]["linkedin_person_urn"] = f"urn:li:person:{person_id}"
            db["credentials"]["linkedin_member_name"] = full_name
        save_db(db)
        
        # Redirect back to saved frontend port
        target_redirect = db["credentials"].get("linkedin_redirect_back", "http://localhost:5173")
        url_suffix = "?auth=success&need_urn=true" if need_urn else "?auth=success"
        return responses.RedirectResponse(url=f"{target_redirect}{url_suffix}")
        
    except Exception as e:
        err_msg = str(e)
        if 'resp' in locals() and hasattr(resp, 'text'):
            err_msg += f" - Response: {resp.text}"
        return responses.HTMLResponse(content=f"<h2>LinkedIn Authorization Error</h2><p>{err_msg}</p>", status_code=400)

@app.post("/api/auth/logout")
def auth_logout():
    db = load_db()
    db["credentials"]["linkedin_access_token"] = ""
    db["credentials"]["linkedin_person_urn"] = ""
    db["credentials"]["linkedin_member_name"] = ""
    save_db(db)
    return {"status": "success", "message": "LinkedIn account disconnected."}

@app.post("/api/generate-draft")
def generate_draft(req: DraftRequest):
    db = load_db()
    gemini_key = db["credentials"].get("gemini_api_key")
    
    # 1. Generate text commentary and card text
    if req.commentary and req.card_text:
        # Use user-provided values if they are editing/customizing
        commentary = req.commentary
        card_text = req.card_text
    else:
        post_data = generate_post_content(gemini_key=gemini_key, topic=req.topic)
        commentary = post_data["commentary"]
        card_text = post_data["card_text"]
        
    # 2. Render visual card
    temp_filename = f"preview_{uuid.uuid4().hex[:8]}.png"
    temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), temp_filename)
    
    try:
        create_quote_card(card_text, temp_filename)
        
        # Convert preview card image to base64
        with open(temp_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {
            "status": "success",
            "commentary": commentary,
            "card_text": card_text,
            "card_image_base64": f"data:image/png;base64,{encoded_string}"
        }
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Visual card generation failed: {e}")

@app.post("/api/publish-adhoc")
def publish_adhoc(req: PublishAdhocRequest):
    db = load_db()
    creds = db.get("credentials", {})
    token = creds.get("linkedin_access_token")
    person_urn = creds.get("linkedin_person_urn")
    
    if not token or not person_urn:
        raise HTTPException(status_code=400, detail="LinkedIn account is not authorized. Please authorize first.")
        
    # Generate temporary visual card file
    filename = f"adhoc_{uuid.uuid4().hex[:8]}.png"
    image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    
    try:
        create_quote_card(req.card_text, filename)
        
        # Publish
        post_urn = publish_to_linkedin(
            commentary=req.commentary,
            image_path=image_path,
            token=token,
            person_urn=person_urn
        )
        
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)
            
        # Add to logs
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "topic": "Ad-hoc Post",
            "commentary": req.commentary,
            "card_text": req.card_text,
            "status": "completed",
            "published_urn": post_urn
        }
        db["logs"].insert(0, log_entry)
        save_db(db)
        
        return {"status": "success", "published_urn": post_urn}
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
            
        # Add failure to logs
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "topic": "Ad-hoc Post",
            "commentary": req.commentary,
            "card_text": req.card_text,
            "status": "failed",
            "error_message": str(e)
        }
        db["logs"].insert(0, log_entry)
        save_db(db)
        
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# Schedule Management
# =========================================================================

@app.get("/api/schedules")
def get_schedules():
    db = load_db()
    return db.get("schedules", [])

@app.post("/api/schedules")
def create_schedule(req: CreateScheduleRequest):
    db = load_db()
    
    # Generate draft content immediately if not provided
    commentary = req.commentary
    card_text = req.card_text
    
    if not commentary or not card_text:
        try:
            gemini_key = db["credentials"].get("gemini_api_key")
            post_data = generate_post_content(gemini_key=gemini_key, topic=req.topic)
            commentary = post_data["commentary"]
            card_text = post_data["card_text"]
        except Exception:
            # Fallback text
            commentary = f"🚀 Learning more about {req.topic} today!"
            card_text = f"Exploring {req.topic}"
            
    schedule_entry = {
        "id": str(uuid.uuid4()),
        "topic": req.topic,
        "scheduled_time": req.scheduled_time, # ISO format datetime
        "commentary": commentary,
        "card_text": card_text,
        "status": "pending", # pending, paused, completed, failed
        "error_message": None,
        "published_urn": None
    }
    
    db["schedules"].append(schedule_entry)
    # Sort schedules chronologically by scheduled time
    db["schedules"].sort(key=lambda x: x["scheduled_time"])
    save_db(db)
    
    return {"status": "success", "data": schedule_entry}

@app.put("/api/schedules/{schedule_id}")
def update_schedule(schedule_id: str, req: UpdateScheduleRequest):
    db = load_db()
    schedules = db.get("schedules", [])
    
    matched = None
    for s in schedules:
        if s["id"] == schedule_id:
            matched = s
            break
            
    if not matched:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    matched["commentary"] = req.commentary
    matched["card_text"] = req.card_text
    matched["scheduled_time"] = req.scheduled_time
    
    # If it was previously failed, reset to pending when editing
    if matched["status"] in ["failed", "completed"]:
        matched["status"] = "pending"
        matched["error_message"] = None
        matched["published_urn"] = None
        
    save_db(db)
    return {"status": "success", "data": matched}

@app.post("/api/schedules/{schedule_id}/toggle")
def toggle_schedule(schedule_id: str):
    db = load_db()
    schedules = db.get("schedules", [])
    
    matched = None
    for s in schedules:
        if s["id"] == schedule_id:
            matched = s
            break
            
    if not matched:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    if matched["status"] == "pending":
        matched["status"] = "paused"
    elif matched["status"] == "paused":
        matched["status"] = "pending"
    else:
        raise HTTPException(status_code=400, detail=f"Cannot toggle schedule in state: {matched['status']}")
        
    save_db(db)
    return {"status": "success", "data": matched}

@app.delete("/api/schedules/{schedule_id}")
def delete_schedule(schedule_id: str):
    db = load_db()
    schedules = db.get("schedules", [])
    
    filtered = [s for s in schedules if s["id"] != schedule_id]
    if len(filtered) == len(schedules):
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    db["schedules"] = filtered
    save_db(db)
    return {"status": "success", "message": "Schedule deleted successfully."}

@app.get("/api/logs")
def get_logs():
    db = load_db()
    return db.get("logs", [])

@app.post("/api/logs/clear")
def clear_logs():
    db = load_db()
    db["logs"] = []
    save_db(db)
    return {"status": "success", "message": "Logs cleared."}

# =========================================================================
# Background Scheduler Loop
# =========================================================================

async def background_scheduler():
    print("⏰ Background scheduler task initialized.")
    while True:
        try:
            db = load_db()
            now = datetime.now()
            schedules = db.get("schedules", [])
            changed = False
            
            for s in schedules:
                if s["status"] == "pending":
                    try:
                        # Parse scheduled_time (ISO format)
                        sched_time = datetime.fromisoformat(s["scheduled_time"].replace('Z', ''))
                        if now >= sched_time:
                            print(f"⏰ Scheduler: Executing pending schedule {s['id']} for topic '{s['topic']}'")
                            s["status"] = "processing"
                            save_db(db)
                            
                            # Generate card image file
                            filename = f"sched_{s['id'][:8]}.png"
                            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                            
                            try:
                                create_quote_card(s["card_text"], filename)
                                
                                # Publish
                                creds = db["credentials"]
                                token = creds.get("linkedin_access_token")
                                person_urn = creds.get("linkedin_person_urn")
                                
                                if not token or not person_urn:
                                    raise ValueError("LinkedIn token or person URN not found in DB configurations. Please reconnect.")
                                    
                                post_urn = publish_to_linkedin(
                                    commentary=s["commentary"],
                                    image_path=image_path,
                                    token=token,
                                    person_urn=person_urn
                                )
                                
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                                    
                                s["status"] = "completed"
                                s["published_urn"] = post_urn
                                s["error_message"] = None
                                
                                db["logs"].insert(0, {
                                    "id": str(uuid.uuid4()),
                                    "timestamp": datetime.now().isoformat(),
                                    "topic": s["topic"],
                                    "commentary": s["commentary"],
                                    "card_text": s["card_text"],
                                    "status": "completed",
                                    "published_urn": post_urn
                                })
                            except Exception as ex:
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                                raise ex
                                
                            changed = True
                    except Exception as schedule_err:
                        error_msg = str(schedule_err)
                        print(f"❌ Scheduler execution failed for schedule {s['id']}: {error_msg}")
                        s["status"] = "failed"
                        s["error_message"] = error_msg
                        
                        db["logs"].insert(0, {
                            "id": str(uuid.uuid4()),
                            "timestamp": datetime.now().isoformat(),
                            "topic": s["topic"],
                            "commentary": s["commentary"],
                            "card_text": s["card_text"],
                            "status": "failed",
                            "error_message": error_msg
                        })
                        changed = True
                        
            if changed:
                save_db(db)
                
        except Exception as e:
            print(f"⚠️ Scheduler main loop error: {e}")
            
        await asyncio.sleep(15) # Check every 15 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_scheduler())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
