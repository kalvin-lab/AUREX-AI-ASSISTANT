# 🤖 AUREX — Advanced Universal Reasoning & Execution Assistant

> **100% FREE-FOREVER** AI assistant running on Telegram  
> Powered by **Google Gemini 1.5 Flash** · Built with Python 3.11  
> Voice + Text · Web Search · YouTube · File Management · Persistent Memory

---

## 📋 Table of Contents

1. [What is AUREX?](#what-is-aurex)
2. [Architecture Overview](#architecture-overview)
3. [File Structure](#file-structure)
4. [Step 1 — Get Your Free API Keys](#step-1--get-your-free-api-keys)
5. [Step 2 — Local Setup & Testing](#step-2--local-setup--testing)
6. [Step 3 — Deploy to Render.com (FREE)](#step-3--deploy-to-rendercom-free)
7. [Step 4 — Alternative: Hugging Face Spaces](#step-4--alternative-hugging-face-spaces)
8. [Features Deep-Dive](#features-deep-dive)
9. [Customization Guide](#customization-guide)
10. [Troubleshooting](#troubleshooting)
11. [Cost Breakdown](#cost-breakdown)

---

## What is AUREX?

AUREX is a production-grade AI assistant that you can chat with on your smartphone via Telegram. It combines:

| Component | Technology | Cost |
|-----------|-----------|------|
| 🧠 AI Brain | Google Gemini 1.5 Flash | FREE (1M tokens/day) |
| 💬 Interface | Telegram Bot API | FREE forever |
| 🔍 Web Search | DuckDuckGo + Playwright | FREE (open source) |
| 🎤 Voice (STT) | Gemini Multimodal Audio | FREE (same API key) |
| 🔊 Voice (TTS) | Microsoft Edge Neural TTS | FREE (edge-tts library) |
| 🧠 Memory | SQLite (local file) | FREE (built into Python) |
| ☁️ Hosting | Render.com / HuggingFace | FREE tier |

**Total monthly cost: $0.00**

---

## Architecture Overview

```
📱 Your Phone (Telegram App)
        │
        ▼
┌───────────────────────────────────────┐
│         Telegram Bot API              │
│           (bot.py)                    │
│  • Text messages                      │
│  • Voice notes (.ogg)                 │
│  • Slash commands                     │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│         AUREX Brain                   │
│        (agent_brain.py)               │
│                                       │
│  ┌─────────────────┐                  │
│  │  Gemini 1.5     │                  │
│  │  Flash LLM      │◄── System Prompt │
│  │  (Orchestrator) │    + Memory      │
│  └────────┬────────┘                  │
│           │                           │
│    ┌──────▼──────┐                    │
│    │ Tool Router │                    │
│    └──┬──────┬───┘                    │
│       │      │                        │
│  INSTANT   BACKGROUND                 │
│  TOOLS     TOOLS                      │
│  (sync)    (async)                    │
└───┬────────────┬──────────────────────┘
    │            │
    ▼            ▼
┌────────┐  ┌─────────────────────────┐
│ File   │  │  SubAgent Worker        │
│ Ops    │  │  (Background Thread)    │
│        │  │                         │
│ create │  │  • web_search           │
│ read   │  │  • scrape_website       │
│ delete │  │  • search_youtube       │
│ list   │  │                         │
└────────┘  │  Results sent back to   │
            │  user automatically ✓   │
            └─────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Memory Manager       │
            │  (memory_manager.py)  │
            │                       │
            │  SQLite Database:     │
            │  • User profiles      │
            │  • Chat history       │
            │  • Extracted facts    │
            │  • Task logs          │
            └───────────────────────┘
```

---

## File Structure

```
aurex/
├── 📄 bot.py                  ← Main entry point (Telegram bot)
├── 🧠 agent_brain.py          ← LLM orchestrator + sub-agent system
├── 🛠️ tools.py                ← Playwright browser + file tools
├── 🔊 voice_handler.py        ← TTS + audio processing
├── 💾 memory_manager.py       ← SQLite persistent memory
├── ⚙️ config.py               ← All settings in one place
│
├── 📋 requirements.txt        ← Python dependencies
├── 🐳 Dockerfile              ← Container for deployment
├── 🚀 render.yaml             ← Render.com deploy config
├── 🔒 .env.example            ← Template for your secrets
├── 🚫 .gitignore              ← Protects secrets from git
│
├── 📁 workspace/              ← User files (created at runtime)
├── 🗃️ temp/                   ← Temp audio files (auto-cleaned)
├── 📝 logs/                   ← Log files
└── 🗄️ aurex_memory.db         ← SQLite database (created at runtime)
```

---

## Step 1 — Get Your Free API Keys

### 1A. Get Google Gemini API Key (FREE)

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with any Google account
3. Click **"Create API Key"**
4. Copy the key (looks like: `AIza...`)

**Free tier limits:**
- ✅ 15 requests per minute
- ✅ 1,000,000 tokens per day
- ✅ Multimodal (text + audio + images)
- ✅ No credit card required

---

### 1B. Create Your Telegram Bot (FREE)

1. Open Telegram on your phone
2. Search for **@BotFather**
3. Send `/newbot`
4. Choose a name: `AUREX Assistant`
5. Choose a username: `aurex_yourname_bot` (must end in `bot`)
6. BotFather gives you a token like: `7123456789:AAF...`
7. Copy it — this is your `TELEGRAM_BOT_TOKEN`

**Optional:** Get your own User ID
1. Search for **@userinfobot** on Telegram
2. Send `/start` — it shows your numeric ID
3. Set this as `ADMIN_USER_ID` in .env to make AUREX private

---

## Step 2 — Local Setup & Testing

### Prerequisites
- Python 3.10 or 3.11 installed
- Git installed
- 500MB disk space (for Playwright Chromium)

### Installation

```bash
# 1. Clone or download the project
git clone https://github.com/yourusername/aurex.git
cd aurex

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Install Playwright browser (Chromium, ~170MB)
playwright install chromium
playwright install-deps chromium   # Linux only

# 6. Set up environment variables
cp .env.example .env
```

Now edit your `.env` file:
```env
TELEGRAM_BOT_TOKEN=7123456789:AAF_your_actual_token_here
GEMINI_API_KEY=AIzaSy_your_actual_key_here
AUDIO_RESPONSE=true
LOG_LEVEL=INFO
```

### Run Locally

```bash
python bot.py
```

You should see:
```
╔══════════════════════════════════════════╗
║   🤖 A U R E X  v1.0.0                  ║
║   Advanced Universal Reasoning & Exe...  ║
║   Powered by Google Gemini 1.5 Flash     ║
╚══════════════════════════════════════════╝

10:00:00 [INFO] AUREX: Memory Manager initialized
10:00:00 [INFO] AUREX: SubAgent background worker started
10:00:00 [INFO] AUREX.brain: AUREXBrain initialized with model: gemini-1.5-flash
10:00:01 [INFO] AUREX: Bot: @aurex_yourname_bot (AUREX)
10:00:01 [INFO] AUREX: Mode: Long Polling
10:00:01 [INFO] AUREX: AUREX is running! Send /start on Telegram.
```

### Test on Telegram

Open Telegram, find your bot, send `/start` — you should get a welcome message!

**Try these test messages:**
```
/start
Hello! My name is Ahmed
Search for latest AI news 2024
Search YouTube for Python tutorials
Create a file notes.txt with content: Hello World
/memory
/files
```

Send a 🎤 voice note saying "What is the capital of France?" — AUREX will transcribe and respond!

---

## Step 3 — Deploy to Render.com (FREE)

Render.com offers a free tier that keeps your bot running 24/7.

> **Free tier note:** After 15 minutes of no web traffic, free services "spin down" (sleep). Since the bot uses Long Polling (not webhooks), it keeps itself alive. For extra reliability, use [UptimeRobot](https://uptimerobot.com) (also free) to ping your health URL every 5 minutes.

### Step-by-Step Render Deployment

**Step 3.1 — Push code to GitHub**

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial AUREX deployment"

# Create a GitHub repo at github.com/new
# Then push:
git remote add origin https://github.com/yourusername/aurex.git
git branch -M main
git push -u origin main
```

> ⚠️ Make sure `.env` is in `.gitignore`! Your secrets must NEVER go to GitHub.

---

**Step 3.2 — Create Render Account**

1. Go to **https://render.com**
2. Sign up with GitHub (free)
3. Click **"New +"** → **"Web Service"**

---

**Step 3.3 — Connect GitHub Repo**

1. Choose **"Build and deploy from a Git repository"**
2. Connect your GitHub account
3. Select your `aurex` repository
4. Click **"Connect"**

---

**Step 3.4 — Configure the Service**

| Setting | Value |
|---------|-------|
| Name | `aurex-ai-assistant` |
| Region | Oregon (US West) |
| Branch | `main` |
| Runtime | **Docker** |
| Instance Type | **Free** |
| Health Check Path | `/health` |

---

**Step 3.5 — Add Environment Variables (SECRETS)**

In the Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAF...` |
| `GEMINI_API_KEY` | `AIzaSy...` |
| `AUDIO_RESPONSE` | `true` |
| `LOG_LEVEL` | `INFO` |

> 🔒 These are encrypted by Render — safe to store here.

---

**Step 3.6 — Deploy!**

Click **"Create Web Service"** — Render will:
1. Pull your GitHub code
2. Build the Docker container (~3-5 minutes)
3. Install Playwright Chromium
4. Start AUREX

**Your bot URL:** `https://aurex-ai-assistant.onrender.com`
**Health check:** `https://aurex-ai-assistant.onrender.com/health`

---

**Step 3.7 — Set Up UptimeRobot (Free Keep-Alive)**

Render free tier sleeps after 15 min of inactivity. Fix this:

1. Go to **https://uptimerobot.com** (free account)
2. Click **"Add New Monitor"**
3. Monitor type: **HTTP(s)**
4. URL: `https://aurex-ai-assistant.onrender.com/health`
5. Monitoring interval: **5 minutes**
6. Save

Your bot will now stay awake 24/7 for free! 🎉

---

## Step 4 — Alternative: Hugging Face Spaces

If Render.com doesn't work, deploy to Hugging Face Spaces (also FREE):

### Step 4.1 — Create HuggingFace Account
1. Go to **https://huggingface.co**
2. Sign up (free)

### Step 4.2 — Create New Space
1. Click **"New Space"**
2. Space name: `aurex-assistant`
3. SDK: **Docker**
4. Hardware: **CPU Basic (FREE)**
5. Visibility: **Private** (recommended for bots)

### Step 4.3 — Add Secrets
In Space Settings → Repository Secrets:
- `TELEGRAM_BOT_TOKEN` = your token
- `GEMINI_API_KEY` = your key

### Step 4.4 — Push Code
```bash
# Set up HuggingFace remote
git remote add hf https://huggingface.co/spaces/yourusername/aurex-assistant
git push hf main
```

The Space will build and deploy automatically!

---

## Features Deep-Dive

### 🎤 Voice Messages
- Send any voice note to AUREX
- Gemini 1.5 Flash transcribes it (multimodal)
- AUREX responds with text + optional voice reply
- Supports all languages Gemini supports

### 🔍 Web Search
- Uses DuckDuckGo (no API key needed)
- Runs in background SubAgent
- You get an immediate "I'm searching..." response
- Results delivered when ready (15-30 sec)

### 📺 YouTube Search
- Searches YouTube with Playwright
- Returns top 5 videos with titles, channels, view counts, URLs
- Also a background task

### 🧠 Memory System
- **Conversation history**: Last 20 messages included in every prompt
- **User facts**: Automatically extracted (name, city, job, preferences)
- **Persists across restarts**: SQLite database
- **Commands**: `/memory`, `/clear`, `/forget <fact>`

### 📁 File Management
- Create `.txt` and `.csv` files
- Read file contents
- Delete files
- List workspace files
- All files saved to `./workspace/` folder

---

## Customization Guide

### Change AUREX's Personality

Edit `agent_brain.py`, the `AUREX_SYSTEM_PROMPT` variable:

```python
AUREX_SYSTEM_PROMPT = """You are AUREX...
## YOUR PERSONALITY
You are sarcastic and witty, like Tony Stark.
You use humor but always deliver accurate information...
"""
```

### Change TTS Voice

Edit `config.py`:
```python
TTS_VOICE = "en-GB-SoniaNeural"  # British accent
# or
TTS_VOICE = "hi-IN-SwaraNeural"  # Hindi
# or
TTS_VOICE = "ur-PK-UzmaNeural"   # Urdu
```

All 400+ Microsoft Neural voices are free with edge-tts!

### Add a New Tool

In `tools.py`, add your function:
```python
async def tool_get_weather(city: str) -> str:
    """Get weather for a city."""
    # Your implementation here
    return f"Weather in {city}: Sunny, 25°C"
```

Register it in `TOOL_REGISTRY`:
```python
TOOL_REGISTRY["get_weather"] = lambda args: tool_get_weather(args.get("city", ""))
INSTANT_TOOLS.add("get_weather")  # or BACKGROUND_TOOLS
```

Tell the LLM about it in `AUREX_SYSTEM_PROMPT`:
```
8. **get_weather** — Get current weather for any city
   - Args: {"tool": "get_weather", "args": {"city": "London"}}
```

### Restrict to Private Use

In `.env`:
```
ADMIN_USER_ID=123456789   # Your Telegram user ID from @userinfobot
```

Only your account will be able to use the bot.

---

## Troubleshooting

### ❌ "TELEGRAM_BOT_TOKEN is not set"
→ Make sure `.env` file exists and has the correct token.  
→ Check `.env` is in the same folder as `bot.py`.

### ❌ Gemini API quota exceeded
→ Free tier: 15 req/min. Wait 1 minute and retry.  
→ Consider rate limiting by adding `asyncio.sleep(1)` between messages.

### ❌ Playwright fails / browser crashes
→ Run: `playwright install chromium`  
→ On Linux: `playwright install-deps chromium`  
→ On Render: This is handled by the Dockerfile automatically.

### ❌ Voice messages not working
→ Check that `AUDIO_RESPONSE=true` in `.env`  
→ Make sure `edge-tts` is installed: `pip install edge-tts`  
→ Check internet connection (edge-tts needs internet for first call)

### ❌ Bot not responding on Render
→ Check Render logs: Dashboard → Your Service → Logs  
→ Check health endpoint: `https://your-app.onrender.com/health`  
→ Make sure environment variables are set in Render dashboard  
→ Check UptimeRobot is pinging the health URL

### ❌ Memory not persisting on Render
→ Free tier disk is ephemeral (resets on redeploy)  
→ Add a Render Disk ($1/month for 1GB) for true persistence  
→ Or export memory periodically (coming in v2)

---

## Cost Breakdown

| Service | Free Tier Limits | What Happens When Exceeded |
|---------|-----------------|---------------------------|
| Google Gemini | 15 req/min, 1M tokens/day | Error returned, wait & retry |
| Telegram Bot API | Unlimited | N/A — always free |
| Playwright/DuckDuckGo | Unlimited | N/A — self-hosted |
| edge-tts | Unlimited | N/A — runs locally |
| Render.com | 750 hours/month | Service sleeps |
| SQLite memory | Unlimited | Local file, no limits |

**For a personal bot (1-5 users), you will NEVER hit free tier limits.**

---

## The Prompt for Claude to Build This

If you want Claude to help you extend or rebuild AUREX, use this prompt:

```
You are an expert Python developer specializing in AI agents and Telegram bots.

Help me extend the AUREX AI assistant project. AUREX is a Telegram bot powered by 
Google Gemini 1.5 Flash with:

Architecture:
- bot.py: python-telegram-bot async handlers
- agent_brain.py: Gemini LLM orchestrator with tool routing
- tools.py: Playwright browser automation + file management
- memory_manager.py: SQLite persistent memory
- voice_handler.py: edge-tts TTS + Gemini multimodal STT
- config.py: centralized settings

All infrastructure must remain 100% free forever:
- Google Gemini 1.5 Flash (free tier: 15 req/min, 1M tokens/day)
- Telegram Bot API (free forever)
- Render.com free tier for hosting
- No paid APIs or services

Current task: [describe what you want to add/change]

Constraints:
- Python 3.11, fully async (asyncio)
- All new tools must register in TOOL_REGISTRY in tools.py
- Instant tools (< 3 sec) go in INSTANT_TOOLS set
- Slow tools (browser/network) go in BACKGROUND_TOOLS set
- All new features must be described in AUREX_SYSTEM_PROMPT
- Maintain backward compatibility with existing memory schema
- Handle all errors gracefully with user-friendly messages
```

---

## License

MIT License — use freely for personal and commercial projects.

---

*Built with ❤️ using Google Gemini, Python, and 100% free tools.*
