"""
Cloud Headless Runner with Web Dashboard for Render
- Automatically runs the continuous broadcast loop on startup (NO manual commands needed).
- Provides a live web dashboard link (e.g. https://auto-ad-bot.onrender.com) to view stats on mobile/PC.
- Compatible with cron-job.org pings to keep the service awake 24/7.
"""

import os
import sys
import json
import random
import re
import time
import asyncio
import threading
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    UserBannedInChannelError,
    ChatWriteForbiddenError,
    SlowModeWaitError,
    ChannelPrivateError,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.json")

# State & Stats
STATS = {
    "status": "Starting up...",
    "paused": False,
    "rounds_completed": 0,
    "messages_delivered": 0,
    "last_sent_at": "None yet",
    "last_target": "None yet",
    "current_target": "Idle",
    "errors_count": 0,
    "recent_logs": []
}


def add_log(msg: str):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    entry = f"[{timestamp}] {msg}"
    print(entry)
    STATS["recent_logs"].insert(0, entry)
    if len(STATS["recent_logs"]) > 20:
        STATS["recent_logs"].pop()


def render_html_dashboard() -> str:
    status_color = "#10b981" if not STATS["paused"] else "#f59e0b"
    status_text = "🟢 BROADCASTING ACTIVE" if not STATS["paused"] else "⏸️ PAUSED"
    
    logs_html = "".join(f"<div style='padding:4px 0; border-bottom:1px solid #334155; font-family:monospace;'>{log}</div>" for log in STATS["recent_logs"])
    if not logs_html:
        logs_html = "<div style='color:#64748b;'>No activity logs yet. Waiting for round...</div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pricify Cloud Broadcaster</title>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: auto; background: #1e293b; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    h1 {{ margin: 0 0 8px; font-size: 22px; color: #38bdf8; text-align: center; }}
    .subtitle {{ text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 20px; }}
    .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; background: {status_color}22; color: {status_color}; border: 1px solid {status_color}; margin-bottom: 16px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
    .card {{ background: #0f172a; padding: 14px; border-radius: 8px; border: 1px solid #334155; }}
    .card-label {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; margin-bottom: 4px; }}
    .card-val {{ font-size: 20px; font-weight: bold; color: #e2e8f0; }}
    .logs-box {{ background: #0f172a; border-radius: 8px; border: 1px solid #334155; padding: 14px; max-height: 250px; overflow-y: auto; font-size: 12px; color: #94a3b8; }}
    .btn {{ display: block; text-align: center; background: #0284c7; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; margin-top: 16px; }}
    .btn-pause {{ background: #d97706; }}
    .btn-resume {{ background: #16a34a; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>💎 Pricify Cloud Broadcaster</h1>
    <div class="subtitle">Autonomous 24/7 Cloud Engine on Render</div>
    <div style="text-align: center;"><span class="badge">{status_text}</span></div>

    <div class="grid">
      <div class="card">
        <div class="card-label">Delivered Ads</div>
        <div class="card-val" style="color: #38bdf8;">{STATS["messages_delivered"]}</div>
      </div>
      <div class="card">
        <div class="card-label">Rounds Completed</div>
        <div class="card-val" style="color: #a855f7;">{STATS["rounds_completed"]}</div>
      </div>
      <div class="card">
        <div class="card-label">Last Target</div>
        <div class="card-val" style="font-size:14px; color:#e2e8f0; word-break:break-all;">{STATS["last_target"][:20]}</div>
      </div>
      <div class="card">
        <div class="card-label">Last Sent At</div>
        <div class="card-val" style="font-size:13px; color:#94a3b8;">{STATS["last_sent_at"]}</div>
      </div>
    </div>

    <div class="card-label" style="margin-bottom: 8px;">Live Cloud Activity Feed</div>
    <div class="logs-box">{logs_html}</div>

    <a href="?action={'resume' if STATS['paused'] else 'pause'}" class="btn {'btn-resume' if STATS['paused'] else 'btn-pause'}">
      {'▶️ Resume Broadcasting' if STATS['paused'] else '⏸️ Pause Broadcasting'}
    </a>
  </div>
</body>
</html>"""


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        if "action" in params:
            act = params["action"][0]
            if act == "pause":
                STATS["paused"] = True
                add_log("Broadcasting PAUSED via Web Dashboard.")
            elif act == "resume":
                STATS["paused"] = False
                add_log("Broadcasting RESUMED via Web Dashboard.")
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        # Serve Dashboard
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = render_html_dashboard()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_http_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    add_log(f"Web Dashboard listening on port {port}")
    server.serve_forever()


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        print(f"[X] Config file not found at: {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_groups() -> list:
    if not os.path.exists(GROUPS_FILE):
        return []
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def parse_spintax(text: str) -> str:
    pattern = re.compile(r"\{([^{}]+)\}")
    while pattern.search(text):
        text = pattern.sub(lambda m: random.choice(m.group(1).split("|")), text)
    return text


def get_telegram_client(account: dict) -> TelegramClient:
    api_id = int(account.get("api_id"))
    api_hash = account.get("api_hash", "").strip()
    session_name = account.get("session_name", "session_account_1")
    session_path = os.path.join(BASE_DIR, session_name)
    return TelegramClient(session_path, api_id, api_hash)


async def broadcast_loop():
    config = load_config()
    active_key = config.get("active_account", "account_1")
    account = config.get("accounts", {}).get(active_key)
    
    if not account:
        add_log("[X] No active account configured in config.json")
        return

    groups = load_groups()
    if not groups:
        add_log("[!] No groups or channels found in groups.json.")
        return

    safety = config.get("rate_and_safety", {})
    min_delay = safety.get("min_delay_seconds", 60)
    max_delay = safety.get("max_delay_seconds", 120)
    max_messages = safety.get("max_messages_per_run", 50)
    loop_cooldown = safety.get("loop_cooldown_minutes", 10)

    msg_cfg = config.get("message_settings", {})
    msg_type = msg_cfg.get("type", "text")
    templates = msg_cfg.get("spintax_text_templates", [])

    add_log(f"Broadcaster active: {len(groups)} targets queued. Delay: {min_delay}s-{max_delay}s.")

    client = get_telegram_client(account)
    await client.connect()

    if not await client.is_user_authorized():
        add_log("[X] CRITICAL: Session is not authorized on Telegram! Make sure session_account_1.session is in repo.")
        return

    add_log("Telegram Client authenticated successfully!")

    round_idx = 1
    is_danger = "danger" in safety.get("speed_profile", "").lower()

    while True:
        # Check if paused via web dashboard
        while STATS["paused"]:
            await asyncio.sleep(3)

        add_log(f"=== Starting Round #{round_idx} ({len(groups)} targets) ===")
        round_sent = 0

        for idx, grp in enumerate(groups, start=1):
            while STATS["paused"]:
                await asyncio.sleep(3)

            if round_sent >= max_messages:
                add_log(f"Round quota of {max_messages} reached.")
                break

            target = grp["id"]
            title = grp.get("title", f"Chat {target}")
            STATS["current_target"] = title

            try:
                if msg_type == "text":
                    ad_text = parse_spintax(random.choice(templates))
                    await client.send_message(target, ad_text, link_preview=False)

                elif msg_type == "photo":
                    ad_text = parse_spintax(random.choice(templates))
                    photo_path = os.path.join(BASE_DIR, msg_cfg.get("photo_path", "promo.jpg"))
                    if not os.path.exists(photo_path):
                        await client.send_message(target, ad_text, link_preview=False)
                    else:
                        await client.send_file(target, photo_path, caption=ad_text)

                elif msg_type == "forward":
                    fwd_cfg = msg_cfg.get("forward_source", {})
                    chan = fwd_cfg.get("channel", "@pricifydeals")
                    mid = fwd_cfg.get("message_id", 1)
                    await client.forward_messages(target, mid, chan)

                round_sent += 1
                STATS["messages_delivered"] += 1
                STATS["last_sent_at"] = time.strftime("%H:%M:%S", time.localtime())
                STATS["last_target"] = title
                add_log(f"Delivered to {title} ({round_sent}/{len(groups)})")

                # Delay between targets
                if idx < len(groups) and round_sent < max_messages:
                    delay = random.randint(min_delay, max_delay)
                    if is_danger and delay <= 1:
                        await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(delay)

            except FloodWaitError as e:
                add_log(f"FloodWait hit: Sleeping {e.seconds}s...")
                await asyncio.sleep(e.seconds)
            except (UserBannedInChannelError, ChatWriteForbiddenError):
                add_log(f"Muted or Forbidden in '{title}'. Skipped.")
                await asyncio.sleep(2)
            except SlowModeWaitError as e:
                add_log(f"SlowMode active in '{title}' ({e.seconds}s). Skipped.")
                await asyncio.sleep(2)
            except Exception as ex:
                err_str = str(ex).lower()
                if "interdc" in err_str:
                    add_log("Telegram DC glitch. Waiting 5s...")
                    await asyncio.sleep(5)
                else:
                    add_log(f"Error on '{title}': {ex}")
                    STATS["errors_count"] += 1
                    await asyncio.sleep(3)

        STATS["rounds_completed"] = round_idx
        add_log(f"Round #{round_idx} complete! Sent {round_sent} messages.")

        round_idx += 1
        rest_secs = loop_cooldown * 60

        if rest_secs <= 0:
            await asyncio.sleep(2)
        else:
            add_log(f"Resting for {loop_cooldown} minutes before next round...")
            # Sleep in small chunks so web dashboard pause works instantly
            for _ in range(rest_secs):
                if STATS["paused"]:
                    break
                await asyncio.sleep(1)


def main():
    # 1. Start HTTP web server in background thread for Render & cron-job.org
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # 2. Run the async broadcasting loop
    asyncio.run(broadcast_loop())


if __name__ == "__main__":
    main()
