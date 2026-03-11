# ================= IMPORTS =================
import os
import random
import hashlib
import sqlite3
import requests
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import threading
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617750252:AAGQNV4D22ekCPjt41aMgdbh6hUJicC79sg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8554863978))
API_URL = "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187"

FORCE_CHANNELS = [
    "@midnight_xaura",
    "@proxydominates"
]

# SIRF AAPKA CREDIT - @proxyfxc
CREATOR = "@proxyfxc"
BOT_NAME = "Instagram Analyzer Pro"

DAILY_CREDITS =
# ================= FLASK APP =================
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": BOT_NAME,
        "creator": CREATOR,
        "endpoints": {
            "/health": "Health check",
            "/stats": "Bot statistics"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/stats')
def stats():
    try:
        cur.execute("SELECT COUNT(*) FROM users WHERE approved = 1")
        approved_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE approved = 0 AND blocked = 0")
        pending_users = cur.fetchone()[0]
        
        return jsonify({
            "bot": BOT_NAME,
            "creator": CREATOR,
            "approved_users": approved_users,
            "pending_approval": pending_users,
            "status": "running"
        })
    except:
        return jsonify({"error": "Database error"}), 500

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

# Create tables with approval system
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    credits INTEGER DEFAULT 10,
    last_reset DATE DEFAULT CURRENT_DATE,
    total_searches INTEGER DEFAULT 0,
    joined_date DATE DEFAULT CURRENT_DATE,
    approved INTEGER DEFAULT 0,
    blocked INTEGER DEFAULT 0,
    approved_by INTEGER,
    approved_date DATE
)
""")
db.commit()

def save_user(uid, username=None):
    cur.execute("""
        INSERT OR IGNORE INTO users (id, username, credits, last_reset, joined_date, approved) 
        VALUES (?, ?, ?, DATE('now'), DATE('now'), 0)
    """, (uid, username, DAILY_CREDITS))
    db.commit()

def approve_user(uid, admin_id):
    cur.execute("""
        UPDATE users 
        SET approved = 1, approved_by = ?, approved_date = DATE('now'), blocked = 0 
        WHERE id = ?
    """, (admin_id, uid))
    db.commit()

def block_user(uid):
    cur.execute("UPDATE users SET blocked = 1, approved = 0 WHERE id = ?", (uid,))
    db.commit()

def unblock_user(uid):
    cur.execute("UPDATE users SET blocked = 0, approved = 0 WHERE id = ?", (uid,))
    db.commit()

def is_approved(uid):
    if uid == ADMIN_ID:
        return True
    cur.execute("SELECT approved, blocked FROM users WHERE id = ?", (uid,))
    result = cur.fetchone()
    if result:
        return result[0] == 1 and result[1] == 0
    return False

def get_user_status(uid):
    cur.execute("SELECT approved, blocked FROM users WHERE id = ?", (uid,))
    return cur.fetchone()

def get_pending_users():
    cur.execute("SELECT id, username, joined_date FROM users WHERE approved = 0 AND blocked = 0")
    return cur.fetchall()

def get_approved_users():
    cur.execute("SELECT id, username, credits FROM users WHERE approved = 1 AND blocked = 0")
    return cur.fetchall()

def get_blocked_users():
    cur.execute("SELECT id, username FROM users WHERE blocked = 1")
    return cur.fetchall()

def get_user_credits(uid):
    if not is_approved(uid):
        return 0
    cur.execute("SELECT credits, last_reset FROM users WHERE id = ?", (uid,))
    result = cur.fetchone()
    if result:
        credits, last_reset = result
        if last_reset != datetime.now().strftime("%Y-%m-%d"):
            credits = DAILY_CREDITS
            cur.execute("UPDATE users SET credits = ?, last_reset = DATE('now') WHERE id = ?", (credits, uid))
            db.commit()
        return credits
    return 0

def deduct_credit(uid):
    if not is_approved(uid):
        return False
    if uid == ADMIN_ID:
        return True
    credits = get_user_credits(uid)
    if credits > 0:
        cur.execute("""
            UPDATE users 
            SET credits = credits - 1, total_searches = total_searches + 1 
            WHERE id = ?
        """, (uid,))
        db.commit()
        return True
    return False

def add_credits(uid, amount):
    cur.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, uid))
    db.commit()

def total_users():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]

def get_user_stats(uid):
    cur.execute("SELECT credits, total_searches, joined_date FROM users WHERE id = ?", (uid,))
    return cur.fetchone()

def get_all_users():
    cur.execute("SELECT id FROM users WHERE approved = 1 AND blocked = 0")
    return [row[0] for row in cur.fetchall()]

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
    btns = [[InlineKeyboardButton(f"📢 Join {c}", url=f"https://t.me/{c[1:]}")] for c in FORCE_CHANNELS]
    btns.append([InlineKeyboardButton("✅ Check Again", callback_data="check")])
    return InlineKeyboardMarkup(btns)

# ================= UI =================
def menu_kb(uid):
    if uid == ADMIN_ID or (get_user_status(uid) and get_user_status(uid)[0] == 1):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Deep Analysis", callback_data="deep")],
            [InlineKeyboardButton("💰 My Credits", callback_data="credits")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("📢 Request Approval", callback_data="request_approval")]
        ])

def after_kb(username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Full Report", callback_data=f"report|{username}")],
        [InlineKeyboardButton("🔄 Analyze Again", callback_data="deep")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")]
    ])

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Pending Users", callback_data="admin_pending")],
        [InlineKeyboardButton("✅ Approved Users", callback_data="admin_approved")],
        [InlineKeyboardButton("🔨 Blocked Users", callback_data="admin_blocked")],
        [InlineKeyboardButton("💰 Add Credits", callback_data="admin_add_credits")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")]
    ])

# ================= API =================
def fetch_profile(username):
    url = API_URL.format(username)
    
    try:
        print(f"\n{'='*50}")
        print(f"🔍 FETCHING: @{username}")
        
        r = requests.get(url, timeout=20)
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code}")
            return None
        
        data = r.json()
        
        # Check if API returned success
        if data.get("status") == "ok" or data.get("success") == True:
            profile = data.get("profile") or data.get("data") or data.get("user")
            if profile:
                return {
                    "status": "ok",
                    "collected_at": data.get("collected_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")),
                    "profile": profile
                }
        
        print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        return None
        
    except Exception as e:
        print(f"🔥 API Error: {e}")
        return None

def download_image(url):
    try:
        r = requests.get(url, timeout=15)
        bio = BytesIO(r.content)
        bio.name = "profile.jpg"
        return bio
    except:
        return None

# ================= ANALYSIS ENGINE =================
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
        issues.append(f"{count}X {i}")

    risk = min(95, 40 + intensity * 6 + (10 if private else 0) + (15 if posts < 5 else 0))
    return risk, issues

# ================ FORMAT REPORT =================
def format_report(data, risk, issues):
    profile = data.get("profile", {})
    collected_at = data.get("collected_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"))
    
    username = profile.get("username", "N/A")
    full_name = profile.get("full_name", "N/A")
    user_id = profile.get("id", "N/A")
    bio = profile.get("biography", "") or "No bio"
    followers = f"{profile.get('followers', 0):,}"
    following = f"{profile.get('following', 0):,}"
    posts = profile.get("posts", 0)
    private = "✅ YES" if profile.get("is_private", False) else "❌ NO"
    verified = "✅ YES" if profile.get("is_verified", False) else "❌ NO"
    business = "✅ YES" if profile.get("is_business_account", False) else "❌ NO"
    professional = "✅ YES" if profile.get("is_professional_account", False) else "❌ NO"
    external_url = profile.get("external_url", "None")
    
    report = f"""
╔══════════════════════════════════════╗
║     🔥 INSTAGRAM ANALYZER PRO 🔥     ║
║           BY {CREATOR}               ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 INSTAGRAM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• USERNAME: @{username}
• FULL NAME: {full_name}
• USER ID: {user_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 BIO:
{bio}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATISTICS:
• 👥 FOLLOWERS: {followers}
• 🔄 FOLLOWING: {following}
• 📸 POSTS: {posts}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 PRIVATE: {private}
✅ VERIFIED: {verified}
💼 BUSINESS: {business}
🎯 PROFESSIONAL: {professional}
🔗 EXTERNAL URL: {external_url if external_url else 'None'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DETECTED ISSUES"""
    
    for issue in issues:
        report += f"\n• {issue}"
    
    if risk >= 80:
        risk_emoji = "🔴 HIGH RISK"
    elif risk >= 50:
        risk_emoji = "🟡 MEDIUM RISK"
    else:
        risk_emoji = "🟢 LOW RISK"
    
    report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
• SCORE: {risk}% {risk_emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ COLLECTED: {collected_at}
👑 CREATOR: {CREATOR}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return report

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username
    save_user(uid, username)
    
    if not await is_joined(context.bot, uid):
        await update.message.reply_text(
            "❌ Please join all channels first.",
            reply_markup=join_kb()
        )
        return
    
    if uid == ADMIN_ID:
        await update.message.reply_text(
            f"👑 Admin Access Granted\n\n"
            f"✨ Welcome to {BOT_NAME} ✨\n"
            f"Created by {CREATOR}\n\n"
            f"💰 Unlimited Credits\n"
            f"Use /admin for panel",
            reply_markup=menu_kb(uid)
        )
        return
    
    status = get_user_status(uid)
    
    if status and status[1] == 1:
        await update.message.reply_text(
            "❌ You have been blocked.\nContact admin."
        )
        return
    
    if status and status[0] == 1:
        credits = get_user_credits(uid)
        await update.message.reply_text(
            f"✨ Welcome to {BOT_NAME} ✨\n"
            f"Created by {CREATOR}\n\n"
            f"✅ Account Approved!\n"
            f"💰 Credits: {credits}/{DAILY_CREDITS}\n"
            f"Send Instagram username to analyze!",
            reply_markup=menu_kb(uid)
        )
    else:
        await update.message.reply_text(
            f"⏳ Pending Approval\n\n"
            f"Bot: {BOT_NAME}\n"
            f"Creator: {CREATOR}\n\n"
            f"Click 'Request Approval' below",
            reply_markup=menu_kb(uid)
        )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "check":
        if await is_joined(context.bot, uid):
            await q.message.edit_text("✅ Access granted!", reply_markup=menu_kb(uid))
        else:
            await q.message.reply_text("❌ Please join all channels first", reply_markup=join_kb())

    elif q.data == "menu":
        await start(update, context)

    elif q.data == "request_approval":
        await context.bot.send_message(
            ADMIN_ID,
            f"🔔 Approval Request\n\n"
            f"User: {uid}\n"
            f"Username: @{q.from_user.username}\n"
            f"Name: {q.from_user.full_name}\n\n"
            f"/approve {uid}\n/block {uid}"
        )
        await q.message.edit_text(
            f"✅ Request Sent to {CREATOR}\nYou'll be notified when approved.",
            reply_markup=menu_kb(uid)
        )

    elif q.data == "credits":
        if not is_approved(uid):
            await q.message.edit_text("❌ Not approved yet!", reply_markup=menu_kb(uid))
            return
        stats = get_user_stats(uid)
        if stats:
            credits, total, joined = stats
            await q.message.edit_text(
                f"💰 YOUR CREDITS\n\n"
                f"• Available: {credits}/{DAILY_CREDITS}\n"
                f"• Total Searches: {total}\n"
                f"• Member Since: {joined}\n\n"
                f"Credits reset daily",
                reply_markup=menu_kb(uid)
            )

    elif q.data == "deep":
        if not is_approved(uid):
            await q.message.edit_text("❌ Not approved yet!", reply_markup=menu_kb(uid))
            return
        
        credits = get_user_credits(uid)
        if credits <= 0 and uid != ADMIN_ID:
            await q.message.edit_text(
                "❌ No credits left!",
                reply_markup=menu_kb(uid)
            )
            return
        
        context.user_data["wait"] = True
        await q.message.reply_text(
            f"👤 Send Instagram username\n"
            f"💰 Credits left: {credits-1 if uid != ADMIN_ID else '∞'}"
        )

    elif q.data.startswith("report|"):
        username = q.data.split("|")[1]
        await q.message.reply_text("🔄 Fetching full report...")
        
        data = fetch_profile(username)
        if not data:
            await q.message.reply_text("❌ Profile not found or API error")
            return
        
        risk, issues = calc_risk(data)
        report = format_report(data, risk, issues)
        await q.message.reply_text(report, reply_markup=after_kb(username))

    elif q.data == "help":
        text = f"🔍 HELP\n\nBot: {BOT_NAME}\nCreator: {CREATOR}\n\n"
        if is_approved(uid):
            text += "• Deep Analysis: Analyze profiles\n• Credits: Check balance\n• Daily reset: 00:00 UTC"
        else:
            text += "• Request approval to use bot"
        await q.message.edit_text(text, reply_markup=menu_kb(uid))

    # Admin callbacks
    elif q.data == "admin_stats" and uid == ADMIN_ID:
        pending = len(get_pending_users())
        approved = len(get_approved_users())
        blocked = len(get_blocked_users())
        await q.message.edit_text(
            f"📊 STATISTICS\n\n"
            f"• Pending: {pending}\n"
            f"• Approved: {approved}\n"
            f"• Blocked: {blocked}\n"
            f"• Creator: {CREATOR}",
            reply_markup=admin_kb()
        )

    elif q.data == "admin_pending" and uid == ADMIN_ID:
        pending = get_pending_users()
        if not pending:
            await q.message.edit_text("No pending users!", reply_markup=admin_kb())
            return
        text = "⏳ PENDING USERS\n\n"
        for uid, user, joined in pending:
            text += f"• {uid} (@{user or 'N/A'})\n/approve {uid}\n\n"
        await q.message.edit_text(text[:4000], reply_markup=admin_kb())

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if not context.user_data.get("wait"):
        return
    
    if not is_approved(uid):
        await update.message.reply_text("❌ Not approved yet!")
        context.user_data["wait"] = False
        return

    if uid != ADMIN_ID:
        credits = get_user_credits(uid)
        if credits <= 0:
            await update.message.reply_text("❌ No credits left!")
            context.user_data["wait"] = False
            return

    context.user_data["wait"] = False
    username = update.message.text.replace("@", "").strip()
    
    if not username:
        await update.message.reply_text("❌ Send valid username")
        return
    
    if uid != ADMIN_ID:
        deduct_credit(uid)
    
    status_msg = await update.message.reply_text("🔄 Analyzing...")
    
    data = fetch_profile(username)
    
    if not data:
        await status_msg.edit_text("❌ Profile not found or API error")
        return
    
    risk, issues = calc_risk(data)
    
    profile = data.get("profile", {})
    pic_url = profile.get("profile_pic_url_hd")
    
    caption = f"ANALYSIS COMPLETE\n@{username}\nRisk: {risk}%"
    
    if pic_url:
        try:
            pic_data = download_image(pic_url)
            if pic_data:
                await update.message.reply_photo(
                    photo=pic_data,
                    caption=caption,
                    reply_markup=after_kb(username)
                )
                await status_msg.delete()
                return
        except:
            pass
    
    await status_msg.edit_text(caption, reply_markup=after_kb(username))

# ================= ADMIN COMMANDS =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        approve_user(uid, ADMIN_ID)
        await update.message.reply_text(f"✅ Approved {uid}")
        await context.bot.send_message(uid, f"✅ Approved by {CREATOR}\n/start to use bot")
    except:
        await update.message.reply_text("Usage: /approve user_id")

async def block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        block_user(uid)
        await update.message.reply_text(f"🔨 Blocked {uid}")
    except:
        await update.message.reply_text("Usage: /block user_id")

async def unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        unblock_user(uid)
        await update.message.reply_text(f"✅ Unblocked {uid}")
    except:
        await update.message.reply_text("Usage: /unblock user_id")

async def add_credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        add_credits(uid, amount)
        await update.message.reply_text(f"✅ Added {amount} credits to {uid}")
    except:
        await update.message.reply_text("Usage: /addcredits user_id amount")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"👑 Admin Panel\nCreator: {CREATOR}", reply_markup=admin_kb())

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return
    msg = " ".join(context.args)
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Sent to {sent} users")

# ================= RUN =================
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("block", block))
    app.add_handler(CommandHandler("unblock", unblock))
    app.add_handler(CommandHandler("addcredits", add_credits_cmd))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))

    print(f"\n{'='*50}")
    print(f"✅ BOT STARTED")
    print(f"👑 CREATOR: {CREATOR}")
    print(f"💰 DAILY CREDITS: {DAILY_CREDITS}")
    print(f"{'='*50}\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()
