<div align="center">

```
 █████╗ ██╗   ██╗██████╗ ███████╗██╗  ██╗
██╔══██╗██║   ██║██╔══██╗██╔════╝╚██╗██╔╝
███████║██║   ██║██████╔╝█████╗   ╚███╔╝ 
██╔══██║██║   ██║██╔══██╗██╔══╝   ██╔██╗ 
██║  ██║╚██████╔╝██║  ██║███████╗██╔╝ ██╗
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
```

### Advanced Universal Reasoning & Execution Assistant

**Your AI-powered lead generation engine — running 24/7 on your phone, for free.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini_1.5_Flash-Free_Tier-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-Free_Forever-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/botfather)
[![Render](https://img.shields.io/badge/Hosted_on-Render.com-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

**[⚡ Quick Start](#-quick-start-5-minutes) · [🎯 Lead Gen Use Cases](#-using-aurex-for-lead-generation) · [🚀 Deploy Free](#-deploying-for-free-on-rendercom) · [🛠 How It Works](#-how-it-works)**

</div>

---

## What Is AUREX?

AUREX is a free AI assistant that lives inside Telegram on your phone. It is powered by Google's Gemini 1.5 Flash — the same AI technology used in enterprise tools — and it costs you absolutely nothing to run.

But here's what makes it genuinely useful for people hunting leads: AUREX can **search the web in real time**, **scrape any website**, **find YouTube channels of potential clients**, **save everything to a CSV file**, and **remember your search criteria across every session** — all without you opening a laptop. You just send a voice note or a text message and AUREX does the work.

Think of it as having a research assistant in your pocket who never sleeps, never charges by the hour, and never forgets what you told them last week.

---

## 🎯 Using AUREX for Lead Generation

This is where AUREX really earns its place. Here are real things you can say to it on Telegram right now:

```
"Search for SaaS startups in Dubai that raised funding in 2024"
```
```
"Find YouTube channels about real estate investing with over 10k subscribers"
```
```
"Scrape this LinkedIn company page and give me their contact info: [URL]"
```
```
"Save all of today's leads to a CSV file called dubai_saas_leads.csv"
```
```
"Search for e-commerce stores in Pakistan using Shopify"
```
```
"Find me the top 10 digital marketing agencies in London and save to agencies.csv"
```

AUREX searches, scrapes, extracts, and saves — and it **remembers your lead preferences** so next time you just say *"find more like the last batch"* and it knows exactly what you mean.

---

## 🔄 How It Works

Here is the full picture of what happens from the moment you send a message to when you receive your leads:

```mermaid
flowchart TD
    A([📱 You on Telegram]) -->|Text or Voice Message| B[bot.py\nTelegram Interface]
    
    B -->|Voice Note .ogg| C[voice_handler.py\nGemini Multimodal STT]
    B -->|Text Message| D[agent_brain.py\nGemini 1.5 Flash LLM]
    C -->|Transcribed Text| D

    D -->|Reads context| E[(memory_manager.py\nSQLite Database)]
    E -->|Past leads, preferences, history| D

    D -->|Decides what tool to use| F{Tool Router}

    F -->|Instant — under 3s| G[File Tools\nCreate / Read / Save CSV]
    F -->|Background — 15-30s| H[SubAgent Worker\nPlaywright Browser]

    H --> I[🔍 DuckDuckGo\nWeb Search]
    H --> J[🌐 Website Scraper\nHeadless Chromium]
    H --> K[📺 YouTube Search\nChannel Discovery]

    I --> L[Results Formatted]
    J --> L
    K --> L
    G --> L

    L -->|Saves to memory| E
    L -->|Pushes result back| A

    style A fill:#26A5E4,color:#fff,stroke:none
    style D fill:#4285F4,color:#fff,stroke:none
    style E fill:#34A853,color:#fff,stroke:none
    style H fill:#EA4335,color:#fff,stroke:none
    style L fill:#FBBC05,color:#000,stroke:none
```

---

## 🏗 Architecture At a Glance

```mermaid
graph LR
    subgraph YOUR_PHONE["📱 Your Phone"]
        TG[Telegram App]
    end

    subgraph CLOUD["☁️ Render.com — Free Hosting"]
        subgraph BOT["bot.py"]
            TH[Text Handler]
            VH[Voice Handler]
            CH[Command Handler]
        end

        subgraph BRAIN["agent_brain.py"]
            LLM[Gemini 1.5 Flash\nOrchestrator]
            TR[Tool Router]
            SA[SubAgent\nBackground Worker]
        end

        subgraph TOOLS["tools.py"]
            WS[Web Search\nDuckDuckGo]
            SC[Site Scraper\nPlaywright]
            YT[YouTube\nSearch]
            FM[File Manager\nCSV / TXT]
        end

        subgraph MEM["memory_manager.py"]
            DB[(SQLite DB\nLeads + History\n+ User Facts)]
        end
    end

    subgraph APIS["Free External APIs"]
        GEM[Google Gemini\n1.5 Flash API]
        TTS[Microsoft Edge\nNeural TTS]
    end

    TG <-->|Long Polling| BOT
    BOT --> BRAIN
    BRAIN <--> MEM
    BRAIN --> TOOLS
    BRAIN <--> GEM
    VH <--> TTS

    style YOUR_PHONE fill:#E3F2FD,stroke:#1976D2
    style CLOUD fill:#E8F5E9,stroke:#388E3C
    style APIS fill:#FFF3E0,stroke:#F57C00
```

---

## 🎯 The Lead Generation Workflow

Here is exactly how a typical lead generation session works, from your first message to a saved CSV file full of prospects:

```mermaid
sequenceDiagram
    actor You as 📱 You
    participant AUREX as 🤖 AUREX
    participant Web as 🌐 Web
    participant File as 📁 CSV File

    You->>AUREX: "Find SaaS companies in UAE that hired recently"
    AUREX->>You: ⏳ Searching now, give me 20 seconds...
    AUREX->>Web: DuckDuckGo search + Playwright scrape
    Web-->>AUREX: Company names, websites, LinkedIn URLs
    AUREX->>You: ✅ Found 8 companies — here they are with details

    You->>AUREX: "Save these to uae_leads.csv"
    AUREX->>File: Creates CSV with name, URL, description columns
    AUREX->>You: ✅ Saved! uae_leads.csv is ready in your workspace

    You->>AUREX: "Now search YouTube for UAE startup founders"
    AUREX->>You: ⏳ Searching YouTube...
    AUREX->>Web: Playwright scrapes YouTube results
    Web-->>AUREX: Channel names, subscriber counts, video URLs
    AUREX->>You: ✅ Found 6 channels — want me to add them to the CSV?

    You->>AUREX: "Yes, add them"
    AUREX->>File: Appends YouTube leads to uae_leads.csv
    AUREX->>You: ✅ Done! Your file now has 14 leads total

    You->>AUREX: "Remember: I'm targeting B2B SaaS in the Gulf region"
    AUREX->>AUREX: Saves to memory — remembers forever
    AUREX->>You: Got it. I'll use this for all future searches 🧠
```

---

## 📁 Project Structure

```
AUREX-AI-ASSISTANT/
│
├── 🤖  bot.py               ← Telegram interface (text, voice, commands)
├── 🧠  agent_brain.py       ← Gemini LLM + SubAgent background system
├── 🛠   tools.py             ← Web search, scraping, YouTube, file manager
├── 💾  memory_manager.py    ← SQLite memory (leads, history, your preferences)
├── 🔊  voice_handler.py     ← Speech-to-text + neural text-to-speech
├── ⚙️   config.py            ← All settings in one place
│
├── 📋  requirements.txt     ← Python packages to install
├── 🐳  Dockerfile           ← Container ready for Render/HuggingFace
├── 🚀  render.yaml          ← One-click Render.com deployment config
└── 🔒  .env.example         ← Template for your API keys
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1 — Get your two free keys

**Google Gemini API** (the AI brain):
1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with any Google account
3. Click **Create API Key** and copy it

**Telegram Bot Token** (how you talk to AUREX):
1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow the prompts
3. Copy the token it gives you (looks like `7123456789:AAFxxx...`)

---

### Step 2 — Install and run locally

```bash
# Clone the repo
git clone https://github.com/kalvin-lab/AUREX-AI-ASSISTANT.git
cd AUREX-AI-ASSISTANT

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install all dependencies
pip install -r requirements.txt

# Install the headless browser (one-time, ~170MB)
playwright install chromium

# Set up your keys
cp .env.example .env
# Open .env and fill in your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY

# Run it!
python bot.py
```

Open Telegram, find your bot, send `/start` — AUREX is live.

---

## 🚀 Deploying for Free on Render.com

Running on your laptop is fine for testing, but to have AUREX working 24/7 — even when your phone is in your pocket and your computer is off — you need to host it. Render.com's free tier is perfect for this.

```mermaid
flowchart LR
    A[📂 Your Code\non GitHub] -->|Auto-detected| B[Render.com\nFree Web Service]
    B -->|Builds Docker\ncontainer| C[🐳 Docker Build\n3-5 minutes]
    C -->|Installs Chromium\n+ all packages| D[🟢 AUREX\nLive Online]
    D -->|Ping every\n5 minutes| E[UptimeRobot\nFree Keep-Alive]
    E -->|Stays awake\n24/7| D

    style A fill:#24292F,color:#fff,stroke:none
    style B fill:#46E3B7,color:#000,stroke:none
    style D fill:#22C55E,color:#fff,stroke:none
    style E fill:#3B82F6,color:#fff,stroke:none
```

**The 7 steps:**

**1. Push to GitHub**
```bash
git init
git add .
git commit -m "Deploy AUREX"
git remote add origin https://github.com/yourusername/aurex.git
git push -u origin main
```
> Make sure `.env` is in `.gitignore` — never push your API keys to GitHub.

**2.** Go to **https://render.com** and sign up with your GitHub account.

**3.** Click **New +** → **Web Service** → connect your GitHub repo.

**4.** Use these settings:

| Setting | Value |
|---|---|
| Runtime | Docker |
| Instance Type | **Free** |
| Health Check Path | `/health` |
| Region | Oregon (US West) |

**5.** Add your environment variables in Render's dashboard:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your BotFather token |
| `GEMINI_API_KEY` | Your Google AI Studio key |
| `AUDIO_RESPONSE` | `true` |

**6.** Click **Create Web Service** and wait 3–5 minutes for the build.

**7. Keep it alive with UptimeRobot (free):**
- Go to **https://uptimerobot.com** → create a free account
- Add a new HTTP monitor pointing to `https://your-app.onrender.com/health`
- Set interval to **5 minutes**

That's it. AUREX is now running 24/7, totally free.

---

## 💬 Lead Generation Commands — Cheat Sheet

Once AUREX is running, here are the most useful things to say to it for finding leads:

| What you want | What to type |
|---|---|
| Search for companies | `Search for fintech startups in Singapore 2024` |
| Scrape a website | `Read this page and extract all contact info: [URL]` |
| Find YouTube leads | `Find YouTube channels about dropshipping with UK audience` |
| Save leads to file | `Save these results to leads.csv` |
| Read your saved leads | `Read the file leads.csv` |
| Remember your niche | `Remember: I target e-commerce brands doing $1M+ revenue` |
| Check what you've saved | `/files` |
| See your memory | `/memory` |
| Search voice | *Send a voice note saying what you want* |

---

## 🧠 What AUREX Remembers About You

Every fact you tell AUREX gets stored in its SQLite database and used in future sessions. This is powerful for lead generation because you can train it over time:

```mermaid
graph TD
    A[You tell AUREX:\n'I target SaaS B2B companies\nin the MENA region'] --> B[(SQLite Memory\naurex_memory.db)]
    C[You tell AUREX:\n'My ideal client has\n10-50 employees'] --> B
    D[You tell AUREX:\n'Focus on LinkedIn\nand Clutch.co'] --> B
    
    B --> E[Every future search\nautomatically uses\nyour criteria]
    
    E --> F[More relevant leads\nwithout repeating yourself]

    style B fill:#34A853,color:#fff,stroke:none
    style F fill:#4285F4,color:#fff,stroke:none
```

Use `/memory` to see everything AUREX knows about you. Use `/forget [key]` to delete something specific.

---

## 💰 Complete Cost Breakdown

| Tool | What it does | Monthly cost |
|---|---|---|
| Google Gemini 1.5 Flash | The AI brain — 1M free tokens/day | **$0** |
| Telegram Bot API | Your phone interface | **$0** |
| DuckDuckGo Search | Web search engine | **$0** |
| Playwright Chromium | Headless browser for scraping | **$0** |
| Microsoft Edge TTS | High-quality voice responses | **$0** |
| Render.com | 24/7 cloud hosting | **$0** |
| UptimeRobot | Keeps the server awake | **$0** |
| SQLite | Persistent memory storage | **$0** |
| **Total** | | **$0.00 / month** |

The only optional paid upgrade is a $1/month Render disk if you want your lead database to survive server restarts. For most users, it's not necessary.

---

## 🔧 Troubleshooting

**AUREX doesn't respond in Telegram**
→ Check your `TELEGRAM_BOT_TOKEN` is set correctly in your `.env` or Render dashboard. The token must be exact — even one wrong character breaks it.

**It says "quota exceeded"**
→ You've hit Gemini's free limit of 15 requests per minute. Wait 60 seconds and try again. For heavier use, add a short delay between searches.

**Web search returns nothing**
→ Run `playwright install chromium` again. On Render, this is handled by the Dockerfile automatically but double-check your build logs.

**Voice messages don't work**
→ Make sure `AUDIO_RESPONSE=true` is in your environment variables and `edge-tts` installed: `pip install edge-tts`

**The bot sleeps and takes 30 seconds to wake up**
→ You skipped the UptimeRobot step. Set it up — it takes 2 minutes and keeps the bot permanently awake.

**My CSV file disappeared after a Render redeploy**
→ Render's free tier uses ephemeral storage that resets on redeploy. Add a Render Disk ($1/month) to persist your files, or download important CSVs before redeploying.

---

## 🗺 Roadmap

Things that are coming next:

- [ ] **LinkedIn scraper** — extract profiles, job titles, company info from public pages
- [ ] **Email finder** — search for contact emails on company websites
- [ ] **Lead scoring** — AUREX ranks leads by how well they match your criteria
- [ ] **Export to Google Sheets** — sync your CSV leads directly to a spreadsheet
- [ ] **Scheduled searches** — tell AUREX to search every Monday morning and send results
- [ ] **WhatsApp support** — same bot, but on WhatsApp via Twilio sandbox

---

## 🤝 Contributing

Pull requests are welcome. If you build a new tool (LinkedIn scraper, email extractor, Google Maps lead finder), add it to `tools.py` following the existing pattern and open a PR.

The rule is simple: **everything must stay free forever**. No paid API dependencies.

---

## 📄 License

MIT License — free to use, fork, modify, and deploy commercially.

---

<div align="center">

**Built with Google Gemini · python-telegram-bot · Playwright · edge-tts · SQLite**

*If this saved you time or money on lead generation, give the repo a ⭐ — it helps others find it.*

[⭐ Star this repo](https://github.com/kalvin-lab/AUREX-AI-ASSISTANT) · [🐛 Report a bug](https://github.com/kalvin-lab/AUREX-AI-ASSISTANT/issues) · [💡 Request a feature](https://github.com/kalvin-lab/AUREX-AI-ASSISTANT/issues)

</div>
