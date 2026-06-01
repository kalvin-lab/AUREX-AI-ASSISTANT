# AUREX — Your Personal AI Assistant on Telegram

AUREX is a free AI assistant you can talk to right from your phone using Telegram. It can search the web, find YouTube videos, remember things about you, and even understand your voice messages. Everything runs for free — no hidden costs, no credit card needed.

---

## Before You Start — What You'll Need

You only need two things to get AUREX running:

1. **A Google Gemini API key** — this is the AI brain of AUREX (free)
2. **A Telegram Bot token** — this is how you talk to AUREX on your phone (free)

Both take about 5 minutes to get. Let's grab them first.

---

## Getting Your Free Keys

### Google Gemini API Key

1. Go to **https://aistudio.google.com/app/apikey** in your browser
2. Sign in with any Google account (Gmail works fine)
3. Click the **"Create API Key"** button
4. Copy the key it gives you — it looks something like `AIzaSyXXXXXXXXXXXXXX`
5. Save it somewhere safe — you'll need it in a minute

That's it. Google gives you 1 million free tokens every day and 15 requests per minute. For personal use, you'll never come close to hitting those limits.

---

### Telegram Bot Token

1. Open Telegram on your phone or computer
2. Search for **@BotFather** (it's Telegram's official bot — has a blue checkmark)
3. Tap **Start** and then send the message `/newbot`
4. BotFather will ask you for a name — type something like `AUREX Assistant`
5. Then it asks for a username — this must end in the word `bot`, like `aurex_myname_bot`
6. BotFather will give you a token that looks like `7123456789:AAFxxxxxxxxxxxxx`
7. Copy that token — this is your `TELEGRAM_BOT_TOKEN`

**Optional but recommended:** If you want AUREX to only respond to you (private mode), get your Telegram user ID:
- Search for **@userinfobot** on Telegram
- Send it `/start`
- It will tell you your numeric user ID like `123456789`
- You'll use this later to lock the bot to just your account

---

## Setting Up on Your Computer

### Step 1 — Make Sure Python is Installed

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```
python --version
```

You need Python 3.10 or higher. If you don't have it, download it from **https://python.org/downloads** and install it.

---

### Step 2 — Download the Project

If you have Git installed:
```
git clone https://github.com/yourusername/aurex.git
cd aurex
```

Or just download the ZIP file, unzip it, and open a terminal inside that folder.

---

### Step 3 — Install the Dependencies

Run these commands one by one:

```
pip install -r requirements.txt
```

Then install the browser that AUREX uses for web searching:
```
playwright install chromium
```

If you're on Linux, also run:
```
playwright install-deps chromium
```

This downloads a headless Chrome browser (~170MB). It's a one-time thing.

---

### Step 4 — Add Your Keys

In the project folder, you'll see a file called `.env.example`. Make a copy of it and rename the copy to `.env`:

**On Mac/Linux:**
```
cp .env.example .env
```

**On Windows:**
```
copy .env.example .env
```

Now open the `.env` file with any text editor (Notepad works fine) and fill in your keys:

```
TELEGRAM_BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXX
AUDIO_RESPONSE=true
LOG_LEVEL=INFO
```

If you want to make AUREX private (only you can use it), also add:
```
ADMIN_USER_ID=123456789
```

Replace `123456789` with your actual Telegram user ID from @userinfobot.

Save the file and close it.

---

### Step 5 — Run AUREX

```
python bot.py
```

If everything is set up correctly, you'll see something like:

```
╔══════════════════════════════════════════╗
║   🤖 A U R E X  v1.0.0                  ║
║   Powered by Google Gemini 1.5 Flash     ║
╚══════════════════════════════════════════╝

AUREX is running! Send /start on Telegram.
```

Now open Telegram, find your bot by its username, and send `/start`. AUREX will greet you!

---

## Putting AUREX Online (So It Runs 24/7)

Running AUREX on your computer means it stops working when you close the terminal. To keep it running all the time — even when your computer is off — you need to host it online. Here's how to do that for free.

---

## Deploying to Render.com (Recommended — Free)

Render.com is a hosting platform with a free tier that's perfect for running bots. Here's the full process:

---

### Step 1 — Push Your Code to GitHub

You need your code on GitHub so Render can access it. If you've never used GitHub, don't worry — it's straightforward.

**First, create a GitHub account** at **https://github.com** if you don't have one.

**Then, create a new repository:**
1. Click the **+** button in the top right on GitHub
2. Click **New repository**
3. Name it `aurex`
4. Keep it **Private** (important — don't share your code publicly yet)
5. Click **Create repository**

**Then push your code:**
```
git init
git add .
git commit -m "First AUREX deployment"
git remote add origin https://github.com/yourusername/aurex.git
git branch -M main
git push -u origin main
```

> ⚠️ Important: Make sure your `.env` file is NOT being pushed to GitHub. The `.gitignore` file in the project already handles this, but double-check — your API keys must stay private.

---

### Step 2 — Create a Render Account

1. Go to **https://render.com**
2. Click **Get Started for Free**
3. Sign up using your GitHub account — this makes connecting your code much easier

---

### Step 3 — Create a New Web Service

1. Once you're logged into Render, click the **New +** button in the top right
2. Select **Web Service**
3. Choose **Build and deploy from a Git repository**
4. Click **Connect** next to your GitHub account
5. Find and select your `aurex` repository
6. Click **Connect**

---

### Step 4 — Configure the Service

Fill in the settings like this:

| Setting | What to put |
|---|---|
| Name | `aurex-assistant` (or anything you like) |
| Region | Oregon (US West) — lowest latency |
| Branch | `main` |
| Runtime | **Docker** |
| Instance Type | **Free** |

Scroll down to the **Health Check Path** field and type `/health`.

---

### Step 5 — Add Your Secret Keys

This is the important part. Scroll down to the **Environment Variables** section and add these:

Click **Add Environment Variable** for each one:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `GEMINI_API_KEY` | Your key from Google AI Studio |
| `AUDIO_RESPONSE` | `true` |
| `LOG_LEVEL` | `INFO` |

These are stored securely by Render — they're encrypted and never visible to anyone else.

---

### Step 6 — Deploy

Click **Create Web Service** at the bottom. Render will now:
- Download your code from GitHub
- Build the Docker container (takes 3–5 minutes the first time)
- Install all the dependencies including Chromium
- Start AUREX

You'll see a live log of everything happening. When it says "Your service is live", AUREX is running online.

Your bot will now have a public URL like `https://aurex-assistant.onrender.com`. The health check page is at `https://aurex-assistant.onrender.com/health` — if you open that in your browser and see `{"status": "healthy"}`, everything is working.

---

### Step 7 — Keep It Awake (Very Important)

Render's free tier has one catch: if nobody visits your service URL for 15 minutes, it goes to sleep. When it wakes back up it can take 30–60 seconds.

The fix is easy and also free: use **UptimeRobot** to automatically ping your service every 5 minutes.

1. Go to **https://uptimerobot.com** and create a free account
2. Click **Add New Monitor**
3. Monitor Type: **HTTP(s)**
4. Friendly Name: `AUREX Bot`
5. URL: `https://aurex-assistant.onrender.com/health`
6. Monitoring Interval: **5 minutes**
7. Click **Create Monitor**

That's it. UptimeRobot will ping your bot every 5 minutes, keeping it awake around the clock. Total cost: $0.

---

## Alternative: Hugging Face Spaces (Also Free)

If you prefer not to use Render, Hugging Face Spaces is another good free option.

1. Go to **https://huggingface.co** and create a free account
2. Click your profile picture → **New Space**
3. Give it a name like `aurex-bot`
4. For **SDK**, choose **Docker**
5. For **Hardware**, choose **CPU Basic** (this is free)
6. Set visibility to **Private**
7. Click **Create Space**

Once the Space is created, go to **Settings → Repository Secrets** and add:
- `TELEGRAM_BOT_TOKEN` — your bot token
- `GEMINI_API_KEY` — your Gemini key

Then push your code to the Space:
```
git remote add hf https://huggingface.co/spaces/yourusername/aurex-bot
git push hf main
```

It will build and deploy automatically. Same UptimeRobot trick applies here too.

---

## What AUREX Can Do

Once it's running, here's what you can ask AUREX to do in Telegram:

**Just send a message or voice note:**
- `Hello! My name is Ahmed` — AUREX remembers your name for future chats
- `What is the capital of Japan?` — General knowledge questions
- `Search for the latest AI news` — Searches the web in real time
- `Find me YouTube videos about Python programming` — Searches YouTube
- `Open this website and summarize it: https://example.com` — Reads any website
- `Save a file called ideas.txt with this content: ...` — Creates files for you

**Send a voice note** and AUREX will transcribe it and reply — both in text and optionally as a voice message back.

**Slash commands:**
- `/start` — Welcome message and overview
- `/help` — List of everything AUREX can do
- `/memory` — See what AUREX remembers about you
- `/clear` — Wipe the conversation history and start fresh
- `/forget name` — Delete a specific thing AUREX remembered
- `/files` — See files you've created in your workspace
- `/stats` — Usage statistics

---

## Changing the Voice

AUREX speaks using Microsoft's free neural text-to-speech. You can change the voice by editing one line in `config.py`:

```python
TTS_VOICE = "en-US-AriaNeural"   # Default — US female
```

Some options to try:
- `en-GB-SoniaNeural` — British female
- `en-US-GuyNeural` — US male
- `hi-IN-SwaraNeural` — Hindi female
- `ur-PK-UzmaNeural` — Urdu female
- `ar-SA-ZariyahNeural` — Arabic female

All of these are completely free.

---

## If Something Goes Wrong

**AUREX isn't responding in Telegram:**
- Check that you ran `python bot.py` and the terminal is still open (for local)
- On Render: go to your service dashboard and check the **Logs** tab
- Make sure both environment variables are set correctly in the Render dashboard

**It says "quota exceeded" or "rate limit":**
- This just means you hit Gemini's free limit of 15 requests per minute
- Wait a minute and try again — it will work

**Web search or YouTube isn't working:**
- Playwright needs Chromium installed: run `playwright install chromium`
- On Render this is handled automatically by the Dockerfile

**Voice messages aren't working:**
- Make sure `AUDIO_RESPONSE=true` is in your environment variables
- Check that `edge-tts` installed correctly: `pip install edge-tts`

**The bot goes offline on Render:**
- Set up UptimeRobot as described above — this is the most common issue people miss

---

## How Much Does This Cost?

Nothing. Here's the breakdown:

| What | Monthly Cost |
|---|---|
| Google Gemini API | $0 — 1M free tokens/day |
| Telegram Bot | $0 — free forever |
| Web search (DuckDuckGo) | $0 — no API key needed |
| Text-to-speech (edge-tts) | $0 — runs locally |
| Render.com hosting | $0 — free tier |
| UptimeRobot | $0 — free tier |
| **Total** | **$0** |

The only thing that isn't free-forever is the Render disk (if you want your memory to survive server restarts). That's $1/month for 1GB. For testing and personal use, you can skip it and just use the free ephemeral storage.

---

## The Prompt to Give Claude for Extending AUREX

If you want to add new features or customise AUREX and you're using Claude to help you code, paste this at the start of your conversation:

```
I'm working on a Telegram AI assistant called AUREX. Here's the architecture:

- bot.py handles all Telegram messages (text, voice, commands) using python-telegram-bot
- agent_brain.py is the LLM orchestrator using Google Gemini 1.5 Flash
- tools.py has Playwright browser automation tools and file management
- memory_manager.py handles persistent SQLite memory
- voice_handler.py handles TTS (edge-tts) and audio processing
- config.py has all settings

Rules for this project:
1. Everything must remain 100% free forever — no paid APIs
2. Use Python 3.11 async/await throughout
3. New tools get added to TOOL_REGISTRY in tools.py
4. Fast tools (under 3 seconds) go in INSTANT_TOOLS
5. Slow tools (browser/network) go in BACKGROUND_TOOLS so users aren't kept waiting
6. New tools must be described in the AUREX_SYSTEM_PROMPT in agent_brain.py
7. All errors must be caught and return friendly messages to the user

What I want to add: [describe your feature here]
```

---

*AUREX — built entirely on free tools, for anyone who wants a smart assistant on their phone without paying a subscription.*
