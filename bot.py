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

# Creator Credit
CREATOR = "@proxyfxc"
DEVELOPER = "@E_commerceseller"

# Credit System
DAILY_CREDITS = 10

# ================= FLASK APP =================
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "Instagram Analyzer Pro",
        "creator": CREATOR,
        "developer": DEVELOPER,
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
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE credits > 0")
        active_users = cur.fetchone()[0]
        return jsonify({
            "total_users": total_users,
            "active_users": active_users,
            "creator": CREATOR,
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

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    credits INTEGER DEFAULT 10,
    last_reset DATE DEFAULT CURRENT_DATE,
    total_searches INTEGER DEFAULT 0,
    joined_date DATE DEFAULT CURRENT_DATE
)
""")
db.commit()

def save_user(uid):
    cur.execute("""
        INSERT OR IGNORE INTO users (id, credits, last_reset, joined_date) 
        VALUES (?, ?, DATE('now'), DATE('now'))
    """, (uid, DAILY_CREDITS))
    db.commit()

def get_user_credits(uid):
    cur.execute("SELECT credits, last_reset FROM users WHERE id = ?", (uid,))
    result = cur.fetchone()
    if result:
        credits, last_reset = result
        # Reset credits if new day
        if last_reset != datetime.now().strftime("%Y-%m-%d"):
            credits = DAILY_CREDITS
            cur.execute("UPDATE users SET credits = ?, last_reset = DATE('now') WHERE id = ?", (credits, uid))
            db.commit()
        return credits
    return 0

def deduct_credit(uid):
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
    cur.execute("SELECT id FROM users")
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
def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Deep Analysis", callback_data="deep")],
        [InlineKeyboardButton("💰 My Credits", callback_data="credits")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
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
        [InlineKeyboardButton("👥 Users List", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Add Credits", callback_data="admin_add_credits")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")]
    ])

# ================= API =================
def fetch_profile(username):
    url = API_URL.format(username)
    
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            print(f"HTTP Error: {r.status_code}")
            return None
        
        data = r.json()
        print(f"API Response for @{username}: {data}")
        
        if data.get("status") != "ok":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        profile = data.get("profile", {})
        if not profile:
            print("No profile data found")
            return None
        
        return {
            "status": "ok",
            "collected_at": data.get("collected_at", ""),
            "developer": DEVELOPER,
            "profile": profile
        }
        
    except Exception as e:
        print(f"API Error: {e}")
        return None

def download_image(url):
    """Download image from URL"""
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
    """API response ko stylish box format mein karo - exactly like screenshot"""
    
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
    
    # Format exactly like screenshot
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
💻 DEVELOPER: {DEVELOPER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return report

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)

    if not await is_joined(context.bot, uid):
        await update.message.reply_text(
            "❌ Please join all channels first.",
            reply_markup=join_kb()
        )
        return

    credits = get_user_credits(uid)
    await update.message.reply_text(
        f"✨ Welcome to Insta Analyzer Pro ✨\n"
        f"👤 Created by {CREATOR}\n\n"
        f"💰 Your Credits: {credits}/{DAILY_CREDITS}\n"
        f"Send any Instagram username to analyze!",
        reply_markup=menu_kb()
    )

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "check":
        if await is_joined(context.bot, uid):
            await q.message.edit_text("✅ Access granted!", reply_markup=menu_kb())
        else:
            await q.message.reply_text("❌ Please join all channels first", reply_markup=join_kb())

    elif q.data == "menu":
        credits = get_user_credits(uid)
        await q.message.edit_text(
            f"🏠 Main Menu\n💰 Credits: {credits}/{DAILY_CREDITS}",
            reply_markup=menu_kb()
        )

    elif q.data == "credits":
        credits, total, joined = get_user_stats(uid)
        await q.message.edit_text(
            f"💰 YOUR CREDITS\n\n"
            f"• Available: {credits}/{DAILY_CREDITS}\n"
            f"• Total Searches: {total}\n"
            f"• Member Since: {joined}\n\n"
            f"Credits reset daily at 00:00 UTC",
            reply_markup=menu_kb()
        )

    elif q.data == "deep":
        credits = get_user_credits(uid)
        if credits <= 0:
            await q.message.edit_text(
                "❌ No credits left!\n"
                "Wait for daily reset or contact admin.",
                reply_markup=menu_kb()
            )
            return
        context.user_data["wait"] = True
        await q.message.reply_text(
            f"👤 Send Instagram username (with or without @)\n"
            f"💰 Credits left: {credits-1}"
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
        await q.message.edit_text(
            "🔍 *HOW TO USE*\n"
            "• Click 'Deep Analysis'\n"
            "• Send Instagram username\n"
            "• Get detailed report\n\n"
            "💰 *CREDIT SYSTEM*\n"
            f"• {DAILY_CREDITS} free credits daily\n"
            "• Resets at midnight UTC\n"
            "• Admin can add more\n\n"
            "👑 *CREATOR*\n"
            f"• {CREATOR}\n"
            f"• Developer: {DEVELOPER}",
            parse_mode='Markdown',
            reply_markup=menu_kb()
        )

    # Admin callbacks
    elif q.data == "admin_stats" and uid == ADMIN_ID:
        total = total_users()
        active = sum(1 for u in get_all_users() if get_user_credits(u) > 0)
        await q.message.edit_text(
            f"📊 BOT STATISTICS\n\n"
            f"• Total Users: {total}\n"
            f"• Active Today: {active}\n"
            f"• Daily Credits: {DAILY_CREDITS}\n"
            f"• Creator: {CREATOR}\n",
            reply_markup=admin_kb()
        )

    elif q.data == "admin_users" and uid == ADMIN_ID:
        users = get_all_users()[:10]  # Show first 10
        text = "👥 RECENT USERS\n\n"
        for u in users:
            cred = get_user_credits(u)
            text += f"• {u}: {cred} credits\n"
        await q.message.edit_text(text, reply_markup=admin_kb())

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if not context.user_data.get("wait"):
        return

    # Check credits
    credits = get_user_credits(uid)
    if credits <= 0 and uid != ADMIN_ID:  # Admin has unlimited
        await update.message.reply_text(
            "❌ No credits left!\n"
            "Wait for daily reset or contact admin.",
            reply_markup=menu_kb()
        )
        context.user_data["wait"] = False
        return

    context.user_data["wait"] = False
    username = update.message.text.replace("@", "").strip()
    
    if not username:
        await update.message.reply_text("❌ Please send a valid username")
        return
    
    # Deduct credit (except admin)
    if uid != ADMIN_ID:
        deduct_credit(uid)
    
    status_msg = await update.message.reply_text("🔄 Analyzing Instagram profile...")
    
    # Fetch profile data
    data = fetch_profile(username)
    
    if not data:
        await status_msg.edit_text("❌ Profile not found or API error")
        return
    
    # Calculate risk
    risk, issues = calc_risk(data)
    
    # Get profile pic URL
    profile = data.get("profile", {})
    pic_url = profile.get("profile_pic_url_hd")
    
    # Format exactly like screenshot
    caption = f"ANALYSIS COMPLETE\n@{username}\nRisk: {risk}%"
    
    # Try to send with profile pic
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
        except Exception as e:
            print(f"Photo error: {e}")
    
    # Send text-only response
    await status_msg.edit_text(caption, reply_markup=after_kb(username))

# ================= ADMIN COMMANDS =================
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    await update.message.reply_text(f"👥 Total users: {total_users()}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    msg = " ".join(context.args)
    users = get_all_users()
    sent = 0
    failed = 0

    for uid in users:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users\n❌ Failed: {failed}")

async def add_credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
        add_credits(user_id, amount)
        await update.message.reply_text(f"✅ Added {amount} credits to {user_id}")
    except:
        await update.message.reply_text("Usage: /addcredits user_id amount")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    credits, total, joined = get_user_stats(uid)
    await update.message.reply_text(
        f"📊 YOUR STATS\n\n"
        f"• Credits: {credits}/{DAILY_CREDITS}\n"
        f"• Searches: {total}\n"
        f"• Joined: {joined}\n"
        f"• Creator: {CREATOR}"
    )

# ================= RUN =================
def main():
    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addcredits", add_credits_cmd))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("stats", my_stats))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))

    print(f"✅ Bot started! Press Ctrl+C to stop")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"👤 Creator: {CREATOR}")
    print(f"💰 Daily credits: {DAILY_CREDITS}")
    print(f"🌐 Flask running on port {os.environ.get('PORT', 8080)}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
