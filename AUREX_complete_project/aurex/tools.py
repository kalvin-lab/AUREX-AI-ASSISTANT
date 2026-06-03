"""
╔══════════════════════════════════════════════════════════════╗
║  AUREX — tools.py                                           ║
║  All tool implementations available to the agent            ║
║                                                              ║
║  Tools included:                                            ║
║    📁 File Management  → create / read / delete / list      ║
║    🔍 Web Search       → DuckDuckGo (no API key needed)     ║
║    🌐 Web Scraper      → Playwright headless browser        ║
║    📺 YouTube Search   → Playwright on youtube.com          ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import csv
import io
import logging
from pathlib import Path
from typing import Any

import aiofiles
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from config import (
    WORKSPACE_DIR,
    BROWSER_TIMEOUT_MS,
    BROWSER_HEADLESS,
    BROWSER_ARGS,
)

logger = logging.getLogger("AUREX.tools")

# Prevent workspace path traversal attacks
def _safe_workspace_path(filename: str) -> Path:
    """Resolve path safely inside workspace (no path traversal)."""
    filename = Path(filename).name  # Strip any directory components
    return WORKSPACE_DIR / filename


# ════════════════════════════════════════════════════════════════
# 📁 FILE MANAGEMENT TOOLS
# ════════════════════════════════════════════════════════════════

async def tool_create_file(filename: str, content: str) -> str:
    """
    Create a text (.txt) or CSV (.csv) file in the workspace.
    Content is written as-is; for CSV, pass comma-separated lines.
    """
    try:
        safe_path = _safe_workspace_path(filename)

        # Handle CSV formatting
        if filename.endswith(".csv"):
            # Parse content into proper CSV if it looks like raw data
            lines = content.strip().split("\n")
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            for line in lines:
                writer.writerow([cell.strip() for cell in line.split(",")])
            content = csv_buffer.getvalue()

        async with aiofiles.open(safe_path, "w", encoding="utf-8") as f:
            await f.write(content)

        size = safe_path.stat().st_size
        logger.info(f"File created: {safe_path} ({size} bytes)")
        return (
            f"✅ **File Created Successfully!**\n"
            f"📄 Name: `{filename}`\n"
            f"📦 Size: {size} bytes\n"
            f"📂 Location: workspace/{filename}"
        )
    except PermissionError:
        return f"❌ Permission denied: Cannot create `{filename}`."
    except Exception as e:
        logger.error(f"File create error: {e}")
        return f"❌ Failed to create `{filename}`: {str(e)}"


async def tool_read_file(filename: str) -> str:
    """Read and return the contents of a file from the workspace."""
    try:
        safe_path = _safe_workspace_path(filename)

        if not safe_path.exists():
            # List available files to help the user
            available = [f.name for f in WORKSPACE_DIR.iterdir() if f.is_file()]
            hint = f"\nAvailable files: {', '.join(available)}" if available else "\nWorkspace is empty."
            return f"❌ File `{filename}` not found in workspace.{hint}"

        size = safe_path.stat().st_size
        if size > 100_000:  # 100KB limit for reading
            return f"❌ File `{filename}` is too large ({size} bytes). Max 100KB for reading."

        async with aiofiles.open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()

        logger.info(f"File read: {filename} ({size} bytes)")
        return (
            f"📄 **{filename}** ({size} bytes)\n"
            f"{'─' * 40}\n"
            f"{content}\n"
            f"{'─' * 40}"
        )
    except Exception as e:
        logger.error(f"File read error: {e}")
        return f"❌ Failed to read `{filename}`: {str(e)}"


async def tool_delete_file(filename: str) -> str:
    """Delete a file from the workspace."""
    try:
        safe_path = _safe_workspace_path(filename)

        if not safe_path.exists():
            return f"❌ File `{filename}` not found in workspace."

        safe_path.unlink()
        logger.info(f"File deleted: {filename}")
        return f"🗑️ File `{filename}` deleted successfully."
    except Exception as e:
        logger.error(f"File delete error: {e}")
        return f"❌ Failed to delete `{filename}`: {str(e)}"


async def tool_list_files() -> str:
    """List all files in the workspace directory with sizes."""
    try:
        files = sorted(WORKSPACE_DIR.iterdir(), key=lambda f: f.name)
        file_list = [f for f in files if f.is_file()]

        if not file_list:
            return "📂 **Workspace is empty.** No files yet.\n\nTip: Ask me to create a file!"

        lines = ["📂 **Workspace Files:**\n"]
        total_size = 0
        for f in file_list:
            size = f.stat().st_size
            total_size += size
            modified = f.stat().st_mtime
            lines.append(f"  • `{f.name}` — {size:,} bytes")

        lines.append(f"\n📊 Total: {len(file_list)} files, {total_size:,} bytes")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"List files error: {e}")
        return f"❌ Failed to list files: {str(e)}"


# ════════════════════════════════════════════════════════════════
# 🌐 BROWSER HELPER (shared Playwright setup)
# ════════════════════════════════════════════════════════════════

async def _get_page_text(url: str, wait_selector: str | None = None) -> tuple[str, str]:
    """
    Launch headless browser, navigate to URL, extract text.
    Returns (page_title, page_text).
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=BROWSER_HEADLESS,
            args=BROWSER_ARGS,
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=BROWSER_TIMEOUT_MS, wait_until="domcontentloaded")

            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                except PlaywrightTimeout:
                    pass  # Continue even if selector didn't appear

            title = await page.title()

            # Extract clean text: remove nav/footer/ads, get main content
            text = await page.evaluate(
                """() => {
                    // Remove noisy elements
                    const noise = ['script','style','nav','footer','header',
                                   'aside','iframe','noscript','form',
                                   '.ad','#cookie','[class*="cookie"]',
                                   '[class*="popup"]','[class*="modal"]'];
                    noise.forEach(sel => {
                        try { document.querySelectorAll(sel).forEach(el => el.remove()); }
                        catch(e) {}
                    });

                    // Try to get the main content area
                    const selectors = [
                        'main', 'article', '[role="main"]',
                        '.content', '#content', '.post-body',
                        '.article-body', '.entry-content'
                    ];
                    let el = null;
                    for (const sel of selectors) {
                        el = document.querySelector(sel);
                        if (el) break;
                    }
                    const target = el || document.body;
                    return (target.innerText || '')
                        .replace(/\\n{3,}/g, '\\n\\n')
                        .trim()
                        .substring(0, 4000);
                }"""
            )
            return title, text

        finally:
            await browser.close()


# ════════════════════════════════════════════════════════════════
# 🔍 WEB SEARCH (DuckDuckGo — no API key required)
# ════════════════════════════════════════════════════════════════

async def tool_web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo (no API key required, completely free).
    Returns a formatted list of search results with titles and snippets.
    """
    if not query.strip():
        return "❌ Please provide a search query."

    logger.info(f"Web search: '{query}'")

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=BROWSER_HEADLESS,
                args=BROWSER_ARGS,
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            encoded_query = query.replace(" ", "+")
            search_url = f"https://duckduckgo.com/?q={encoded_query}&ia=web"

            await page.goto(search_url, timeout=BROWSER_TIMEOUT_MS,
                          wait_until="domcontentloaded")

            # Wait a moment for JS to render results
            await asyncio.sleep(2)

            # Extract results using multiple possible selectors
            results = await page.evaluate(
                """() => {
                    const items = [];

                    // DuckDuckGo result selectors (try multiple for resilience)
                    const containers = document.querySelectorAll(
                        '[data-result="web"], .result, .nrn-react-div, .results_links_deep'
                    );

                    containers.forEach((el, i) => {
                        if (i >= 6) return;

                        const titleEl = el.querySelector('h2, .result__title, [data-testid="result-title-a"]');
                        const snippetEl = el.querySelector(
                            '.result__snippet, [data-result="snippet"], .E2eLOJr8HoysK6dCwr0W'
                        );
                        const linkEl = el.querySelector('a[href^="http"]');

                        const title   = titleEl  ? titleEl.innerText.trim()   : '';
                        const snippet = snippetEl ? snippetEl.innerText.trim() : '';
                        const url     = linkEl    ? linkEl.href                : '';

                        if (title && snippet) {
                            items.push({ title, snippet, url });
                        }
                    });

                    // Fallback: grab any links with text if above failed
                    if (items.length === 0) {
                        document.querySelectorAll('a[href^="http"]').forEach((a, i) => {
                            if (i >= 8) return;
                            const text = a.innerText.trim();
                            if (text.length > 20 && !a.href.includes('duckduckgo')) {
                                items.push({ title: text, snippet: '', url: a.href });
                            }
                        });
                    }

                    return items;
                }"""
            )

            await browser.close()

            if not results:
                return (
                    f"🔍 Searched for **'{query}'** but couldn't extract results.\n"
                    f"Try rephrasing or asking me to scrape a specific website."
                )

            lines = [f"🔍 **Search Results for:** `{query}`\n{'═' * 45}\n"]
            for i, r in enumerate(results[:5], 1):
                lines.append(f"**{i}. {r['title']}**")
                if r.get("snippet"):
                    lines.append(r["snippet"])
                if r.get("url"):
                    lines.append(f"🔗 {r['url']}")
                lines.append("")

            return "\n".join(lines)

    except PlaywrightTimeout:
        return f"⏱️ Search timed out for '{query}'. The website took too long to respond."
    except Exception as e:
        logger.error(f"Web search error: {e}", exc_info=True)
        return f"❌ Web search failed: {str(e)[:200]}\n\nTry asking a different question or providing a URL."


# ════════════════════════════════════════════════════════════════
# 🌐 WEBSITE SCRAPER
# ════════════════════════════════════════════════════════════════

async def tool_scrape_website(url: str) -> str:
    """
    Scrape and extract the main text content from any website.
    Uses Playwright headless browser for JavaScript-rendered pages.
    """
    if not url.strip():
        return "❌ Please provide a valid URL."

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(f"Scraping website: {url}")

    try:
        title, text = await _get_page_text(url)

        if not text:
            return f"🌐 Opened **{url}** but couldn't extract readable content.\nThe page may require JavaScript or a login."

        word_count = len(text.split())
        return (
            f"🌐 **{title or 'Web Page'}**\n"
            f"🔗 URL: {url}\n"
            f"📊 ~{word_count} words extracted\n"
            f"{'═' * 45}\n\n"
            f"{text[:3500]}"
            + ("\n\n_(Content truncated — page has more)_" if len(text) > 3500 else "")
        )

    except PlaywrightTimeout:
        return f"⏱️ Timed out loading `{url}`. The website may be slow or blocking bots."
    except Exception as e:
        logger.error(f"Scrape error: {e}", exc_info=True)
        return f"❌ Failed to scrape `{url}`: {str(e)[:200]}"


# ════════════════════════════════════════════════════════════════
# 📺 YOUTUBE SEARCH
# ════════════════════════════════════════════════════════════════

async def tool_search_youtube(query: str) -> str:
    """
    Search YouTube for videos and return top results with titles,
    channel names, view counts, and direct video URLs.
    """
    if not query.strip():
        return "❌ Please provide a YouTube search query."

    logger.info(f"YouTube search: '{query}'")

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=BROWSER_HEADLESS,
                args=BROWSER_ARGS,
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            encoded = query.replace(" ", "+")
            await page.goto(
                f"https://www.youtube.com/results?search_query={encoded}",
                timeout=BROWSER_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )

            # Wait for results to render
            try:
                await page.wait_for_selector("ytd-video-renderer", timeout=8000)
            except PlaywrightTimeout:
                await asyncio.sleep(3)  # Fallback wait

            videos = await page.evaluate(
                """() => {
                    const results = [];
                    const items = document.querySelectorAll('ytd-video-renderer');

                    items.forEach((item, idx) => {
                        if (idx >= 6) return;

                        const titleEl   = item.querySelector('#video-title');
                        const channelEl = item.querySelector('#channel-name .yt-formatted-string, ytd-channel-name yt-formatted-string');
                        const viewsEl   = item.querySelector('.ytd-video-meta-block span:first-child, #metadata-line span:first-child');
                        const durationEl = item.querySelector('ytd-thumbnail-overlay-time-status-renderer .badge-shape-wiz__text');

                        const title    = titleEl   ? titleEl.textContent.trim()   : '';
                        const href     = titleEl   ? titleEl.href                 : '';
                        const channel  = channelEl ? channelEl.textContent.trim() : '';
                        const views    = viewsEl   ? viewsEl.textContent.trim()   : '';
                        const duration = durationEl ? durationEl.textContent.trim() : '';

                        if (title && href) {
                            results.push({ title, url: href, channel, views, duration });
                        }
                    });
                    return results;
                }"""
            )

            await browser.close()

            if not videos:
                return (
                    f"📺 Searched YouTube for **'{query}'** but couldn't extract video results.\n"
                    f"Try searching directly: https://youtube.com/results?search_query={encoded}"
                )

            lines = [f"📺 **YouTube Results for:** `{query}`\n{'═' * 45}\n"]
            for i, v in enumerate(videos[:5], 1):
                lines.append(f"**{i}. {v['title']}**")
                if v.get("channel"):
                    lines.append(f"   👤 {v['channel']}")
                if v.get("views"):
                    lines.append(f"   👁️ {v['views']}")
                if v.get("duration"):
                    lines.append(f"   ⏱️ {v['duration']}")
                if v.get("url"):
                    lines.append(f"   🔗 {v['url']}")
                lines.append("")

            return "\n".join(lines)

    except PlaywrightTimeout:
        return f"⏱️ YouTube search timed out for '{query}'."
    except Exception as e:
        logger.error(f"YouTube search error: {e}", exc_info=True)
        return f"❌ YouTube search failed: {str(e)[:200]}"


# ════════════════════════════════════════════════════════════════
# TOOL REGISTRY (used by agent_brain.py for routing)
# ════════════════════════════════════════════════════════════════

# Maps tool names → async callables
TOOL_REGISTRY: dict[str, Any] = {
    "web_search":     lambda args: tool_web_search(args.get("query", "")),
    "scrape_website": lambda args: tool_scrape_website(args.get("url", "")),
    "search_youtube": lambda args: tool_search_youtube(args.get("query", "")),
    "create_file":    lambda args: tool_create_file(
                          args.get("filename", "output.txt"),
                          args.get("content", "")
                      ),
    "read_file":      lambda args: tool_read_file(args.get("filename", "")),
    "delete_file":    lambda args: tool_delete_file(args.get("filename", "")),
    "list_files":     lambda args: tool_list_files(),
}

# These tools run as background sub-agents (they involve browser and take time)
BACKGROUND_TOOLS: set[str] = {"web_search", "scrape_website", "search_youtube"}

# These tools run instantly (file ops are fast)
INSTANT_TOOLS: set[str] = {"create_file", "read_file", "delete_file", "list_files"}
