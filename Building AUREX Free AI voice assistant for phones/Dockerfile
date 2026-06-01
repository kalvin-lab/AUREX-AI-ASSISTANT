# ════════════════════════════════════════════════════════════════
# AUREX — Dockerfile
# Optimized for Render.com free tier (512MB RAM, shared CPU)
# ════════════════════════════════════════════════════════════════

FROM python:3.11-slim-bookworm

# ── System dependencies for Playwright + Chromium ────────────
# These are required for headless Chrome to work in container
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium dependencies
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libxss1 \
    # Audio tools for pydub
    ffmpeg \
    # Networking & utilities
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Copy requirements first (Docker layer caching) ───────────
COPY requirements.txt .

# ── Install Python dependencies ───────────────────────────────
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Install Playwright browsers ───────────────────────────────
# Use pre-installed chromium instead of downloading to save space
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
RUN playwright install chromium --with-deps || \
    echo "Playwright browser install fallback - using system chromium"

# ── Copy application code ─────────────────────────────────────
COPY . .

# ── Create necessary directories ─────────────────────────────
RUN mkdir -p workspace temp logs

# ── Environment variables (secrets set in Render dashboard) ──
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Health check ─────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# ── Run the bot ───────────────────────────────────────────────
CMD ["python", "bot.py"]
