# ================= INSTAGRAM ANALYZER PRO =================
# DEVELOPER: @proxyfxc
# VERSION: 28.0 (RENDER DEPLOYMENT READY)
# ==========================================================

import requests
import json
import random
import hashlib
import sqlite3
import re
import asyncio
import os
import sys
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

# ================= CONFIGURATION =================

# ENVIRONMENT VARIABLES (Render me set karna)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617750252:AAGQNV4D22ekCPjt41aMgdbh6hUJicC79sg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8554863978"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@proxyfxc")

# API CONFIGURATION
API_URL = "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187"
API_TIMEOUT = 10

# FORCE JOIN CHANNELS
FORCE_CHANNELS = ["@midnight_xaura", "@proxydominates"]

# DATABASE FILE
DB_FILE = "users.db"

# SECURITY CODES CONFIG
TOTAL_CODES = 150
CODES_FILE = "security_codes.txt"

# ================= DATABASE SETUP =================

def init_database():
    """INITIALIZE DATABASE WITH ALL TABLES"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    
    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
        ID INTEGER PRIMARY KEY,
        USERNAME TEXT,
        FIRST_NAME TEXT,
        JOINED_DATE TEXT,
        IS_APPROVED INTEGER DEFAULT 0,
        IS_PREMIUM INTEGER DEFAULT 0,
        SUBSCRIPTION_END TEXT,
        TOTAL_ANALYSIS INTEGER DEFAULT 0,
        IS_BLOCKED INTEGER DEFAULT 0,
        REFERRALS INTEGER DEFAULT 0,
        REFERRED_BY INTEGER,
        PREMIUM_ACTIVATED_DATE TEXT,
        REMAINING_SEARCHES INTEGER DEFAULT 0
    )
    """)
    
    # PENDING APPROVALS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS PENDING_APPROVALS (
        USER_ID INTEGER PRIMARY KEY,
        USERNAME TEXT,
        FIRST_NAME TEXT,
        REQUEST_TIME TEXT
    )
    """)
    
    # REFERRAL TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS REFERRALS (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        USER_ID INTEGER,
        REFERRED_USER_ID INTEGER,
        REFERRED_USERNAME TEXT,
        REFERRAL_DATE TEXT,
        STATUS TEXT DEFAULT 'PENDING'
    )
    """)
    
    # INSTAGRAM CACHE TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS INSTA_CACHE (
        USERNAME TEXT PRIMARY KEY,
        DATA TEXT,
        COLLECTED_TIME TEXT
    )
    """)
    
    # STATS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS STATS (
        ID INTEGER PRIMARY KEY CHECK (ID=1),
        TOTAL_USERS INTEGER DEFAULT 0,
        TOTAL_ANALYSES INTEGER DEFAULT 0,
        TOTAL_PREMIUM INTEGER DEFAULT 0,
        TOTAL_REFERRALS INTEGER DEFAULT 0,
        LAST_RESTART TEXT,
        TOTAL_CODES_USED INTEGER DEFAULT 0,
        TOTAL_CODES_GENERATED INTEGER DEFAULT 0
    )
    """)
    
    # SECURITY CODES TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS SECURITY_CODES (
        CODE TEXT PRIMARY KEY,
        IS_USED INTEGER DEFAULT 0,
        USED_BY INTEGER,
        USED_DATE TEXT,
        GENERATED_DATE TEXT
    )
    """)
    
    # INSERT STATS IF NOT EXISTS
    cur.execute("INSERT OR IGNORE INTO STATS (ID, LAST_RESTART, TOTAL_CODES_GENERATED) VALUES (1, ?, 0)", 
                (datetime.now().isoformat(),))
    
    conn.commit()
    
    # GENERATE SECURITY CODES IF NEEDED
    cur.execute("SELECT COUNT(*) FROM SECURITY_CODES")
    count = cur.fetchone()[0]
    
    if count < TOTAL_CODES:
        generate_security_codes(cur, conn)
    
    print("✅ DATABASE INITIALIZED")
    return conn, cur

def generate_security_codes(cur, conn):
    """GENERATE 150 UNIQUE 4-DIGIT CODES"""
    print("🔄 GENERATING SECURITY CODES...")
    
    # DELETE OLD CODES
    cur.execute("DELETE FROM SECURITY_CODES")
    
    # GENERATE NEW CODES
    codes = set()
    while len(codes) < TOTAL_CODES:
        code = str(random.randint(1000, 9999))
        codes.add(code)
    
    # INSERT INTO DATABASE
    for code in codes:
        cur.execute("""
            INSERT INTO SECURITY_CODES (CODE, GENERATED_DATE)
            VALUES (?, ?)
        """, (code, datetime.now().isoformat()))
    
    # UPDATE STATS
    cur.execute("UPDATE STATS SET TOTAL_CODES_GENERATED = ? WHERE ID=1", (len(codes),))
    
    conn.commit()
    
    # SAVE TO FILE
    try:
        with open(CODES_FILE, 'w') as f:
            f.write("INSTAGRAM ANALYZER PRO - SECURITY CODES\n")
            f.write("=" * 40 + "\n")
            f.write(f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"TOTAL CODES: {len(codes)}\n")
            f.write("=" * 40 + "\n\n")
            
            for i, code in enumerate(sorted(codes), 1):
                f.write(f"{i:3d}. {code}\n")
    except:
        pass
    
    print(f"✅ GENERATED {len(codes)} SECURITY CODES")

# INITIALIZE DATABASE
DB, CUR = init_database()

# ================= LOGGING SETUP =================

def log_error(error: str, location: str):
    """LOG ERRORS FOR DEBUGGING"""
    print(f"❌ ERROR AT {location}: {error}")
    try:
        with open("error.log", "a") as f:
            f.write(f"{datetime.now()} - {location}: {error}\n")
    except:
        pass

# ================= YOUR ORIGINAL RISK ENGINE =================

def CALC_RISK(profile: Dict) -> Tuple[int, List[str]]:
    """ORIGINAL RISK CALCULATION ENGINE"""
    try:
        username = profile.get("username", "user")
        bio = (profile.get("biography") or "").lower()
        private = profile.get("is_private", False)
        posts = int(profile.get("posts") or 0)

        seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
        rnd = random.Random(seed)

        POOL = [
            "SCAM", "SPAM", "NUDITY",
            "HATE", "HARASSMENT",
            "BULLYING", "VIOLENCE",
            "TERRORISM"
        ]

        if any(x in bio for x in ["music", "rapper", "artist", "singer"]):
            POOL += ["DRUGS", "DRUGS"]

        if private and posts == 0:
            POOL += ["SCAM", "SCAM", "SCAM"]

        INCLUDE_SELF = private and rnd.choice([True, False])
        if INCLUDE_SELF:
            POOL.append("SELF")
            POOL = [i for i in POOL if i != "HATE"]

        if rnd.random() < 0.15:
            POOL.append("WEAPONS")

        rnd.shuffle(POOL)
        SELECTED = list(dict.fromkeys(POOL))[:rnd.randint(1, 3)]

        ISSUES, INTENSITY = [], 0
        for i in SELECTED:
            COUNT = rnd.randint(3, 4) if i == "WEAPONS" else rnd.randint(1, 4)
            INTENSITY += COUNT
            ISSUES.append(f"{COUNT}X {i}")

        RISK = min(95, 40 + INTENSITY * 6 + (10 if private else 0) + (10 if posts == 0 else 0))
        return RISK, ISSUES
    except Exception as e:
        log_error(str(e), "CALC_RISK")
        return 50, ["1X ERROR"]

# ================= API FUNCTION =================

def GET_INSTAGRAM_DATA(username: str) -> Optional[Dict]:
    """FETCH INSTAGRAM DATA FROM API"""
    try:
        url = API_URL.format(username)
        response = requests.get(url, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return data.get('profile', {})
        return None
    except Exception as e:
        log_error(str(e), "GET_INSTAGRAM_DATA")
        return None

# ================= FORMAT REPORT =================

def FORMAT_REPORT(username: str, profile: Dict, risk: int, issues: List[str]) -> str:
    """PROFESSIONAL REPORT WITH @proxyfxc BRANDING"""
    try:
        if risk < 30:
            RISK_LEVEL = "🟢 LOW RISK"
        elif risk < 60:
            RISK_LEVEL = "🟡 MEDIUM RISK"
        else:
            RISK_LEVEL = "🔴 HIGH RISK"
        
        FOLLOWERS = f"{profile.get('followers', 0):,}"
        FOLLOWING = f"{profile.get('following', 0):,}"
        POSTS = f"{profile.get('posts', 0):,}"
        
        CURRENT_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        REPORT = f"""
╔══════════════════════════════════════╗
║     🔥 INSTAGRAM ANALYZER PRO 🔥     ║
║           BY @proxyfxc               ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 INSTAGRAM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• USERNAME: @{username}
• FULL NAME: {profile.get('full_name', 'N/A')}
• USER ID: {profile.get('id', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 BIO:
{profile.get('biography', 'NO BIO AVAILABLE')[:200]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATISTICS:
• 👥 FOLLOWERS: {FOLLOWERS}
• 🔄 FOLLOWING: {FOLLOWING}
• 📸 POSTS: {POSTS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 PRIVATE: {'✅ YES' if profile.get('is_private') else '❌ NO'}
✅ VERIFIED: {'✅ YES' if profile.get('is_verified') else '❌ NO'}
💼 BUSINESS: {'✅ YES' if profile.get('is_business_account') else '❌ NO'}
🔗 EXTERNAL URL: {profile.get('external_url', 'NONE')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DETECTED ISSUES
"""
        
        if issues:
            for issue in issues:
                REPORT += f"• {issue}\n"
        else:
            REPORT += "• NO ISSUES DETECTED\n"
        
        REPORT += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
• SCORE: {risk}% {RISK_LEVEL}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ COLLECTED: {CURRENT_TIME}
💻 DEVELOPER: @proxyfxc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return REPORT
    except Exception as e:
        log_error(str(e), "FORMAT_REPORT")
        return "❌ ERROR GENERATING REPORT"

# ================= SECURITY CODE FUNCTIONS =================

def VERIFY_CODE(code: str, user_id: int) -> Tuple[bool, str]:
    """VERIFY IF CODE IS VALID AND NOT USED"""
    try:
        # ADMIN BYPASS
        if user_id == ADMIN_ID:
            return True, "ADMIN_BYPASS"
        
        CUR.execute("SELECT IS_USED FROM SECURITY_CODES WHERE CODE=?", (code,))
        result = CUR.fetchone()
        
        if not result:
            return False, "❌ INVALID CODE! CONTACT @proxyfxc"
        
        if result[0] == 1:
            return False, "❌ CODE ALREADY USED! CONTACT @proxyfxc"
        
        # MARK CODE AS USED
        CUR.execute("""
            UPDATE SECURITY_CODES 
            SET IS_USED=1, USED_BY=?, USED_DATE=? 
            WHERE CODE=?
        """, (user_id, datetime.now().isoformat(), code))
        
        # ADD 1 SEARCH TO USER
        CUR.execute("""
            UPDATE USERS 
            SET REMAINING_SEARCHES = REMAINING_SEARCHES + 1 
            WHERE ID=?
        """, (user_id,))
        
        # UPDATE STATS
        CUR.execute("""
            UPDATE STATS 
            SET TOTAL_CODES_USED = TOTAL_CODES_USED + 1 
            WHERE ID=1
        """)
        
        DB.commit()
        
        CUR.execute("SELECT REMAINING_SEARCHES FROM USERS WHERE ID=?", (user_id,))
        remaining = CUR.fetchone()[0]
        
        return True, f"✅ CODE ACCEPTED! YOU HAVE {remaining} SEARCH{'ES' if remaining != 1 else ''} LEFT."
        
    except Exception as e:
        log_error(str(e), "VERIFY_CODE")
        return False, "❌ ERROR VERIFYING CODE! CONTACT @proxyfxc"

def CHECK_SEARCH_AVAILABLE(user_id: int) -> Tuple[bool, int, str]:
    """CHECK IF USER HAS SEARCHES AVAILABLE"""
    try:
        if user_id == ADMIN_ID:
            return True, 999, "ADMIN"
        
        CUR.execute("SELECT REMAINING_SEARCHES FROM USERS WHERE ID=?", (user_id,))
        result = CUR.fetchone()
        
        if not result:
            return False, 0, "NO_USER"
        
        remaining = result[0]
        
        if remaining > 0:
            return True, remaining, "AVAILABLE"
        else:
            return False, 0, "NO_SEARCHES"
            
    except Exception as e:
        log_error(str(e), "CHECK_SEARCH_AVAILABLE")
        return False, 0, "ERROR"

def USE_ONE_SEARCH(user_id: int) -> bool:
    """USE ONE SEARCH FROM USER'S BALANCE"""
    try:
        if user_id == ADMIN_ID:
            return True
        
        CUR.execute("""
            UPDATE USERS 
            SET REMAINING_SEARCHES = REMAINING_SEARCHES - 1,
                TOTAL_ANALYSIS = TOTAL_ANALYSIS + 1
            WHERE ID=? AND REMAINING_SEARCHES > 0
        """, (user_id,))
        DB.commit()
        return CUR.rowcount > 0
    except Exception as e:
        log_error(str(e), "USE_ONE_SEARCH")
        return False

# ================= DATABASE FUNCTIONS =================

def SAVE_USER(user_id: int, username: str, first_name: str):
    """SAVE USER TO DATABASE"""
    try:
        CUR.execute("""
            INSERT OR IGNORE INTO USERS 
            (ID, USERNAME, FIRST_NAME, JOINED_DATE, IS_APPROVED, IS_PREMIUM, REFERRALS, REMAINING_SEARCHES)
            VALUES (?, ?, ?, ?, 0, 0, 0, 0)
        """, (user_id, username, first_name, datetime.now().isoformat()))
        DB.commit()
    except Exception as e:
        log_error(str(e), "SAVE_USER")

def CHECK_ACCESS(user_id: int) -> Tuple[bool, str]:
    """CHECK USER ACCESS LEVEL"""
    try:
        if user_id == ADMIN_ID:
            return True, "ADMIN"
        
        CUR.execute("""
            SELECT IS_APPROVED, IS_BLOCKED, IS_PREMIUM, SUBSCRIPTION_END 
            FROM USERS WHERE ID=?
        """, (user_id,))
        RESULT = CUR.fetchone()
        
        if not RESULT:
            return False, "NOT_REGISTERED"
        
        IS_APPROVED, IS_BLOCKED, IS_PREMIUM, SUB_END = RESULT
        
        if IS_BLOCKED == 1:
            return False, "BLOCKED"
        
        if IS_APPROVED == 0:
            return False, "PENDING_APPROVAL"
        
        return True, "APPROVED"
    except Exception as e:
        log_error(str(e), "CHECK_ACCESS")
        return False, "ERROR"

def APPROVE_USER(user_id: int) -> bool:
    """APPROVE USER"""
    try:
        CUR.execute("UPDATE USERS SET IS_APPROVED=1 WHERE ID=?", (user_id,))
        CUR.execute("DELETE FROM PENDING_APPROVALS WHERE USER_ID=?", (user_id,))
        DB.commit()
        return True
    except Exception as e:
        log_error(str(e), "APPROVE_USER")
        return False

# ================= FORCE JOIN CHECK =================

async def CHECK_JOINED(bot, user_id: int) -> bool:
    """CHECK IF USER JOINED ALL CHANNELS"""
    try:
        for channel in FORCE_CHANNELS:
            try:
                MEMBER = await bot.get_chat_member(channel, user_id)
                if MEMBER.status in ['left', 'kicked']:
                    return False
            except TelegramError:
                return False
        return True
    except Exception as e:
        log_error(str(e), "CHECK_JOINED")
        return False

def FORCE_JOIN_KEYBOARD() -> InlineKeyboardMarkup:
    """FORCE JOIN KEYBOARD"""
    BUTTONS = []
    for ch in FORCE_CHANNELS:
        BUTTONS.append([InlineKeyboardButton(f"📢 JOIN {ch}", url=f"https://t.me/{ch[1:]}")])
    BUTTONS.append([InlineKeyboardButton("✅ CHECK AGAIN", callback_data="check")])
    return InlineKeyboardMarkup(BUTTONS)

# ================= KEYBOARDS =================

def MAIN_KEYBOARD(is_admin: bool = False) -> InlineKeyboardMarkup:
    """MAIN MENU KEYBOARD"""
    BUTTONS = [
        [InlineKeyboardButton("🔍 DEEP ANALYSIS", callback_data="deep")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="stats")],
        [InlineKeyboardButton("🎫 USE CODE", callback_data="use_code")],
        [InlineKeyboardButton("❓ HELP", callback_data="help")]
    ]
    
    if is_admin:
        BUTTONS.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
    
    return InlineKeyboardMarkup(BUTTONS)

def AFTER_ANALYSIS_KEYBOARD(username: str) -> InlineKeyboardMarkup:
    """AFTER ANALYSIS KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 NEW ANALYSIS", callback_data="deep")],
        [InlineKeyboardButton("🎫 USE CODE", callback_data="use_code")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="menu")]
    ])

def ADMIN_KEYBOARD() -> InlineKeyboardMarkup:
    """ADMIN PANEL KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats"),
         InlineKeyboardButton("🎫 CODES", callback_data="admin_codes")],
        [InlineKeyboardButton("⏳ PENDING", callback_data="admin_pending"),
         InlineKeyboardButton("✅ APPROVE", callback_data="admin_approve")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="menu")]
    ])

# ================= HANDLERS =================

async def START(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START COMMAND HANDLER"""
    try:
        USER = update.effective_user
        SAVE_USER(USER.id, USER.username, USER.first_name)
        
        if not await CHECK_JOINED(context.bot, USER.id):
            await update.message.reply_text(
                "❌ **PLEASE JOIN ALL CHANNELS FIRST!**",
                parse_mode='Markdown',
                reply_markup=FORCE_JOIN_KEYBOARD()
            )
            return
        
        ACCESS, STATUS = CHECK_ACCESS(USER.id)
        
        if STATUS == "PENDING_APPROVAL" and USER.id != ADMIN_ID:
            CUR.execute("""
                INSERT OR REPLACE INTO PENDING_APPROVALS 
                VALUES (?, ?, ?, ?)
            """, (USER.id, USER.username, USER.first_name, datetime.now().isoformat()))
            DB.commit()
            
            await update.message.reply_text(
                "⏳ **REQUEST SENT TO ADMIN!**\n\nWAIT FOR APPROVAL.",
                parse_mode='Markdown'
            )
            return
        
        AVAILABLE, BALANCE, _ = CHECK_SEARCH_AVAILABLE(USER.id)
        
        WELCOME = f"""
╔════════════════════════════════╗
║    🔥 INSTAGRAM ANALYZER 🔥    ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

👋 WELCOME {USER.first_name}!
🎫 SEARCHES LEFT: {BALANCE if AVAILABLE else 0}

USE CODE TO GET SEARCHES!
"""
        
        await update.message.reply_text(
            WELCOME,
            reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
        )
        
    except Exception as e:
        log_error(str(e), "START")

async def BUTTON_CALLBACK(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BUTTON CALLBACK HANDLER"""
    try:
        QUERY = update.callback_query
        USER = QUERY.from_user
        await QUERY.answer()
        
        if QUERY.data == "check":
            if await CHECK_JOINED(context.bot, USER.id):
                await QUERY.message.edit_text("✅ ACCESS GRANTED!", reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID))
            else:
                await QUERY.message.edit_text("❌ NOT JOINED!", reply_markup=FORCE_JOIN_KEYBOARD())
        
        elif QUERY.data == "menu":
            AVAILABLE, BALANCE, _ = CHECK_SEARCH_AVAILABLE(USER.id)
            await QUERY.message.edit_text(
                f"🏠 MAIN MENU\n\n🎫 SEARCHES: {BALANCE if AVAILABLE else 0}",
                reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
            )
        
        elif QUERY.data == "use_code":
            context.user_data['mode'] = 'enter_code'
            await QUERY.message.edit_text(
                "🎫 **ENTER 4-DIGIT CODE:**\n\nEXAMPLE: `4512`",
                parse_mode='Markdown'
            )
        
        elif QUERY.data == "deep":
            AVAILABLE, BALANCE, STATUS = CHECK_SEARCH_AVAILABLE(USER.id)
            
            if not AVAILABLE:
                await QUERY.message.edit_text(
                    "❌ **NO SEARCHES!**\n\nUSE A CODE FIRST.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🎫 USE CODE", callback_data="use_code")
                    ]])
                )
                return
            
            context.user_data['mode'] = 'deep'
            await QUERY.message.edit_text(
                f"🔍 **SEND USERNAME**\n🎫 LEFT: {BALANCE}\n\nEXAMPLE: `cristiano`",
                parse_mode='Markdown'
            )
        
        elif QUERY.data == "stats":
            CUR.execute("SELECT TOTAL_ANALYSIS, REMAINING_SEARCHES FROM USERS WHERE ID=?", (USER.id,))
            stats = CUR.fetchone() or (0, 0)
            
            await QUERY.message.edit_text(
                f"📊 **YOUR STATS**\n\n"
                f"🆔 ID: `{USER.id}`\n"
                f"📈 ANALYSES: {stats[0]}\n"
                f"🎫 SEARCHES: {stats[1]}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="menu")
                ]])
            )
        
        elif QUERY.data == "help":
            await QUERY.message.edit_text(
                "❓ **HELP**\n\n"
                "1. GET CODE FROM @proxyfxc\n"
                "2. USE CODE TO GET SEARCHES\n"
                "3. ANALYZE INSTAGRAM PROFILES",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="menu")
                ]])
            )
        
        # ADMIN BUTTONS
        elif QUERY.data == "admin" and USER.id == ADMIN_ID:
            CUR.execute("SELECT COUNT(*) FROM SECURITY_CODES WHERE IS_USED=0")
            unused = CUR.fetchone()[0]
            
            await QUERY.message.edit_text(
                f"👑 **ADMIN PANEL**\n\n🎫 AVAILABLE CODES: {unused}",
                parse_mode='Markdown',
                reply_markup=ADMIN_KEYBOARD()
            )
        
        elif QUERY.data == "admin_stats" and USER.id == ADMIN_ID:
            CUR.execute("SELECT COUNT(*) FROM USERS")
            total_users = CUR.fetchone()[0]
            CUR.execute("SELECT SUM(REMAINING_SEARCHES) FROM USERS")
            total_searches = CUR.fetchone()[0] or 0
            CUR.execute("SELECT TOTAL_CODES_USED FROM STATS WHERE ID=1")
            codes_used = CUR.fetchone()[0] or 0
            
            await QUERY.message.edit_text(
                f"📊 **STATISTICS**\n\n"
                f"👥 USERS: {total_users}\n"
                f"🎫 SEARCHES: {total_searches}\n"
                f"✅ CODES USED: {codes_used}",
                parse_mode='Markdown',
                reply_markup=ADMIN_KEYBOARD()
            )
        
        elif QUERY.data == "admin_codes" and USER.id == ADMIN_ID:
            CUR.execute("SELECT CODE FROM SECURITY_CODES WHERE IS_USED=0 LIMIT 10")
            codes = CUR.fetchall()
            
            text = "🎫 **AVAILABLE CODES:**\n\n"
            for code in codes:
                text += f"`{code[0]}` "
            
            text += f"\n\n📁 FILE: `{CODES_FILE}`"
            
            await QUERY.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 GENERATE NEW", callback_data="admin_gen_codes")],
                    [InlineKeyboardButton("⬅️ BACK", callback_data="admin")]
                ])
            )
        
        elif QUERY.data == "admin_gen_codes" and USER.id == ADMIN_ID:
            generate_security_codes(CUR, DB)
            await QUERY.message.edit_text("✅ NEW CODES GENERATED!", reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "admin_pending" and USER.id == ADMIN_ID:
            CUR.execute("SELECT USER_ID, USERNAME FROM PENDING_APPROVALS")
            pending = CUR.fetchall()
            
            if not pending:
                await QUERY.message.edit_text("✅ NO PENDING REQUESTS!", reply_markup=ADMIN_KEYBOARD())
                return
            
            text = "⏳ **PENDING APPROVALS:**\n\n"
            for uid, uname in pending:
                text += f"`{uid}` - @{uname}\n"
            
            text += "\nUSE /approve USER_ID"
            
            await QUERY.message.edit_text(text, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "admin_approve" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'approve'
            await QUERY.message.edit_text(
                "✅ **SEND USER ID TO APPROVE:**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="admin")
                ]])
            )
        
        elif QUERY.data == "admin_broadcast" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'broadcast'
            await QUERY.message.edit_text(
                "📢 **SEND MESSAGE TO BROADCAST:**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="admin")
                ]])
            )
        
    except Exception as e:
        log_error(str(e), "BUTTON_CALLBACK")

async def HANDLE_MESSAGES(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MESSAGE HANDLER"""
    try:
        USER = update.effective_user
        MSG = update.message
        
        if not USER or not MSG:
            return
        
        if not await CHECK_JOINED(context.bot, USER.id):
            await MSG.reply_text("❌ JOIN CHANNELS FIRST!", reply_markup=FORCE_JOIN_KEYBOARD())
            return
        
        ACCESS, STATUS = CHECK_ACCESS(USER.id)
        if not ACCESS and USER.id != ADMIN_ID:
            await MSG.reply_text(f"⏳ PENDING APPROVAL!")
            return
        
        # CODE ENTRY
        if context.user_data.get('mode') == 'enter_code':
            CODE = MSG.text.strip()
            
            if not CODE.isdigit() or len(CODE) != 4:
                await MSG.reply_text("❌ **ENTER 4-DIGIT CODE!**", parse_mode='Markdown')
                return
            
            SUCCESS, MESSAGE = VERIFY_CODE(CODE, USER.id)
            await MSG.reply_text(MESSAGE, reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID))
            context.user_data['mode'] = None
            return
        
        # DEEP ANALYSIS
        if context.user_data.get('mode') == 'deep':
            AVAILABLE, BALANCE, _ = CHECK_SEARCH_AVAILABLE(USER.id)
            
            if not AVAILABLE:
                context.user_data['mode'] = None
                await MSG.reply_text("❌ NO SEARCHES!", reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID))
                return
            
            USERNAME = MSG.text.replace('@', '').strip().lower()
            
            if not re.match(r'^[a-zA-Z0-9._]+$', USERNAME):
                await MSG.reply_text("❌ INVALID USERNAME!")
                return
            
            if not USE_ONE_SEARCH(USER.id) and USER.id != ADMIN_ID:
                await MSG.reply_text("❌ ERROR!")
                return
            
            status_msg = await MSG.reply_text(f"🔍 ANALYZING @{USERNAME}...")
            
            PROFILE = GET_INSTAGRAM_DATA(USERNAME)
            
            if PROFILE:
                RISK, ISSUES = CALC_RISK(PROFILE)
                REPORT = FORMAT_REPORT(USERNAME, PROFILE, RISK, ISSUES)
                
                await status_msg.delete()
                
                AVAILABLE, REMAINING, _ = CHECK_SEARCH_AVAILABLE(USER.id)
                await MSG.reply_text(
                    REPORT + f"\n🎫 LEFT: {REMAINING if AVAILABLE else 0}",
                    reply_markup=AFTER_ANALYSIS_KEYBOARD(USERNAME)
                )
            else:
                if USER.id != ADMIN_ID:
                    CUR.execute("UPDATE USERS SET REMAINING_SEARCHES = REMAINING_SEARCHES + 1 WHERE ID=?", (USER.id,))
                    DB.commit()
                
                await status_msg.edit_text("❌ PROFILE NOT FOUND!")
            
            context.user_data['mode'] = None
            return
        
        # ADMIN COMMANDS
        if context.user_data.get('admin_mode') == 'approve' and USER.id == ADMIN_ID:
            try:
                target_id = int(MSG.text.strip())
                if APPROVE_USER(target_id):
                    await MSG.reply_text(f"✅ USER {target_id} APPROVED!", reply_markup=ADMIN_KEYBOARD())
                else:
                    await MSG.reply_text("❌ ERROR!", reply_markup=ADMIN_KEYBOARD())
            except:
                await MSG.reply_text("❌ INVALID ID!", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
        
        elif context.user_data.get('admin_mode') == 'broadcast' and USER.id == ADMIN_ID:
            text = MSG.text
            CUR.execute("SELECT ID FROM USERS")
            users = CUR.fetchall()
            
            status = await MSG.reply_text(f"📢 BROADCASTING TO {len(users)} USERS...")
            sent = 0
            
            for (uid,) in users:
                try:
                    await context.bot.send_message(uid, f"📢 **BROADCAST**\n\n{text}")
                    sent += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            
            await status.edit_text(f"✅ SENT TO {sent} USERS")
            context.user_data['admin_mode'] = None
    
    except Exception as e:
        log_error(str(e), "HANDLE_MESSAGES")

async def APPROVE_COMMAND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """APPROVE COMMAND HANDLER"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve USER_ID")
        return
    
    try:
        target_id = int(context.args[0])
        if APPROVE_USER(target_id):
            await update.message.reply_text(f"✅ USER {target_id} APPROVED!")
        else:
            await update.message.reply_text("❌ ERROR!")
    except:
        await update.message.reply_text("❌ INVALID ID!")

# ================= BOT SETUP =================

async def RUN_BOT():
    """RUN THE BOT"""
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", START))
        app.add_handler(CommandHandler("approve", APPROVE_COMMAND))
        app.add_handler(CallbackQueryHandler(BUTTON_CALLBACK))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, HANDLE_MESSAGES))
        
        print("✅ BOT STARTED!")
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        log_error(str(e), "RUN_BOT")
    finally:
        DB.close()

def start_bot():
    """START BOT IN THREAD"""
    asyncio.run(RUN_BOT())

# ================= FLASK SERVER =================

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "Instagram Analyzer Pro",
        "developer": "@proxyfxc",
        "time": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/codes')
def get_codes():
    """ADMIN ONLY - PROTECT IN PRODUCTION"""
    try:
        with open(CODES_FILE, 'r') as f:
            codes = f.read()
        return f"<pre>{codes}</pre>"
    except:
        return "No codes file found"

# ================= MAIN =================

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
