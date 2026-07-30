# 🔗 Autonomous LinkedIn Content & Image Poster

A fully autonomous local utility that generates engaging professional tech posts, creates premium matching graphics, and publishes them to LinkedIn at scheduled daily intervals natively on macOS.

---

## ✨ Features

- **Gemini AI Integration**: Generates unique, structured, and topic-specific professional text commentary utilizing Gemini. If no API key is provided, it falls back to a curated collection of templates.
- **Dynamic Graphical Cards**: Generates high-quality gradient visual cards (1200x630px landscape) centered with quotes/headlines, modern fonts, and custom branding automatically.
- **REST API Shares**: Uses modern, versioned LinkedIn REST endpoints (`/rest/images` and `/rest/posts`) replacing legacy deprecated endpoints.
- **Native Scheduling**: Configured via macOS `launchd` to execute silently in the background daily at a set hour. No open terminal windows or persistent processes needed.

---

## 🛠️ Step 1: Set Up LinkedIn Developer App

To communicate with LinkedIn, you need developer credentials:

1. Visit the [LinkedIn Developer Portal](https://www.linkedin.com/developers/) and log in.
2. Click **Create App** and fill in your details:
   - Associate a page (a personal showcase page or company page).
   - Upload an app logo.
3. Once created, go to the **Products** tab and click **Request Access** on:
   - **Share on LinkedIn** (this enables user posting permissions: `w_member_social`).
4. Go to the **Auth** tab:
   - Copy your **Client ID** and **Client Secret**.
   - Under **Authorized redirect URLs**, click **Add redirect URL** and paste:
     `http://localhost:8000/callback`
   - Click **Update**.

---

## 🔑 Step 2: Authenticate and Configure

We use a local OAuth setup script that spins up a quick callback listener on your machine to securely generate and store your access tokens.

1. Ensure your active directory is set to this workspace:
   ```bash
   cd /Users/raju/.gemini/antigravity-ide/scratch/linkedin-autoposter
   ```

2. Make sure your virtual environment is active (or call its binaries directly):
   ```bash
   source .venv/bin/activate
   ```

3. Run the authorization assistant:
   ```bash
   python3 auth.py
   ```

4. The script will prompt you for your **Client ID** and **Client Secret** if they are not in `.env` yet. Then, it will automatically open your web browser.
5. Click **Allow** on the LinkedIn consent screen.
6. The browser will redirect to `http://localhost:8000/callback` showing a success page.
7. Return to the terminal; you should see that `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN` are successfully retrieved and written to `.env`.

> [!TIP]
> To use AI content generation instead of static templates, add your Gemini API Key in the `.env` file under `GEMINI_API_KEY=your_key_here`.

---

## 🧪 Step 3: Run Validation Tests

Run a quick local check to make sure the generator is outputting text and card graphics properly without posting to LinkedIn yet:

```bash
python3 main.py --test-generation
```

Check the directory for a new file named `temp_post_image.png`. It should be a beautiful 1200x630 image card with the matching post summary.

To run a test post live to your LinkedIn feed:
```bash
python3 main.py
```
Open your LinkedIn Profile posts feed to verify it is published!

---

## ⏰ Step 4: Enable Autonomous Scheduling (macOS)

We use macOS's native `launchd` service manager to run this script silently in the background daily.

1. Copy the plist configuration to the macOS User LaunchAgents directory:
   ```bash
   cp com.user.linkedin-autoposter.plist ~/Library/LaunchAgents/
   ```

2. Register and load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.linkedin-autoposter.plist
   ```

3. Confirm that the agent is registered:
   ```bash
   launchctl list | grep autoposter
   ```

Now, the daemon is active! Every day at **9:00 AM local time**, macOS will boot the virtual environment Python interpreter, run the poster, save details to `autoposter.log`, and cleanly exit.

### Useful Scheduling Commands:
- **Trigger immediate run** (for testing the daemon scheduler):
  ```bash
  launchctl start com.user.linkedin-autoposter
  ```
- **Stop/Unload the scheduler**:
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.user.linkedin-autoposter.plist
  ```
- **Inspect Execution Logs**:
  ```bash
  tail -f autoposter.log
  ```
