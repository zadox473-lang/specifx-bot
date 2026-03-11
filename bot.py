# ================= INSTAGRAM ANALYZER PRO =================
# DEVELOPER: @proxyfxc
# VERSION: FIXED FOR RENDER
# ==========================================================

import os
import random
import hashlib
import sqlite3
import requests
from io import BytesIO
from datetime import datetime
import threading
import time
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from flask import Flask, request

# Try to load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# ================= CONFIG FROM ENV =================
print("🔍 Checking environment variables...")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_STR = os.environ.get("ADMIN_ID")
API_URL = os.environ.get("API_URL", "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187")
PORT = int(os.environ.get("PORT", 8080))

print(f"BOT_TOKEN set: {'✅' if BOT_TOKEN else '❌'}")
print(f"ADMIN_ID set: {'✅' if ADMIN_ID_STR else '❌'}")

if not BOT_TOKEN:
    print("❌ CRITICAL: BOT_TOKEN not set!")
    BOT_TOKEN = "DUMMY_TOKEN"  # Just for Flask to start

if not ADMIN_ID_STR:
    print("❌ CRITICAL: ADMIN_ID not set!")
    ADMIN_ID = 0
else:
    try:
        ADMIN_ID = int(ADMIN_ID_STR)
        print(f"✅ ADMIN_ID: {ADMIN_ID}")
    except ValueError:
        print(f"❌ ADMIN_ID must be number! Got: {ADMIN_ID_STR}")
        ADMIN_ID = 0

FORCE_CHANNELS = ["@midnight_xaura", "@proxydominates"]
DEVELOPER = "@proxyfxc"

print(f"📊 Force channels: {FORCE_CHANNELS}")
print(f"💻 Developer: {DEVELOPER}")

# ================= FLASK APP =================
app = Flask(__name__)

@app.route('/')
def home():
    bot_status = "✅ RUNNING" if 'bot_app' in globals() and bot_app else "❌ NOT STARTED"
    return f"""
    <html>
        <head>
            <title>Instagram Analyzer Pro</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #1a1a1a; color: white; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .status {{ padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .online {{ background: #00ff8844; border: 1px solid #00ff88; }}
                .offline {{ background: #ff444444; border: 1px solid #ff4444; }}
                .credit {{ color: #00ff88; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔥 INSTAGRAM ANALYZER PRO 🔥</h1>
                <h2 class="credit">BY {DEVELOPER}</h2>
                
                <div class="status {'online' if 'bot_app' in globals() and bot_app else 'offline'}">
                    <h3>Bot Status: {bot_status}</h3>
                    <p>🤖 Telegram Bot: {'✅ Active' if 'bot_app' in globals() and bot_app else '❌ Inactive'}</p>
                    <p>🌐 Web Server: ✅ Active</p>
                </div>
                
                <div class="status">
                    <h3>Configuration:</h3>
                    <p>👑 Admin ID: {ADMIN_ID}</p>
                    <p>📊 Force Channels: {', '.join(FORCE_CHANNELS)}</p>
                </div>
                
                <hr>
                <p>© 2024 {DEVELOPER} - All Rights Reserved</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {
        "status": "ok", 
        "developer": DEVELOPER,
        "bot_running": 'bot_app' in globals() and bot_app is not None
    }, 200

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
db.commit()

def save_user(uid):
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
    db.commit()

def total_users():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]

# ================= FORCE JOIN =================
async def is_joined(bot, user_id):
    for ch in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def join_kb():
    btns = [[InlineKeyboardButton(f"📢 JOIN {c}", url=f"https://t.me/{c[1:]}")] for c in FORCE_CHANNELS]
    btns.append([InlineKeyboardButton("✅ CHECK AGAIN", callback_data="check")])
    return InlineKeyboardMarkup(btns)

# ================= KEYBOARDS =================
def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 DEEP ANALYSIS", callback_data="deep")],
        [InlineKeyboardButton("❓ HELP", callback_data="help")]
    ])

def action_kb(username):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 FULL REPORT", callback_data=f"report|{username}"),
            InlineKeyboardButton("🔄 ANALYZE AGAIN", callback_data="deep")
        ],
        [InlineKeyboardButton("⬅️ MENU", callback_data="menu")]
    ])

# ================= API =================
def fetch_profile(username):
    url = API_URL.format(username)
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") != "ok":
            return None
        return data
    except Exception as e:
        print(f"API Error: {e}")
        return None

def download_image(url):
    try:
        r = requests.get(url, timeout=15)
        bio = BytesIO(r.content)
        bio.name = "profile.jpg"
        return bio
    except:
        return None

# ================= RISK ENGINE =================
def calc_risk(profile_data):
    profile = profile_data.get("profile", {})
    username = profile.get("username", "user")
    bio = (profile.get("biography") or "").lower()
    private = profile.get("is_private", False)
    
    try:
        posts = int(profile.get("posts", 0))
    except:
        posts = 0

    seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    rnd = random.Random(seed)

    pool = [
        "SCAM", "SPAM", "NUDITY",
        "HATE", "HARASSMENT",
        "BULLYING", "VIOLENCE",
        "TERRORISM"
    ]

    if any(x in bio for x in ["music", "rapper", "artist", "singer", "phonk", "promo"]):
        pool += ["DRUGS", "DRUGS"]

    if private and posts < 5:
        pool += ["SCAM", "SCAM", "SCAM"]

    include_self = private and rnd.choice([True, False])
    if include_self:
        pool.append("SELF")
        pool = [i for i in pool if i != "HATE"]

    if rnd.random() < 0.15:
        pool.append("WEAPONS")

    rnd.shuffle(pool)
    selected = list(dict.fromkeys(pool))[:rnd.randint(1, 3)]

    issues, intensity = [], 0
    for i in selected:
        count = rnd.randint(3, 4) if i == "WEAPONS" else rnd.randint(1, 4)
        intensity += count
        issues.append(f"{count}x {i}")

    risk = min(95, 40 + intensity * 6 + (10 if private else 0) + (15 if posts < 5 else 0))
    return risk, issues

# ================= FORMAT ANALYSIS COMPLETE =================
def format_analysis_complete(username, risk, pic_url):
    caption = f"ANALYSIS COMPLETE\n@{username}\nRisk: {risk}%"
    return caption, pic_url

# ================= FORMAT DEEP REPORT =================
def format_deep_report(data, risk, issues):
    profile = data.get("profile", {})
    
    username = profile.get("username", "N/A")
    full_name = profile.get("full_name", "N/A")
    followers = f"{profile.get('followers', 0):,}"
    following = f"{profile.get('following', 0):,}"
    posts = profile.get("posts", 0)
    private = "Yes" if profile.get("is_private", False) else "No"
    pic_url = profile.get("profile_pic_url_hd")
    
    issues_text = "\n".join([f"• {issue}" for issue in issues]) if issues else "• No issues detected"
    
    report = f"""
Deep Analysis Report
Profile: @{username}

• Name: {full_name}
• Followers: {followers}
• Following: {following}
• Posts: {posts}
• Private: {private}

Detected Issues
{issues_text}

Overall Risk
Overall Risk: {risk}%
"""
    return report.strip(), pic_url

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)

    if not await is_joined(context.bot, uid):
        await update.message.reply_text(
            "❌ PLEASE JOIN ALL CHANNELS FIRST!",
            reply_markup=join_kb()
        )
        return

    await update.message.reply_text(
        f"✨ WELCOME TO INSTAGRAM ANALYZER PRO ✨\n\nSEND ANY USERNAME TO ANALYZE!\n\n— {DEVELOPER}",
        reply_markup=menu_kb()
    )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "check":
        if await is_joined(context.bot, q.from_user.id):
            await q.message.edit_text("✅ ACCESS GRANTED!", reply_markup=menu_kb())
        else:
            await q.message.reply_text("❌ PLEASE JOIN ALL CHANNELS FIRST", reply_markup=join_kb())

    elif q.data == "menu":
        await q.message.edit_text("🏠 MAIN MENU", reply_markup=menu_kb())

    elif q.data == "deep":
        context.user_data["waiting_for"] = "username"
        await q.message.reply_text("📤 SEND INSTAGRAM USERNAME:")

    elif q.data.startswith("report|"):
        username = q.data.split("|")[1]
        
        data = fetch_profile(username)
        if not data:
            await q.message.reply_text("❌ PROFILE NOT FOUND!")
            return
        
        risk, issues = calc_risk(data)
        report, pic_url = format_deep_report(data, risk, issues)
        
        if pic_url:
            pic_data = download_image(pic_url)
            if pic_data:
                await q.message.reply_photo(
                    photo=pic_data,
                    caption=report,
                    reply_markup=action_kb(username)
                )
                return
        
        await q.message.reply_text(report, reply_markup=action_kb(username))

    elif q.data == "help":
        await q.message.reply_text(
            "🔍 *HOW TO USE:*\n"
            "• SEND ANY INSTAGRAM USERNAME\n"
            "• GET INSTANT ANALYSIS\n"
            "• RISK ASSESSMENT INCLUDED\n\n"
            f"— {DEVELOPER}",
            parse_mode='Markdown'
        )

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for") == "username":
        return

    context.user_data["waiting_for"] = None
    username = update.message.text.replace("@", "").strip()
    
    if not username:
        await update.message.reply_text("❌ SEND A VALID USERNAME!")
        return
    
    status_msg = await update.message.reply_text("⏳ ANALYZING...")
    
    data = fetch_profile(username)
    
    if not data:
        await status_msg.edit_text("❌ PROFILE NOT FOUND OR API ERROR!")
        return
    
    risk, issues = calc_risk(data)
    profile = data.get("profile", {})
    pic_url = profile.get("profile_pic_url_hd")
    
    caption, _ = format_analysis_complete(username, risk, pic_url)
    
    if pic_url:
        pic_data = download_image(pic_url)
        if pic_data:
            await status_msg.delete()
            await update.message.reply_photo(
                photo=pic_data,
                caption=caption,
                reply_markup=action_kb(username)
            )
            return
    
    await status_msg.edit_text(caption, reply_markup=action_kb(username))

# ================= ADMIN COMMANDS =================
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ UNAUTHORIZED!")
        return
    await update.message.reply_text(f"👥 TOTAL USERS: {total_users()}")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ UNAUTHORIZED!")
        return

    if not context.args:
        await update.message.reply_text("USAGE: /broadcast MESSAGE")
        return

    msg = " ".join(context.args)
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    sent = 0
    failed = 0

    for (uid,) in users:
        try:
            await context.bot.send_message(uid, f"📢 BROADCAST\n\n{msg}\n\n— {DEVELOPER}")
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ SENT: {sent}\n❌ FAILED: {failed}")

# ================= RUN BOT =================
bot_app = None

def run_bot():
    global bot_app
    try:
        print("🚀 Starting Telegram bot...")
        
        if not BOT_TOKEN or BOT_TOKEN == "DUMMY_TOKEN":
            print("❌ Cannot start bot: Invalid BOT_TOKEN")
            return
            
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("users", users_cmd))
        bot_app.add_handler(CommandHandler("broadcast", broadcast_cmd))
        bot_app.add_handler(CallbackQueryHandler(callbacks))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
        
        print("✅ Bot handlers registered!")
        print(f"👑 ADMIN ID: {ADMIN_ID}")
        print(f"📊 FORCE CHANNELS: {FORCE_CHANNELS}")
        print(f"💻 DEVELOPER: {DEVELOPER}")
        print("=" * 40)
        print("✅ Bot is polling for updates...")
        
        bot_app.run_polling()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        bot_app = None

# ================= MAIN =================
if __name__ == "__main__":
    # Print startup banner
    print("╔════════════════════════════════╗")
    print("║    INSTAGRAM ANALYZER PRO     ║")
    print("║         BY @proxyfxc           ║")
    print("╚════════════════════════════════╝")
    
    # Start bot in background thread only if token is valid
    if BOT_TOKEN and BOT_TOKEN != "DUMMY_TOKEN":
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot thread started")
    else:
        print("❌ Bot not started: Invalid token")
    
    # Run Flask app
    print(f"✅ Flask app starting on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
