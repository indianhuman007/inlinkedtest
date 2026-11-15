"""
██████╗ ██████╗ ██╗ ██████╗██╗███████╗██╗   ██╗
██╔══██╗██╔══██╗██║██╔════╝██║██╔════╝╚██╗ ██╔╝
██████╔╝██████╔╝██║██║     ██║█████╗   ╚████╔╝ 
██╔═══╝ ██╔══██╗██║██║     ██║██╔══╝    ╚██╔╝  
██║     ██║  ██║██║╚██████╗██║██║        ██║   
╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝╚═╝        ╚═╝   
   [ PRICIFY STORE // MULTI-PLATFORM PROMOTER PRO ]
   [✈️ TELEGRAM]   [📸 INSTAGRAM]   [📘 FACEBOOK]
"""

import os
import sys

# Windows UTF-8 and ANSI escape code configuration
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    os.system("")  # Enable ANSI virtual terminal processing on Windows

import json
import random
import re
import time
import sqlite3
import asyncio
import requests
from typing import List, Dict, Any, Set

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import (
    FloodWaitError,
    UserBannedInChannelError,
    ChatWriteForbiddenError,
    SlowModeWaitError,
    ChannelPrivateError,
)

# Optional Instagrapi for Instagram operations
try:
    from instagrapi import Client as InstaClient
    from instagrapi.exceptions import FeedbackRequired, PleaseWaitFewMinutes, ChallengeRequired
    INSTA_AVAILABLE = True
except ImportError:
    INSTA_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.json")
IG_HISTORY_FILE = os.path.join(BASE_DIR, "ig_comment_history.txt")
IG_SESSION_FILE = os.path.join(BASE_DIR, "ig_session.json")


# --- Terminal Color Palette ---
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def clear_screen():
    os.system("cls" if sys.platform.startswith("win") else "clear")


def print_header_banner():
    banner = f"""{C.RED}{C.BOLD}
  ██████╗ ██████╗ ██╗ ██████╗██╗███████╗██╗   ██╗
  ██╔══██╗██╔══██╗██║██╔════╝██║██╔════╝╚██╗ ██╔╝
  ██████╔╝██████╔╝██║██║     ██║█████╗   ╚████╔╝ 
  ██╔═══╝ ██╔══██╗██║██║     ██║██╔══╝    ╚██╔╝  
  ██║     ██║  ██║██║╚██████╗██║██║        ██║   
  ╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝╚═╝        ╚═╝   {C.RESET}{C.CYAN}
   [+] PRICIFY STORE // MULTI-PLATFORM PROMOTER PRO [+]
   [✈️ TELEGRAM: READY]  [📸 INSTAGRAM: READY]  [📘 FACEBOOK: READY]{C.RESET}
    """
    print(banner)


def cmd_prompt(text: str) -> str:
    print(f"{C.RED}┌──({C.GREEN}pricify-pro{C.RED})-[{C.CYAN}{text}{C.RED}]")
    val = input(f"{C.RED}└─{C.YELLOW}${C.RESET} ").strip()
    return val


# --- Config & Data Handlers ---
def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        print(f"{C.RED}[X] Missing config: {CONFIG_FILE}{C.RESET}")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_groups() -> List[dict]:
    if not os.path.exists(GROUPS_FILE):
        return []
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_groups(groups: List[dict]):
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)


def parse_spintax(text: str) -> str:
    pattern = re.compile(r"\{([^{}]+)\}")
    while pattern.search(text):
        text = pattern.sub(lambda m: random.choice(m.group(1).split("|")), text)
    return text


def get_active_account(config: dict) -> dict:
    active_key = config.get("active_account", "account_1")
    accounts = config.get("accounts", {})
    if active_key not in accounts:
        if accounts:
            active_key = list(accounts.keys())[0]
            config["active_account"] = active_key
            save_config(config)
        else:
            print(f"{C.RED}[X] No accounts configured.{C.RESET}")
            sys.exit(1)
    return accounts[active_key]


# ==============================================================================
# SECTION 1: TELEGRAM ENGINE (MTPROTO USERBOT)
# ==============================================================================

def get_telegram_client(account: dict) -> TelegramClient:
    api_id = account.get("api_id")
    api_hash = account.get("api_hash", "").strip()
    session_name = account.get("session_name", "user_session")
    session_path = os.path.join(BASE_DIR, session_name)
    return TelegramClient(session_path, int(api_id), api_hash)


async def start_client(client: TelegramClient, account: dict):
    if client.is_connected():
        return
    phone = account.get("phone", "").strip()
    password = account.get("password", "").strip() or None
    if phone and not phone.startswith("+91XXXX"):
        await client.start(phone=phone, password=password)
    else:
        await client.start(password=password)


async def run_client_task(account: dict, task_func, *args):
    """Guarantees SQLite session release so 'database is locked' errors never occur."""
    client = get_telegram_client(account)
    try:
        await task_func(client, account, *args)
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            print(f"\n{C.RED}[!] Database lock detected: another window is holding the session.{C.RESET}")
            print(f"{C.YELLOW}    Please close any other open command prompt and try again.{C.RESET}\n")
            input(f"{C.DIM}Press Enter to return...{C.RESET}")
        else:
            print(f"{C.RED}[X] Database Error: {e}{C.RESET}")
            input(f"{C.DIM}Press Enter to return...{C.RESET}")
    except Exception as e:
        print(f"{C.RED}[X] Error: {e}{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
    finally:
        try:
            if client.is_connected():
                await client.disconnect()
        except Exception:
            pass


async def broadcast_ads(client: TelegramClient, account: dict, config: dict):
    groups = load_groups()
    if not groups:
        print(f"\n{C.YELLOW}[!] No target groups selected! Run Option [2] to select groups first.{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    safety = config.get("rate_and_safety", {})
    min_delay = safety.get("min_delay_seconds", 60)
    max_delay = safety.get("max_delay_seconds", 120)
    max_messages = safety.get("max_messages_per_run", 50)
    loop_cooldown = safety.get("loop_cooldown_minutes", 10)

    msg_cfg = config.get("message_settings", {})
    msg_type = msg_cfg.get("type", "text")
    templates = msg_cfg.get("spintax_text_templates", [])

    if not templates and msg_type in ["text", "photo"]:
        print(f"\n{C.RED}[!] No ad templates found! Add an ad in Option [8] first.{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│              LAUNCH TELEGRAM BROADCAST ENGINE               │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
    print(f" {C.BOLD}Target Groups  :{C.RESET} {C.GREEN}{len(groups)}{C.RESET}")
    print(f" {C.BOLD}Payload Type   :{C.RESET} {C.YELLOW}{msg_type.upper()}{C.RESET}")
    print(f" {C.BOLD}Delay Range    :{C.RESET} {C.CYAN}{min_delay}s – {max_delay}s{C.RESET}")
    print(f" {C.BOLD}Loop Cooldown  :{C.RESET} {C.MAGENTA}{loop_cooldown} minutes{C.RESET}\n")

    print(f" {C.BOLD}[1]{C.RESET} Single Burst (Post to all groups once)")
    print(f" {C.BOLD}[2]{C.RESET} Continuous Auto-Loop (Cycle endlessly until Ctrl+C)")
    print(f" {C.BOLD}[C]{C.RESET} Cancel\n")

    choice = cmd_prompt("select-mode").lower()
    if choice not in ["1", "2"]:
        return

    continuous = (choice == "2")
    print(f"\n{C.GREEN}[+] Initializing Telegram MTProto Client...{C.RESET}")

    try:
        await start_client(client, account)
    except Exception as e:
        print(f"{C.RED}[X] Login failure: {e}{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    print(f"{C.GREEN}[+] Connected! Broadcast running in {'CONTINUOUS LOOP' if continuous else 'SINGLE'} mode.{C.RESET}")
    print(f"{C.YELLOW}[!] Press Ctrl+C at ANY time to pause and exit safely.\n{C.RESET}")

    round_idx = 1
    total_sent = 0
    is_danger = "danger" in safety.get("speed_profile", "").lower()

    try:
        while True:
            print(f"{C.CYAN}{C.BOLD}=== [ ROUND #{round_idx} INITIATED // {len(groups)} TARGETS ] ==={C.RESET}")
            round_sent = 0

            for idx, grp in enumerate(groups, start=1):
                if round_sent >= max_messages:
                    print(f"{C.YELLOW}[!] Round quota of {max_messages} reached.{C.RESET}")
                    break

                target = grp["id"]
                title = grp.get("title", f"Destination {target}")
                tag = f"{C.MAGENTA}[📢 CHANNEL]{C.RESET}" if grp.get("type") == "channel" else f"{C.CYAN}[👥 GROUP]{C.RESET}"
                print(f"\n{C.WHITE}[{idx}/{len(groups)}] Target: {tag} {C.BOLD}{title}{C.RESET}")

                try:
                    if msg_type == "text":
                        ad_text = parse_spintax(random.choice(templates))
                        await client.send_message(target, ad_text, link_preview=False)
                        print(f"    {C.GREEN}[✓] INJECTED: Text payload delivered successfully.{C.RESET}")

                    elif msg_type == "photo":
                        ad_text = parse_spintax(random.choice(templates))
                        photo_path = os.path.join(BASE_DIR, msg_cfg.get("photo_path", "promo.jpg"))
                        if not os.path.exists(photo_path):
                            print(f"    {C.YELLOW}[!] Banner missing. Sending text payload.{C.RESET}")
                            await client.send_message(target, ad_text, link_preview=False)
                        else:
                            await client.send_file(target, photo_path, caption=ad_text)
                            print(f"    {C.GREEN}[✓] INJECTED: Banner + Caption delivered successfully.{C.RESET}")

                    elif msg_type == "forward":
                        fwd_cfg = msg_cfg.get("forward_source", {})
                        chan = fwd_cfg.get("channel", "@pricifydeals")
                        mid = fwd_cfg.get("message_id", 1)
                        await client.forward_messages(target, mid, chan)
                        print(f"    {C.GREEN}[✓] INJECTED: Forwarded {chan} #{mid}{C.RESET}")

                    round_sent += 1
                    total_sent += 1

                    if idx < len(groups) and round_sent < max_messages:
                        delay = random.randint(min_delay, max_delay)
                        if is_danger and delay <= 1:
                            print(f"    {C.RED}[💀] DANGER BURST: 1s gap...{C.RESET}")
                            await asyncio.sleep(1)
                        else:
                            print(f"    {C.YELLOW}[⏳] Anti-detection wait: {delay}s...{C.RESET}")
                            for s in range(delay, 0, -1):
                                m, sec = divmod(s, 60)
                                t_str = f"{m:02d}:{sec:02d}" if m else f"{sec}s"
                                print(f"         Next payload in {t_str}... [Ctrl+C to abort]   ", end="\r", flush=True)
                                await asyncio.sleep(1)
                            print(" " * 55, end="\r")

                except FloodWaitError as e:
                    print(f"\n    {C.RED}[!] Telegram FloodWait: Must sleep {e.seconds}s.{C.RESET}")
                    await asyncio.sleep(e.seconds)
                except (UserBannedInChannelError, ChatWriteForbiddenError):
                    print(f"    {C.RED}[-] Write forbidden / muted in '{title}'. Skipped.{C.RESET}")
                    await asyncio.sleep(2)
                except SlowModeWaitError as e:
                    print(f"    {C.YELLOW}[-] Slow mode active ({e.seconds}s). Skipped.{C.RESET}")
                    await asyncio.sleep(2)
                except Exception as ex:
                    err_str = str(ex).lower()
                    if "interdc" in err_str or "internal issues" in err_str:
                        print(f"    {C.YELLOW}[!] Telegram DC routing glitch. Retrying in 5s...{C.RESET}")
                        await asyncio.sleep(5)
                    else:
                        print(f"    {C.RED}[X] Error: {ex}{C.RESET}")
                        await asyncio.sleep(3)

            print(f"\n{C.GREEN}[✓] Round #{round_idx} complete! Sent: {round_sent} messages.{C.RESET}")

            if not continuous:
                print(f"{C.CYAN}[✓] Broadcast completed. Total delivered: {total_sent}{C.RESET}")
                input(f"\n{C.DIM}Press Enter to return to menu...{C.RESET}")
                break

            round_idx += 1
            rest_secs = loop_cooldown * 60
            if rest_secs <= 0:
                if is_danger:
                    print(f"\n{C.RED}{C.BOLD}[💀] DANGER MODE: 0s cooldown! Instantly launching Round #{round_idx}... [Ctrl+C to stop]{C.RESET}")
                else:
                    print(f"\n{C.YELLOW}[⏳] Continuous Loop: No resting cooldown (0m). Launching Round #{round_idx}... [Ctrl+C to stop]{C.RESET}")
                await asyncio.sleep(1)
            else:
                print(f"\n{C.YELLOW}[💤] Resting for {loop_cooldown} minutes before Round #{round_idx}... [Ctrl+C to stop]{C.RESET}")
                for s in range(rest_secs, 0, -1):
                    m, sec = divmod(s, 60)
                    print(f"     Next round in {m:02d}m {sec:02d}s... (Ctrl+C to abort)   ", end="\r", flush=True)
                    await asyncio.sleep(1)
                print(" " * 60, end="\r")

    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}[!] Broadcast stopped by operator (Ctrl+C).{C.RESET}")
        print(f"{C.GREEN}[✓] Total payloads injected: {total_sent} across {round_idx} round(s).{C.RESET}")
        time.sleep(2)


async def scan_and_select_groups(client: TelegramClient, account: dict):
    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}[*] Scanning account dialogs for joined channels & groups...{C.RESET}")
    await start_client(client, account)

    dialogs = await client.get_dialogs()
    targets_pool = []

    for d in dialogs:
        if d.is_group or d.is_channel:
            entity = d.entity
            is_broadcast_channel = isinstance(entity, Channel) and entity.broadcast
            
            # Check posting capability if it's a channel
            can_post = True
            if is_broadcast_channel:
                is_creator = getattr(entity, "creator", False)
                admin_rights = getattr(entity, "admin_rights", None)
                can_post = is_creator or (admin_rights and admin_rights.post_messages)

            targets_pool.append({
                "id": d.id,
                "title": d.title,
                "username": getattr(entity, "username", None) or "",
                "type": "channel" if is_broadcast_channel else "group",
                "can_post": can_post
            })

    if not targets_pool:
        print(f"{C.YELLOW}[!] No channels or groups found for this account.{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    print(f"\n{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│             DISCOVERED CHANNELS & GROUPS                    │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
    for idx, t in enumerate(targets_pool, start=1):
        tag = f"{C.MAGENTA}[📢 CHANNEL]{C.RESET}" if t["type"] == "channel" else f"{C.CYAN}[👥 GROUP]{C.RESET}  "
        uname = f"(@{t['username']})" if t['username'] else "(Private)"
        post_badge = f"{C.GREEN}[ADMIN/POST]{C.RESET}" if t["can_post"] else f"{C.DIM}[SUB]{C.RESET}"
        print(f" [{C.GREEN}{idx:2d}{C.RESET}] {tag} {C.BOLD}{t['title'][:30]:30s}{C.RESET} {uname[:18]:18s} {post_badge}")

    print("\n" + C.CYAN + "-" * 63 + C.RESET)
    print("Options:")
    print("  • Type numbers to select (e.g. '1, 3, 5')")
    print("  • Type 'channels' to select all channels")
    print("  • Type 'groups' to select all groups")
    print("  • Type 'all' to select everything")
    print("  • Type 'M' to manually add channels/groups by username (@chan1, @chan2)")
    print("  • Type 'C' to cancel\n")
    choice = cmd_prompt("select-targets").lower()

    if choice == 'c' or not choice:
        return

    selected = []
    if choice == 'all':
        selected = targets_pool
    elif choice == 'channels':
        selected = [t for t in targets_pool if t["type"] == "channel"]
    elif choice == 'groups':
        selected = [t for t in targets_pool if t["type"] == "group"]
    elif choice == 'm':
        print(f"\n{C.CYAN}Enter channel usernames or links (comma-separated):{C.RESET}")
        print(f"{C.DIM}Example: @pricifydeals, @my_channel_2, https://t.me/my_channel_3{C.RESET}")
        manual_in = cmd_prompt("channel-list")
        if manual_in:
            for item in manual_in.split(","):
                clean = item.strip().replace("https://t.me/", "").replace("t.me/", "")
                if not clean:
                    continue
                try:
                    ent = await client.get_entity(clean)
                    is_bc = isinstance(ent, Channel) and ent.broadcast
                    selected.append({
                        "id": ent.id,
                        "title": getattr(ent, "title", clean),
                        "username": getattr(ent, "username", clean).replace("@", ""),
                        "type": "channel" if is_bc else "group",
                        "can_post": True
                    })
                    print(f"  {C.GREEN}[✓] Added: {getattr(ent, 'title', clean)} ({clean}){C.RESET}")
                except Exception as ex:
                    print(f"  {C.RED}[X] Could not resolve {clean}: {ex}{C.RESET}")
    else:
        for p in choice.split(","):
            p = p.strip()
            if p.isdigit():
                i = int(p) - 1
                if 0 <= i < len(targets_pool):
                    selected.append(targets_pool[i])

    if selected:
        save_groups(selected)
        ch_count = sum(1 for s in selected if s.get("type") == "channel")
        gr_count = len(selected) - ch_count
        print(f"\n{C.GREEN}[✓] Successfully targeted {len(selected)} destinations ({ch_count} channels, {gr_count} groups)!{C.RESET}")
    else:
        print(f"{C.YELLOW}[!] No destinations selected.{C.RESET}")
    time.sleep(1.5)


async def inspect_selected_groups(client: TelegramClient, account: dict):
    groups = load_groups()
    if not groups:
        print(f"{C.YELLOW}[!] No groups in groups.json to inspect.{C.RESET}")
        time.sleep(1.5)
        return

    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}[*] Interrogating Telegram API for metadata on {len(groups)} group(s)...{C.RESET}\n")
    await start_client(client, account)

    for idx, grp in enumerate(groups, start=1):
        gid = grp["id"]
        cached_title = grp.get("title", f"Group {gid}")

        try:
            entity = await client.get_entity(gid)
            title = getattr(entity, "title", cached_title)
            uname = getattr(entity, "username", None)
            uname_str = f"@{uname}" if uname else "Private (Link-only)"

            is_channel = isinstance(entity, Channel)
            chat_type = "Supergroup" if (is_channel and entity.megagroup) else ("Channel" if is_channel else "Basic Group")

            members = "Hidden"
            slowmode = "None (0s)"
            try:
                if is_channel:
                    full = await client(GetFullChannelRequest(entity))
                    if full.full_chat.participants_count:
                        members = f"{full.full_chat.participants_count:,}"
                    sm = getattr(full.full_chat, "slowmode_seconds", 0) or 0
                    if sm > 0:
                        slowmode = f"{sm}s"
                else:
                    members = getattr(entity, "participants_count", "Standard")
            except Exception:
                pass

            can_msg, can_media, can_link = "Yes", "Yes", "Yes"
            try:
                perms = await client.get_permissions(entity, "me")
                can_msg = f"{C.GREEN}YES{C.RESET}" if perms.send_messages else f"{C.RED}NO (MUTED){C.RESET}"
                can_media = f"{C.GREEN}YES{C.RESET}" if perms.send_media else f"{C.RED}NO{C.RESET}"
                can_link = f"{C.GREEN}YES{C.RESET}" if perms.embed_links else f"{C.RED}NO{C.RESET}"
            except Exception:
                pass

            print(f"{C.CYAN}┌──[{C.WHITE}{idx}/{len(groups)}{C.CYAN}] {C.BOLD}{title}{C.RESET}")
            print(f"{C.CYAN}│{C.RESET}  ID: {gid}  |  Username: {C.CYAN}{uname_str}{C.RESET}  |  Type: {chat_type}")
            print(f"{C.CYAN}│{C.RESET}  Members: {C.MAGENTA}{members}{C.RESET}  |  SlowMode: {slowmode}")
            print(f"{C.CYAN}│{C.RESET}  Permissions: [Post: {can_msg}] [Media: {can_media}] [Links: {can_link}]")
            print(f"{C.CYAN}└──{C.GREEN}[STATUS: READY]{C.RESET}\n")

        except Exception as e:
            print(f"{C.RED}[-] Target {gid} inspection failed: {e}{C.RESET}\n")

    input(f"{C.DIM}Press Enter to return to menu...{C.RESET}")


async def check_spambot(client: TelegramClient, account: dict):
    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}[*] Interrogating official @SpamBot for penalties...{C.RESET}\n")
    await start_client(client, account)
    try:
        sb = await client.get_entity("@SpamBot")
        await client.send_message(sb, "/start")
        await asyncio.sleep(2)
        msgs = await client.get_messages(sb, limit=1)
        if msgs:
            print(f"{C.CYAN}┌──[ @SpamBot Official Verdict ]──────────────────────────────┐{C.RESET}")
            print(f"{C.WHITE}{msgs[0].text}{C.RESET}")
            print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
        else:
            print(f"{C.YELLOW}[!] No response received from @SpamBot.{C.RESET}")
    except Exception as e:
        print(f"{C.RED}[X] Error: {e}{C.RESET}")
    input(f"\n{C.DIM}Press Enter to return to menu...{C.RESET}")


# ==============================================================================
# SECTION 2: INSTAGRAM ENGINE (REEL COMMENTER & OUTREACH)
# ==============================================================================

def get_insta_client(config: dict) -> Any:
    if not INSTA_AVAILABLE:
        print(f"{C.RED}[!] 'instagrapi' is not installed. Run 'pip install instagrapi' first.{C.RESET}")
        return None

    cl = InstaClient()
    proxy = config.get("instagram", {}).get("proxy", "").strip()
    if proxy:
        cl.set_proxy(proxy)

    username = config.get("instagram", {}).get("username", "").strip()
    password = config.get("instagram", {}).get("password", "").strip()

    if not username or username == "your_ig_username":
        print(f"{C.YELLOW}[!] Please configure your Instagram username & password first (Option 5).{C.RESET}")
        return None

    if os.path.exists(IG_SESSION_FILE):
        try:
            print(f"{C.CYAN}[*] Restoring saved Instagram session...{C.RESET}")
            cl.load_settings(IG_SESSION_FILE)
            cl.login(username, password)
            print(f"{C.GREEN}[✓] Instagram session restored!{C.RESET}")
            return cl
        except Exception:
            print(f"{C.YELLOW}[!] Session expired. Re-logging in...{C.RESET}")

    try:
        print(f"{C.CYAN}[*] Logging in to Instagram as @{username}...{C.RESET}")
        cl.login(username, password)
        cl.dump_settings(IG_SESSION_FILE)
        print(f"{C.GREEN}[✓] Instagram login successful!{C.RESET}")
        return cl
    except Exception as e:
        print(f"{C.RED}[X] Instagram login failed: {e}{C.RESET}")
        return None


def run_instagram_commenter(config: dict):
    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│               📸 INSTAGRAM REEL AUTO-COMMENTER              │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")

    cl = get_insta_client(config)
    if not cl:
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    ig_cfg = config.get("instagram", {})
    targets = ig_cfg.get("targets", [])
    if not targets:
        print(f"{C.YELLOW}[!] No target Instagram creator accounts configured!{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    templates = config.get("message_settings", {}).get("spintax_text_templates", [])
    if not templates:
        print(f"{C.RED}[!] No ad templates available! Add one in Option [8].{C.RESET}")
        input(f"{C.DIM}Press Enter to return...{C.RESET}")
        return

    # Load history
    commented_history = set()
    if os.path.exists(IG_HISTORY_FILE):
        with open(IG_HISTORY_FILE, "r", encoding="utf-8") as f:
            commented_history = set(line.strip() for line in f if line.strip())

    min_delay = ig_cfg.get("min_delay_seconds", 180)
    max_delay = ig_cfg.get("max_delay_seconds", 360)
    max_comments = ig_cfg.get("max_comments_per_run", 8)
    my_handle = ig_cfg.get("my_handle", "@PricifyStore")

    print(f" Targets Queue : {len(targets)} creator pages")
    print(f" Daily Quota   : {max_comments} comments")
    print(f" Delay Range   : {min_delay}s – {max_delay}s between comments\n")
    print(f"{C.YELLOW}[Tip] Instagram comments never contain raw links (avoids shadowbans). Refer to {my_handle} in bio.{C.RESET}\n")

    confirm = cmd_prompt("start-instagram-commenter (y/n)").lower()
    if confirm != 'y':
        return

    sent = 0
    try:
        for creator in targets:
            if sent >= max_comments:
                print(f"{C.GREEN}[✓] Quota of {max_comments} reached for this run.{C.RESET}")
                break

            print(f"\n{C.WHITE}[{sent + 1}/{len(targets)}] Creator: {C.BOLD}@{creator}{C.RESET}")

            try:
                user_id = cl.user_id_from_username(creator)
                medias = cl.user_medias(user_id, amount=2)
                if not medias:
                    print(f"    {C.YELLOW}[-] No recent posts found for @{creator}.{C.RESET}")
                    continue

                latest = medias[0]
                media_id = str(latest.id)

                if media_id in commented_history:
                    print(f"    {C.DIM}[-] Already commented on latest Reel ({media_id}). Skipping.{C.RESET}")
                    continue

                # Prepare comment
                ad_text = parse_spintax(random.choice(templates))
                # Clean markdown links for Instagram
                ad_text = ad_text.replace("**", "").replace("__", "")

                # Like post first
                try:
                    cl.media_like(latest.id)
                    time.sleep(random.randint(5, 10))
                except Exception:
                    pass

                print(f"    {C.CYAN}[*] Injecting comment on Reel {media_id}...{C.RESET}")
                cl.media_comment(latest.id, ad_text)
                print(f"    {C.GREEN}[✓] Comment delivered: \"{ad_text[:60]}...\"{C.RESET}")

                with open(IG_HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{media_id}\n")
                commented_history.add(media_id)
                sent += 1

                if sent < max_comments:
                    delay = random.randint(min_delay, max_delay)
                    print(f"    {C.YELLOW}[⏳] Anti-spam pacing: waiting {delay}s before next creator...{C.RESET}")
                    for s in range(delay, 0, -1):
                        m, sec = divmod(s, 60)
                        print(f"         Next Reel comment in {m:02d}m {sec:02d}s... [Ctrl+C to stop]   ", end="\r", flush=True)
                        time.sleep(1)
                    print(" " * 60, end="\r")

            except FeedbackRequired:
                print(f"\n{C.RED}[!] Instagram Action Block detected. Let account rest for 24-48 hours.{C.RESET}")
                break
            except Exception as e:
                print(f"    {C.RED}[X] Error on @{creator}: {e}{C.RESET}")
                time.sleep(10)

        print(f"\n{C.GREEN}[✓] Instagram Run complete. Total comments posted: {sent}{C.RESET}")
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}[!] Instagram run stopped by user.{C.RESET}")

    input(f"\n{C.DIM}Press Enter to return to menu...{C.RESET}")


def manage_instagram_menu(config: dict):
    ig_cfg = config.get("instagram", {})
    while True:
        clear_screen()
        print_header_banner()
        print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
        print(f"{C.CYAN}│               📸 INSTAGRAM CONFIGURATION & TARGETS          │{C.RESET}")
        print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
        print(f" Account Username : {C.GREEN}@{ig_cfg.get('username', 'None')}{C.RESET}")
        print(f" Your IG Profile  : {C.MAGENTA}{ig_cfg.get('my_handle', '@PricifyStore')}{C.RESET}")
        print(f" Target Creators  : {C.CYAN}{len(ig_cfg.get('targets', []))} accounts{C.RESET}\n")

        targets = ig_cfg.get("targets", [])
        for idx, t in enumerate(targets, start=1):
            print(f" [{idx}] @{t}")

        print("\nOptions:")
        print("  [1] Add Target Creator Handle")
        print("  [2] Delete Target Creator")
        print("  [3] Set Instagram Username & Password")
        print("  [4] Set Your Profile Handle (@YourPage in bio)")
        print("  [0] Back to Main Menu\n")

        c = cmd_prompt("instagram-config")
        if c == "1":
            new_t = cmd_prompt("enter-creator-handle (without @)").replace("@", "")
            if new_t:
                targets.append(new_t)
                ig_cfg["targets"] = targets
                config["instagram"] = ig_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Target added: @{new_t}{C.RESET}")
                time.sleep(1)
        elif c == "2":
            idx_s = cmd_prompt("delete-target-#")
            if idx_s.isdigit() and 1 <= int(idx_s) <= len(targets):
                removed = targets.pop(int(idx_s) - 1)
                ig_cfg["targets"] = targets
                config["instagram"] = ig_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Removed @{removed}{C.RESET}")
                time.sleep(1)
        elif c == "3":
            u = cmd_prompt("instagram-username")
            p = cmd_prompt("instagram-password")
            if u and p:
                ig_cfg["username"] = u
                ig_cfg["password"] = p
                config["instagram"] = ig_cfg
                save_config(config)
                if os.path.exists(IG_SESSION_FILE):
                    os.remove(IG_SESSION_FILE)
                print(f"{C.GREEN}[✓] Instagram credentials saved!{C.RESET}")
                time.sleep(1.2)
        elif c == "4":
            h = cmd_prompt("your-brand-handle (e.g. @PricifyStore)")
            if h:
                ig_cfg["my_handle"] = h if h.startswith("@") else f"@{h}"
                config["instagram"] = ig_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Brand handle updated!{C.RESET}")
                time.sleep(1)
        elif c == "0":
            break


# ==============================================================================
# SECTION 3: FACEBOOK ENGINE (GROUP AUTO-POSTER VIA COOKIES)
# ==============================================================================

def post_facebook_group(c_user: str, xs: str, group_id: str, message: str) -> bool:
    """Posts a message to a Facebook group using mbasic mobile session."""
    session = requests.Session()
    session.cookies.set("c_user", c_user, domain=".facebook.com")
    session.cookies.set("xs", xs, domain=".facebook.com")
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    url = f"https://mbasic.facebook.com/groups/{group_id}"
    res = session.get(url, headers=headers, timeout=15)

    if "mbasic_logout_button" not in res.text and "c_user" not in str(session.cookies):
        return False

    # Extract form tokens
    match_form = re.search(r'action="(/composer/mbasic/[^"]+)"', res.text)
    if not match_form:
        match_form = re.search(r'action="([^"]*composer[^"]*)"', res.text)
    if not match_form:
        return False

    fb_dtsg_m = re.search(r'name="fb_dtsg" value="([^"]+)"', res.text)
    jazoest_m = re.search(r'name="jazoest" value="([^"]+)"', res.text)
    target_m = re.search(r'name="target" value="([^"]+)"', res.text)

    post_url = "https://mbasic.facebook.com" + match_form.group(1)
    payload = {
        "fb_dtsg": fb_dtsg_m.group(1) if fb_dtsg_m else "",
        "jazoest": jazoest_m.group(1) if jazoest_m else "",
        "target": target_m.group(1) if target_m else group_id,
        "xc_message": message,
        "view_post": "Post",
    }

    post_res = session.post(post_url, data=payload, headers=headers, allow_redirects=True, timeout=20)
    return post_res.status_code in [200, 302]


def run_facebook_poster(config: dict):
    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│               📘 FACEBOOK GROUP AUTO-POSTER                 │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")

    fb_cfg = config.get("facebook", {})
    c_user = fb_cfg.get("c_user", "").strip()
    xs = fb_cfg.get("xs", "").strip()

    if not c_user or not xs:
        print(f"{C.YELLOW}[!] Facebook cookies (c_user & xs) not configured! Please configure them in Option [7].{C.RESET}")
        input(f"\n{C.DIM}Press Enter to return...{C.RESET}")
        return

    targets = fb_cfg.get("targets", [])
    if not targets:
        print(f"{C.YELLOW}[!] No target Facebook Groups added! Add target groups in Option [7].{C.RESET}")
        input(f"\n{C.DIM}Press Enter to return...{C.RESET}")
        return

    templates = config.get("message_settings", {}).get("spintax_text_templates", [])
    if not templates:
        print(f"{C.RED}[!] No ad templates available! Add one in Option [8].{C.RESET}")
        input(f"\n{C.DIM}Press Enter to return...{C.RESET}")
        return

    min_delay = fb_cfg.get("min_delay_seconds", 120)
    max_delay = fb_cfg.get("max_delay_seconds", 240)

    print(f" Facebook Account : c_user={c_user}")
    print(f" Target Groups    : {len(targets)} groups")
    print(f" Delay Range      : {min_delay}s – {max_delay}s\n")

    confirm = cmd_prompt("start-facebook-broadcaster (y/n)").lower()
    if confirm != 'y':
        return

    sent = 0
    try:
        for idx, grp in enumerate(targets, start=1):
            gid = grp.get("id", "")
            title = grp.get("title", f"Group {gid}")
            print(f"\n{C.WHITE}[{idx}/{len(targets)}] Target Group: {C.BOLD}{title}{C.RESET} ({gid})")

            ad_text = parse_spintax(random.choice(templates))
            # Clean formatting for Facebook
            ad_text = ad_text.replace("**", "").replace("__", "")

            print(f"    {C.CYAN}[*] Injecting post payload into group...{C.RESET}")
            success = post_facebook_group(c_user, xs, gid, ad_text)

            if success:
                print(f"    {C.GREEN}[✓] INJECTED: Post delivered to Facebook Group successfully!{C.RESET}")
                sent += 1
            else:
                print(f"    {C.RED}[-] Post failed. Verify group ID or cookies.{C.RESET}")

            if idx < len(targets):
                delay = random.randint(min_delay, max_delay)
                print(f"    {C.YELLOW}[⏳] Anti-spam delay: waiting {delay}s before next group...{C.RESET}")
                for s in range(delay, 0, -1):
                    m, sec = divmod(s, 60)
                    print(f"         Next FB group in {m:02d}m {sec:02d}s... [Ctrl+C to stop]   ", end="\r", flush=True)
                    time.sleep(1)
                print(" " * 60, end="\r")

        print(f"\n{C.GREEN}[✓] Facebook run finished. Total groups posted: {sent}{C.RESET}")
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}[!] Facebook broadcast stopped by user.{C.RESET}")

    input(f"\n{C.DIM}Press Enter to return to menu...{C.RESET}")


def manage_facebook_menu(config: dict):
    fb_cfg = config.get("facebook", {})
    while True:
        clear_screen()
        print_header_banner()
        print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
        print(f"{C.CYAN}│               📘 FACEBOOK CONFIGURATION & GROUPS            │{C.RESET}")
        print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
        print(f" c_user Cookie : {C.GREEN}{fb_cfg.get('c_user', 'Not Set')}{C.RESET}")
        print(f" xs Cookie     : {C.MAGENTA}{'Configured (Hidden)' if fb_cfg.get('xs') else 'Not Set'}{C.RESET}")
        print(f" Target Groups : {C.CYAN}{len(fb_cfg.get('targets', []))} groups{C.RESET}\n")

        targets = fb_cfg.get("targets", [])
        for idx, t in enumerate(targets, start=1):
            print(f" [{idx}] {t.get('title', 'Group')} (ID: {t.get('id')})")

        print("\nOptions:")
        print("  [1] Add Target Facebook Group (ID / Title)")
        print("  [2] Delete Target Group")
        print("  [3] Set Facebook Session Cookies (c_user & xs)")
        print("  [0] Back to Main Menu\n")

        c = cmd_prompt("facebook-config")
        if c == "1":
            gid = cmd_prompt("enter-facebook-group-id (e.g. 1234567890)")
            title = cmd_prompt("enter-group-title (optional)") or f"Group {gid}"
            if gid:
                targets.append({"id": gid, "title": title})
                fb_cfg["targets"] = targets
                config["facebook"] = fb_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Group added: {title} ({gid}){C.RESET}")
                time.sleep(1)
        elif c == "2":
            idx_s = cmd_prompt("delete-group-#")
            if idx_s.isdigit() and 1 <= int(idx_s) <= len(targets):
                removed = targets.pop(int(idx_s) - 1)
                fb_cfg["targets"] = targets
                config["facebook"] = fb_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Group removed!{C.RESET}")
                time.sleep(1)
        elif c == "3":
            print(f"\n{C.YELLOW}Tip: To get c_user and xs cookies from your browser:{C.RESET}")
            print("1. Log in to Facebook on Chrome/Firefox.")
            print("2. Press F12 -> Application tab -> Cookies -> https://www.facebook.com")
            print("3. Copy the 'c_user' and 'xs' cookie values.\n")
            c_u = cmd_prompt("c_user cookie")
            xs_v = cmd_prompt("xs cookie")
            if c_u and xs_v:
                fb_cfg["c_user"] = c_u
                fb_cfg["xs"] = xs_v
                config["facebook"] = fb_cfg
                save_config(config)
                print(f"{C.GREEN}[✓] Facebook cookies saved!{C.RESET}")
                time.sleep(1.2)
        elif c == "0":
            break


# ==============================================================================
# SECTION 4: GLOBAL CUSTOM AD PAYLOAD MAKER & SETTINGS
# ==============================================================================

def custom_ad_manager(config: dict):
    while True:
        templates = config.get("message_settings", {}).get("spintax_text_templates", [])
        clear_screen()
        print_header_banner()
        print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
        print(f"{C.CYAN}│                   GLOBAL AD PAYLOAD MANAGER                 │{C.RESET}")
        print(f"{C.CYAN}│         (Shared across Telegram, Instagram & Facebook)      │{C.RESET}")
        print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
        print(f" Current Active Templates: {C.GREEN}{len(templates)}{C.RESET}\n")

        for idx, t in enumerate(templates, start=1):
            clean = t.replace("\n", " ").strip()
            preview = (clean[:60] + "...") if len(clean) > 60 else clean
            print(f" [{C.GREEN}{idx}{C.RESET}] {preview}")

        print(f"\n {C.BOLD}[1]{C.RESET} Add a New Custom Ad Payload")
        print(f" {C.BOLD}[2]{C.RESET} View Full Ad Content")
        print(f" {C.BOLD}[3]{C.RESET} Edit an Existing Ad")
        print(f" {C.BOLD}[4]{C.RESET} Delete an Ad")
        print(f" {C.BOLD}[5]{C.RESET} Test / Preview Random Spintax")
        print(f" {C.BOLD}[0]{C.RESET} Back to Main Menu\n")

        choice = cmd_prompt("ad-manager")

        if choice == "1":
            print(f"\n{C.GREEN}[+] ADD NEW AD PAYLOAD:{C.RESET}")
            print(f"{C.DIM}Type or paste your ad below.")
            print(f"To finish, type 'done' (or press Enter on an empty line):{C.RESET}\n")
            lines = []
            while True:
                line = input()
                if line.strip().lower() in ["done", "d", "exit", ":wq"] or (line == "" and len(lines) > 0 and lines[-1] == ""):
                    if lines and lines[-1] == "":
                        lines.pop()
                    break
                lines.append(line)

            new_text = "\n".join(lines).strip()
            if new_text:
                templates.append(new_text)
                config["message_settings"]["spintax_text_templates"] = templates
                save_config(config)
                print(f"\n{C.GREEN}[✓] Custom ad payload saved successfully!{C.RESET}")
            else:
                print(f"\n{C.YELLOW}[!] Blank ad discarded.{C.RESET}")
            time.sleep(1.5)

        elif choice == "2":
            idx_str = cmd_prompt("view-ad-#")
            if idx_str.isdigit() and 1 <= int(idx_str) <= len(templates):
                print(f"\n{C.CYAN}--- AD TEMPLATE #{idx_str} ---{C.RESET}")
                print(templates[int(idx_str) - 1])
                print(f"{C.CYAN}----------------------------{C.RESET}")
                input(f"\n{C.DIM}Press Enter to continue...{C.RESET}")

        elif choice == "3":
            idx_str = cmd_prompt("edit-ad-#")
            if idx_str.isdigit() and 1 <= int(idx_str) <= len(templates):
                idx = int(idx_str) - 1
                print(f"\n{C.YELLOW}Current Content:\n{templates[idx]}{C.RESET}")
                print(f"\n{C.DIM}Type new text (finish with 'done' on a new line):{C.RESET}\n")
                lines = []
                while True:
                    line = input()
                    if line.strip().lower() in ["done", "d", "exit"]:
                        break
                    lines.append(line)
                updated = "\n".join(lines).strip()
                if updated:
                    templates[idx] = updated
                    config["message_settings"]["spintax_text_templates"] = templates
                    save_config(config)
                    print(f"{C.GREEN}[✓] Template #{idx_str} updated!{C.RESET}")
                time.sleep(1.5)

        elif choice == "4":
            idx_str = cmd_prompt("delete-ad-#")
            if idx_str.isdigit() and 1 <= int(idx_str) <= len(templates):
                idx = int(idx_str) - 1
                templates.pop(idx)
                config["message_settings"]["spintax_text_templates"] = templates
                save_config(config)
                print(f"{C.GREEN}[✓] Template #{idx_str} removed.{C.RESET}")
                time.sleep(1.2)

        elif choice == "5":
            if templates:
                sample = parse_spintax(random.choice(templates))
                print(f"\n{C.GREEN}=== SAMPLE SPINTAX PREVIEW ==={C.RESET}")
                print(sample)
                print(f"{C.GREEN}=============================={C.RESET}")
                input(f"\n{C.DIM}Press Enter to continue...{C.RESET}")

        elif choice == "0":
            break


def speed_settings_menu(config: dict):
    safety = config.get("rate_and_safety", {})
    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│                   SPEED & TIMING PROFILES                   │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}")
    print(f" Current Profile : {C.GREEN}{safety.get('speed_profile', 'Normal')}{C.RESET}")
    print(f" Delay Range     : {C.CYAN}{safety.get('min_delay_seconds', 45)}s – {safety.get('max_delay_seconds', 90)}s{C.RESET}")
    print(f" Loop Cooldown   : {C.MAGENTA}{safety.get('loop_cooldown_minutes', 10)} mins{C.RESET}\n")

    print(f" {C.BOLD}[1]{C.RESET} 🛡️  Ultra-Safe (Slow)    : 120s – 240s (Minimal ban risk, personal accounts)")
    print(f" {C.BOLD}[2]{C.RESET} ⚖️  Normal (Balanced)     :  60s – 120s (Standard balanced speed)")
    print(f" {C.BOLD}[3]{C.RESET} ⚡ Fast (Aggressive)     :  15s –  35s (Rapid fire, burner numbers only)")
    print(f" {C.BOLD}[4]{C.RESET} 💀 {C.RED}{C.BOLD}DANGER / TURBO MODE{C.RESET}  : {C.RED}1s gap, 0s rest cooldown (MAX SPEED - BURNER ONLY!){C.RESET}")
    print(f" {C.BOLD}[5]{C.RESET} 🛠️  Custom Timing        : Enter exact Min & Max seconds")
    print(f" {C.BOLD}[6]{C.RESET} ⏳ Set Loop Cooldown     : Minutes between continuous rounds")
    print(f" {C.BOLD}[0]{C.RESET} Back\n")

    c = cmd_prompt("speed-profile")
    if c == "1":
        safety["speed_profile"] = "Ultra-Safe"
        safety["min_delay_seconds"] = 120
        safety["max_delay_seconds"] = 240
        safety["loop_cooldown_minutes"] = 15
        save_config(config)
        print(f"{C.GREEN}[✓] Speed set: ULTRA-SAFE (120s - 240s, 15m rest cooldown){C.RESET}")
    elif c == "2":
        safety["speed_profile"] = "Normal"
        safety["min_delay_seconds"] = 60
        safety["max_delay_seconds"] = 120
        safety["loop_cooldown_minutes"] = 10
        save_config(config)
        print(f"{C.GREEN}[✓] Speed set: NORMAL (60s - 120s, 10m rest cooldown){C.RESET}")
    elif c == "3":
        safety["speed_profile"] = "Fast (Burner Only)"
        safety["min_delay_seconds"] = 15
        safety["max_delay_seconds"] = 35
        safety["loop_cooldown_minutes"] = 5
        save_config(config)
        print(f"{C.YELLOW}[✓] Speed set: FAST (15s - 35s, 5m rest cooldown){C.RESET}")
    elif c == "4":
        safety["speed_profile"] = "💀 DANGER (1s Gap, 0s Rest)"
        safety["min_delay_seconds"] = 1
        safety["max_delay_seconds"] = 1
        safety["loop_cooldown_minutes"] = 0
        save_config(config)
        print(f"\n{C.RED}{C.BOLD}[💀] DANGER / TURBO MODE ARMED!{C.RESET}")
        print(f"{C.YELLOW}    Delay: Exactly 1 second between groups.{C.RESET}")
        print(f"{C.YELLOW}    Cooldown: 0 seconds (loops continuously without stopping).{C.RESET}")
        print(f"{C.RED}    ⚠️  HIGH BAN RISK: Use only on disposable burner accounts!{C.RESET}")
        time.sleep(2)
    elif c == "5":
        try:
            mn = int(cmd_prompt("min-delay-seconds"))
            mx = int(cmd_prompt("max-delay-seconds"))
            if mn > 0 and mx >= mn:
                cd_in = cmd_prompt(f"loop-cooldown-minutes (default: {safety.get('loop_cooldown_minutes', 10)})")
                cd_val = int(cd_in) if cd_in.isdigit() else 10
                safety["speed_profile"] = f"Custom ({mn}s-{mx}s)"
                safety["min_delay_seconds"] = mn
                safety["max_delay_seconds"] = mx
                safety["loop_cooldown_minutes"] = cd_val
                save_config(config)
                print(f"{C.GREEN}[✓] Custom timing saved: {mn}s - {mx}s ({cd_val}m rest){C.RESET}")
        except Exception:
            pass
    elif c == "6":
        try:
            cd = int(cmd_prompt("loop-cooldown-minutes"))
            if cd >= 1:
                safety["loop_cooldown_minutes"] = cd
                save_config(config)
                print(f"{C.GREEN}[✓] Cooldown saved: {cd} mins{C.RESET}")
        except Exception:
            pass
    time.sleep(1.2)


def switch_account_menu(config: dict):
    accounts = config.get("accounts", {})
    active = config.get("active_account", "")

    clear_screen()
    print_header_banner()
    print(f"{C.CYAN}┌─────────────────────────────────────────────────────────────┐{C.RESET}")
    print(f"{C.CYAN}│                    TELEGRAM IDENTITY POOL                   │{C.RESET}")
    print(f"{C.CYAN}└─────────────────────────────────────────────────────────────┘{C.RESET}\n")

    acc_keys = list(accounts.keys())
    for idx, key in enumerate(acc_keys, start=1):
        acc = accounts[key]
        act_tag = f"{C.GREEN}[ACTIVE]{C.RESET}" if key == active else ""
        print(f" [{C.CYAN}{idx}{C.RESET}] {C.BOLD}{acc.get('label', key)}{C.RESET} {act_tag}")

    print(f"\n {C.BOLD}[A]{C.RESET} Add New Identity / Burner")
    print(f" {C.BOLD}[C]{C.RESET} Cancel\n")

    c = cmd_prompt("identity-select").lower()
    if c == "a":
        new_k = f"account_{len(accounts) + 1}"
        phone = cmd_prompt("phone (+countrycode)")
        aid = cmd_prompt("api_id")
        ahash = cmd_prompt("api_hash")
        lbl = cmd_prompt("label (e.g. Burner 2)") or new_k
        pwd = cmd_prompt("2fa-cloud-password (leave blank if none)")
        if phone and aid.isdigit() and ahash:
            accounts[new_k] = {
                "label": lbl, "phone": phone, "password": pwd,
                "api_id": int(aid), "api_hash": ahash, "session_name": f"session_{new_k}"
            }
            config["accounts"] = accounts
            config["active_account"] = new_k
            save_config(config)
            print(f"{C.GREEN}[✓] Identity added and activated!{C.RESET}")
            time.sleep(1.5)
    elif c.isdigit():
        idx = int(c) - 1
        if 0 <= idx < len(acc_keys):
            config["active_account"] = acc_keys[idx]
            save_config(config)
            print(f"{C.GREEN}[✓] Switched active identity to {accounts[acc_keys[idx]].get('label')}{C.RESET}")
            time.sleep(1.2)


# --- Main Dashboard ---
def main():
    while True:
        clear_screen()
        print_header_banner()

        config = load_config()
        active_acc = get_active_account(config)
        groups = load_groups()
        safety = config.get("rate_and_safety", {})
        msg_cfg = config.get("message_settings", {})
        ig_cfg = config.get("instagram", {})
        fb_cfg = config.get("facebook", {})

        speed_name = safety.get("speed_profile", "Normal")
        min_d = safety.get("min_delay_seconds", 60)
        max_d = safety.get("max_delay_seconds", 120)

        # Telegram status summary
        if groups:
            ch_count = sum(1 for g in groups if g.get("type") == "channel")
            gr_count = len(groups) - ch_count
            parts = []
            if ch_count > 0:
                parts.append(f"{ch_count} chan")
            if gr_count > 0:
                parts.append(f"{gr_count} grp")
            type_str = f" ({', '.join(parts)})" if parts else ""
            tg_summary = f"{len(groups)} targets{type_str} [" + ", ".join(g.get("title", "")[:12] for g in groups[:2])
            if len(groups) > 2:
                tg_summary += f", +{len(groups) - 2} more"
            tg_summary += "]"
        else:
            tg_summary = "None selected"

        # Instagram status summary
        ig_user = ig_cfg.get("username", "None")
        ig_targets_count = len(ig_cfg.get("targets", []))
        ig_summary = f"@{ig_user} ({ig_targets_count} creators)" if ig_user != "your_ig_username" else "Not Configured"

        # Facebook status summary
        fb_user = fb_cfg.get("c_user", "")
        fb_groups_count = len(fb_cfg.get("targets", []))
        fb_summary = f"User: {fb_user} ({fb_groups_count} groups)" if fb_user else "Not Configured"

        print(f"{C.CYAN}┌──[ SYSTEM TELEMETRY ]───────────────────────────────────────┐{C.RESET}")
        print(f"{C.CYAN}│{C.RESET} 👤 {C.BOLD}Active Telegram{C.RESET}  : {C.GREEN}{active_acc.get('label', 'Unnamed')}{C.RESET} ({tg_summary})")
        print(f"{C.CYAN}│{C.RESET} 📸 {C.BOLD}Instagram Status{C.RESET} : {C.MAGENTA}{ig_summary}{C.RESET}")
        print(f"{C.CYAN}│{C.RESET} 📘 {C.BOLD}Facebook Status{C.RESET}  : {C.BLUE}{fb_summary}{C.RESET}")
        print(f"{C.CYAN}│{C.RESET} ⚡ {C.BOLD}Timing Engine{C.RESET}    : {C.YELLOW}{speed_name} ({min_d}s – {max_d}s delay){C.RESET}")
        print(f"{C.CYAN}└──[ MULTI-PLATFORM OPERATIONS ]──────────────────────────────┘{C.RESET}\n")

        print(f"  {C.CYAN}=== ✈️  TELEGRAM OPERATIONS ==={C.RESET}")
        print(f"  {C.RED}[1]{C.RESET} 🚀 {C.BOLD}Launch Telegram Broadcast{C.RESET} (Single or Continuous Loop)")
        print(f"  {C.RED}[2]{C.RESET} 📋 {C.BOLD}Scan & Select Telegram Targets{C.RESET}")
        print(f"  {C.RED}[3]{C.RESET} 🔍 {C.BOLD}Inspect Telegram Targets{C.RESET} (Permissions & SlowMode)\n")

        print(f"  {C.CYAN}=== 📸 INSTAGRAM OPERATIONS ==={C.RESET}")
        print(f"  {C.RED}[4]{C.RESET} 💬 {C.BOLD}Instagram Reel Auto-Commenter{C.RESET} (Target competitors' reels)")
        print(f"  {C.RED}[5]{C.RESET} 🎯 {C.BOLD}Manage Instagram Targets & Account{C.RESET}\n")

        print(f"  {C.CYAN}=== 📘 FACEBOOK OPERATIONS ==={C.RESET}")
        print(f"  {C.RED}[6]{C.RESET} 📢 {C.BOLD}Facebook Group Auto-Poster{C.RESET} (Cookie Session)")
        print(f"  {C.RED}[7]{C.RESET} 👥 {C.BOLD}Manage Facebook Target Groups & Cookies{C.RESET}\n")

        print(f"  {C.CYAN}=== ⚙️  GLOBAL TOOLS & AD ENGINE ==={C.RESET}")
        print(f"  {C.RED}[8]{C.RESET} ✏️  {C.BOLD}Custom Ad Payload Maker{C.RESET} (Shared across TG, IG & FB)")
        print(f"  {C.RED}[9]{C.RESET} ⚡ {C.BOLD}Speed & Timing Engine{C.RESET} (Slow / Normal / Fast / Danger)")
        print(f"  {C.RED}[10]{C.RESET} 🔄 {C.BOLD}Switch / Add Telegram Identity{C.RESET} (Multi-Account)")
        print(f"  {C.RED}[11]{C.RESET} 🛡️  {C.BOLD}Telegram SpamBot Standing Check{C.RESET}")
        print(f"  {C.RED}[0]{C.RESET} ❌ {C.BOLD}Exit{C.RESET}\n")

        opt = cmd_prompt("root")

        if opt == "1":
            asyncio.run(run_client_task(active_acc, broadcast_ads, config))
        elif opt == "2":
            asyncio.run(run_client_task(active_acc, scan_and_select_groups))
        elif opt == "3":
            asyncio.run(run_client_task(active_acc, inspect_selected_groups))
        elif opt == "4":
            run_instagram_commenter(config)
        elif opt == "5":
            manage_instagram_menu(config)
        elif opt == "6":
            run_facebook_poster(config)
        elif opt == "7":
            manage_facebook_menu(config)
        elif opt == "8":
            custom_ad_manager(config)
        elif opt == "9":
            speed_settings_menu(config)
        elif opt == "10":
            switch_account_menu(config)
        elif opt == "11":
            asyncio.run(run_client_task(active_acc, check_spambot))
        elif opt == "0":
            clear_screen()
            print(f"\n{C.GREEN}[+] Exiting. Keep dominating across Telegram, Instagram & Facebook! 🚀{C.RESET}\n")
            break


if __name__ == "__main__":
    main()
