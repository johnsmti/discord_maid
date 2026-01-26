import discord
from discord.ext import commands
from discord import ui
import json
import os
import time
from datetime import datetime

# =========================================================
# ⚙️ 1. ตั้งค่า ID ยศ (ต้องแก้เลขตรงนี้ให้เป็นของจริง!)
# =========================================================
VIP_ROLE_ID = 1462100797734125825      # 👈 ใส่ ID ยศ VIP
RANK_VIP_ID = 1453046003212095669      # ยศ VIP (จากการสะสมยอด - ถ้าใช้อันเดียวกับข้างบนก็ใส่เลขเดิม)
RANK_REG_ID = 1453045889424949349
STAFF_CHANNEL_ID = 1464980257160429721 # 👈 ใส่ ID ห้อง Staff สำหรับแจ้งเตือน

# =========================================================
# ⚙️ 2. ข้อมูลเมด
# =========================================================
MAID_DATA = {
    "maid_01": {
        "id": 880704502846586911, 
        "name": "น้องไข่หวาน 🍳",
        "emoji": "<a:HGWS_92:1451914602622357647",
        "color": 0xffeebb, 
        "desc": (
            "❝ นายท่านรับข้าวห่อไข่ไหมคะ? ❞\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**<a:dount_withcreams:1452651298942877866> ความถนัด:** ร่ายมนต์ความอร่อย, ทำอาหาร\n"
            "**<a:920979210204487690:1449346155589926912> นิสัย:** ร่าเริง, ซุ่มซ่ามนิดหน่อย\n"
            "**<a:4420alarm1:1452655790488944681> เวลาเข้างาน:** 18:00 - 22:00 น.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "image": "https://media.tenor.com/tHqF_o_W3SAAAAAd/anime-maid.gif"
    },
    "maid_02": {
        "id": 612282254093451264, 
        "name": "คุณพี่มิร่า 🍷",
        "emoji": "<a:emoji_124:1452651697737302046>",
        "color": 0x800020, 
        "desc": (
            "❝ รับชาเอิร์ลเกรย์หรือดาร์จีลิงดีคะ? ❞\n"
            "━━━━━━━━━━━━━━━━━\n"
            "**<a:dount_withcreams:1452651298942877866> ความถนัด:** ชงชาชั้นเลิศ, ดูแลความเรียบร้อย\n"
            "**<a:920979210204487690:1449346155589926912> นิสัย:** เจ้าระเบียบ, ดุแต่น่ารัก\n"
            "**<a:4420alarm1:1452655790488944681> เวลาเข้างาน:** 20:00 - 00:00 น.\n"
            "━━━━━━━━━━━━━━━━━"
        ),
        "image": "https://media.tenor.com/images/3342378943f21820623631a788484180/tenor.gif"
    }
}
DB_FILE = "users_data.json"

# =========================================================
# 🛠️ 3. ฟังก์ชันระบบ
# =========================================================
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

def get_user_title(member):
    if not isinstance(member, discord.Member): return "นายท่าน"
    for role in member.roles:
        if "คุณหนู" in role.name or "Lady" in role.name: return "คุณหนู"
    return "นายท่าน"

def get_rank_discount(total_spent):
    if total_spent >= 5000:
        return "VIP", 10, 0xffd700
    elif total_spent >= 1000:
        return "Regular", 5, 0x1abc9c
    else:
        return "Guest", 0, 0x95a5a6

def get_status_info(guild, user_id):
    member = guild.get_member(user_id)
    
    # ถ้าหาตัวไม่เจอ
    if not member: 
        return "<a:9366laydowntorest:1464993190485692449> ไม่พบตัว", True, discord.ButtonStyle.secondary

    # เช็คสถานะแล้วใส่ Emoji เคลื่อนไหว
    if member.status == discord.Status.online:
        return "<a:1370everythingisstable:1464993082234634503> เข้างาน (Online)", False, discord.ButtonStyle.success
        
    elif member.status == discord.Status.idle:
        return "<:4572discordidle:1464993521110089923> พักผ่อน (Idle)", False, discord.ButtonStyle.success
        
    elif member.status == discord.Status.dnd:
        return "<a:9366laydowntorest:1464993190485692449> ยุ่ง (Do Not Disturb)", False, discord.ButtonStyle.danger
        
    else:
        return "<:4624discordoffline:1464993486771191979> ไม่เข้างาน (Offline)", True, discord.ButtonStyle.secondary

# =========================================================
# 🖥️ 4. ส่วนแสดงผล (View & Buttons)
# =========================================================

# 👇👇 Class ปุ่มรับงานสำหรับ Staff (เพิ่มกลับมาให้แล้วครับ) 👇👇
class JobAcceptView(discord.ui.View):
    def __init__(self, customer_id, customer_channel_id):
        super().__init__(timeout=None)
        self.customer_id = customer_id
        self.customer_channel_id = customer_channel_id

    @discord.ui.button(label="กดเพื่อรับงานนี้", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_job(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. อัปเดตห้อง Staff (ให้ปุ่มหายไป) เปลี่ยนเป็นชื่อคนรับงาน
        await interaction.response.edit_message(content=f"✅ **รับงานแล้วโดย:** {interaction.user.mention}", view=None)
        
        # 2. เตรียมข้อมูลลูกค้า
        guild = interaction.guild
        customer = guild.get_member(self.customer_id)
        
        # ข้อความที่จะส่ง (ใส่ Embed ให้สวยงาม)
        embed = discord.Embed(
            description=f"🏃‍♀️ **รับทราบค่ะ!**\nน้อง {interaction.user.mention} รับงานแล้ว และกำลังรีบไปหานะคะ 💨", 
            color=0x2ecc71
        )

        # 3. ระบบ Hybrid (พยายามส่ง DM ก่อน)
        sent_in_dm = False
        if customer:
            try:
                # 📨 ส่งเข้า DM ส่วนตัว (Private 100%)
                await customer.send(embed=embed)
                sent_in_dm = True
            except:
                pass # ถ้าลูกค้าปิด DM ก็ข้ามไป

        # 4. ถ้าส่ง DM ไม่ได้ -> ให้ส่งในห้องเดิมแต่ลบใน 10 วิ (กันรก)
        if not sent_in_dm:
            channel = guild.get_channel(self.customer_channel_id)
            if channel:
                # delete_after=10 คือทีเด็ด! ส่งปุ๊บ นับถอยหลัง 10 วิ ลบทิ้งทันที
                await channel.send(content=f"<@{self.customer_id}>", embed=embed, delete_after=10)

class MaidSelect(ui.Select):
    def __init__(self):
        options = []
        for key, info in MAID_DATA.items():
            # 👇 แก้ตรง emoji=... จาก "🎀" เป็น info.get("emoji", "🎀")
            # (แปลว่า: ให้ใช้อิโมจิประจำตัว ถ้าไม่มีให้ใช้โบว์เป็นค่าสำรอง)
            options.append(
                discord.SelectOption(
                    label=info["name"], 
                    value=key, 
                    emoji=info.get("emoji", "🎀") 
                )
            )
        super().__init__(placeholder="🔻 เลือกดูโปรไฟล์เมดท่านอื่น...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        view = MaidDirectoryView(default_maid_key=selected_key)
        await view.refresh_display(interaction, is_edit=True)

class MaidDirectoryView(ui.View):
    def __init__(self, default_maid_key="maid_01"):
        super().__init__(timeout=None)
        self.current_maid_key = default_maid_key
        self.add_item(MaidSelect())

    async def refresh_display(self, interaction, is_edit=False):
        maid_info = MAID_DATA[self.current_maid_key]
        status_text, is_disabled, btn_style = get_status_info(interaction.guild, maid_info["id"])
        
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "btn_call_maid":
                child.disabled = is_disabled
                child.style = btn_style
                child.label = "เรียกเมดคนนี้" if not is_disabled else "⛔ ไม่เข้างาน"

        embed = discord.Embed(
            title=f"**ข้อมูลเมด:** {maid_info['name']}",
            description=f"{maid_info['desc']}\n\n**สถานะปัจจุบัน:** {status_text}",
            color=maid_info['color']
        )
        embed.set_image(url=maid_info["image"])
        try:
            real_user = await interaction.client.fetch_user(maid_info["id"])
            if real_user.avatar: embed.set_thumbnail(url=real_user.avatar.url)
            embed.set_footer(text=f"User: {real_user.name}")
        except: pass
        
        if is_edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed, view=self)

    # --- ปุ่ม 1: เรียกเมด (15 เครดิต + XP) ---
    @ui.button(label="เรียกเมด (15 เครดิต)", style=discord.ButtonStyle.success, emoji=discord.PartialEmoji.from_str("<a:4381anouncementsanimated:1452658197625180322>"), row=1, custom_id="btn_call_maid")
    async def call_paid(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        data = load_db()
        
        if user_id not in data: 
            data[user_id] = {"points": 0, "total_spent": 0}

        base_price = 15      
        
        current_spent = data[user_id].get("total_spent", 0)
        rank_name, discount_percent, _ = get_rank_discount(current_spent)

        final_price = base_price
        if discount_percent > 0:
            discount_amount = int(base_price * (discount_percent / 100))
            final_price = base_price - discount_amount

        user_credits = data[user_id].get("points", 0)
        
        if user_credits < final_price:
            await interaction.response.send_message(
                f"⛔ **เครดิตไม่พอค่ะ!**\nต้องการ: {final_price} เครดิต (มีอยู่: {user_credits})\n💳 กรุณาติดต่อแอดมินเพื่อเติมเงินนะคะ", 
                ephemeral=True
            )
            return

        data[user_id]["points"] -= final_price
        data[user_id]["total_spent"] = current_spent + final_price 
        save_db(data)
        
        # ... (โค้ดก่อนหน้านี้เหมือนเดิม) ...

        # 5. เช็คการเลื่อนยศ (หลังจากสะสมยอดเพิ่มแล้ว)
        new_spent = data[user_id]["total_spent"]
        new_rank, _, _ = get_rank_discount(new_spent)
        
        # 6. ส่งข้อความตอบกลับ
        target_maid = MAID_DATA[self.current_maid_key]
        
        msg = f"<a:4968_verif_green:1452650972340818040> **ชำระเงินสำเร็จ!** (หัก {final_price} เครดิต)\n"
        if rank_name != "Guest":
            msg += f"<a:Little_Pretty_Star_Yellow:1451907037012164720> **(สิทธิพิเศษ {rank_name}: ลดราคา {discount_percent}%)**\n"
            
        msg += f"<a:849305166716993647:1449360337005449367> เครดิตคงเหลือ: **{data[user_id]['points']}**\n"
        msg += f"📈 ยอดสะสม (XP): **{new_spent}** (ระดับ: {new_rank})\n"
        msg += f"กำลังตามน้อง **{target_maid['name']}** มาค่ะ! 💨"
        
        # 🔥🔥🔥 ส่วนที่เพิ่ม: แจกยศจริงๆ ใน Discord 🔥🔥🔥
        if rank_name != new_rank:
            msg += f"\n\n🎉 **CONGRATULATIONS!** 🎉\nนายท่านเลื่อนขั้นเป็นระดับ **{new_rank}** แล้วค่ะ!"
            
            # เตรียมยศ
            guild = interaction.guild
            reg_role = guild.get_role(RANK_REG_ID)
            vip_role = guild.get_role(RANK_VIP_ID)
            
            try:
                if new_rank == "Regular":
                    if reg_role: await interaction.user.add_roles(reg_role)
                elif new_rank == "VIP":
                    if vip_role: await interaction.user.add_roles(vip_role)
                    # (Optional) ถ้าขึ้น VIP แล้วอยากให้ถอด Regular ออก ให้เปิดบรรทัดล่าง
                    # if reg_role: await interaction.user.remove_roles(reg_role)
            except Exception as e:
                print(f"แจกยศไม่สำเร็จ: {e}")

        await interaction.response.send_message(msg, ephemeral=True)
        await self.notify_staff(interaction, mode="PAID_CREDIT")

    # --- ปุ่ม 2: เรียก VIP ---
    @ui.button(label="VIP Only", style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji.from_str("<a:74780diamond:1465002711056384186>"), row=1, custom_id="btn_vip")
    async def call_vip(self, interaction: discord.Interaction, button: ui.Button):
        has_vip = any(role.id == VIP_ROLE_ID for role in interaction.user.roles)

        if has_vip:
            target_maid = MAID_DATA[self.current_maid_key]
            msg = (f"✨ **Welcome VIP Member!** ✨\n"
                   f"ขอบพระคุณที่สนับสนุนเรานะคะ💖\n"
                   f"กำลังตามน้อง **{target_maid['name']}** มาดูแลทันทีค่ะ!")
            await interaction.response.send_message(msg, ephemeral=True)
            await self.notify_staff(interaction, mode="PAID_REAL_MONEY")
        else:
            embed = discord.Embed(
                title="⛔ เฉพาะสมาชิก VIP เท่านั้น!",
                description="**<a:74780diamond:1465002711056384186> สมัคร VIP เพียง 50 บาท/เดือน**\nได้รับสิทธิ์เรียกเมดได้ไม่อั้น และห้องส่วนตัว!",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- ปุ่ม 3: ดูบัตรสมาชิก ---
    # (ใน class MaidDirectoryView)

    @ui.button(label="ดูบัตรสมาชิก", style=discord.ButtonStyle.secondary, emoji="💳", row=2)
    async def check_card(self, interaction: discord.Interaction, button: ui.Button):
        data = load_db()
        user_id = str(interaction.user.id)
        user_data = data.get(user_id, {}) 

        # 1. ดึงข้อมูล
        my_name = user_data.get("name", "ไม่ระบุ")
        my_age = user_data.get("age", "-")
        my_gender = user_data.get("gender", "ไม่ระบุ")
        my_status = user_data.get("status", "ว่างเสมอเพื่อเธอคนเดียว").strip() # .strip() เพื่อตัดช่องว่างหัวท้าย
        
        # 2. คำเรียก
        title_call = "นายท่าน"
        if "หญิง" in my_gender or "Female" in my_gender:
            title_call = "คุณหนู"

        # 3. ข้อมูลการเงิน
        points = user_data.get("points", 0)
        total_spent = user_data.get("total_spent", 0)
        rank_name, discount, rank_color = get_rank_discount(total_spent)
        
        # 4. สร้าง Embed
        embed = discord.Embed(
            title=f"💳 Maid Passport: {title_call} {interaction.user.display_name}", 
            description=f"ข้อมูลสมาชิกอย่างเป็นทางการ",
            color=rank_color
        )
        
        if "avatar_url" in user_data and user_data["avatar_url"]:
            embed.set_thumbnail(url=user_data["avatar_url"])
        else:
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

        # --- ส่วนข้อมูลส่วนตัว ---
        embed.add_field(name="<:1685member:1451949628412006490> ชื่อในวงการ", value=my_name, inline=True)
        embed.add_field(name="<:22236cutesystar:1451888594750013521> อายุ", value=f"{my_age} ปี", inline=True)
        embed.add_field(name="🚻 เพศ", value=my_gender, inline=True)
        
        embed.add_field(name="<a:9754_Loading:1449346048416809100> สเตตัส", value=f"❝ {my_status} ❞", inline=False) # จัดจัดคำพูดให้สวย
        
        # --- เส้นคั่นแบบทึบ (ดูแพงกว่า) ---
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**STATISTICS**", inline=False)
        
        # --- ส่วนข้อมูลเกม (ใส่ลูกน้ำ , ให้ตัวเลข) ---
        embed.add_field(name="<a:68230questionexclaimanimated:1465006064276607283> ระดับชั้น", value=f"**{rank_name}**\n(ลด {discount}%)", inline=True)
        embed.add_field(name="<a:853235082922819604:1449360343947153538> เครดิต", value=f"**{points:,}**", inline=True)     # 👈 ใส่ , ตรงนี้
        embed.add_field(name="📈 ยอดเปย์", value=f"**{total_spent:,}**", inline=True) # 👈 ใส่ , ตรงนี้
        
        embed.set_footer(text=f"Card Holder: {interaction.user.name} • Maid Cafe System")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- ปุ่ม 4: รีเฟรช ---
    @ui.button(label="รีเฟรช", style=discord.ButtonStyle.secondary, emoji=discord.PartialEmoji.from_str("<a:4428ghosticonload:1465007188106936487>"), row=2)
    async def refresh(self, interaction, button):
        await self.refresh_display(interaction, is_edit=True)

    # ฟังก์ชันแจ้ง Staff (แก้ไขให้ส่งปุ่ม JobAcceptView ไปด้วย)
    # (ใน Class MaidDirectoryView)

    # (ใน Class MaidDirectoryView)

    # (ใน Class MaidDirectoryView)

    async def notify_staff(self, interaction, mode):
        staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)
        if not staff_channel: return

        # 1. โหลดข้อมูลพื้นฐาน
        data = load_db()
        user_id = str(interaction.user.id)
        total_spent = data.get(user_id, {}).get("total_spent", 0)
        
        # --- 🚨 ส่วนที่แก้: เช็ค Role ใน Discord เป็นอันดับแรก 🚨 ---
        
        # กำหนด ID ของ Role ต่างๆ (ตรวจสอบให้ตรงกับเซิร์ฟเวอร์จริง)
        # ⚠️ สำคัญ: ต้องเอา ID ของยศ "VIP-ระดับสูง", "Guest-ฝึกหัด" ฯลฯ มาใส่ตรงนี้
        ROLE_VIP_HIGH = 1453046003212095669    # ใส่ ID ยศ VIP-ระดับสูง
        ROLE_REGULAR = 1453045889424949349     # ใส่ ID ยศ Regular
        
        # ดึง Role ทั้งหมดของ User
        user_roles_ids = [role.id for role in interaction.user.roles]
        
        # ตรรกะการเลือกยศที่จะโชว์ (เรียงจากสูงไปต่ำ)
        if ROLE_VIP_HIGH in user_roles_ids:
            rank_display = "VIP (ระดับสูง)"
            rank_color = 0xFFD700 # สีทอง
        elif ROLE_REGULAR in user_roles_ids:
            rank_display = "Regular (ขาประจำ)"
            rank_color = 0x1ABC9C # สีเขียว
        else:
            # ถ้าไม่มียศพิเศษ ให้ใช้ระบบคำนวณจากยอดเงิน (XP) เป็นตัวสำรอง
            calculated_rank, _, _ = get_rank_discount(total_spent)
            rank_display = calculated_rank
            if rank_display == "Guest": 
                rank_display = "Guest (ฝึกหัด)"
            
        # -----------------------------------------------------------

        # 2. เตรียมข้อความแจ้งเตือน
        target_maid = MAID_DATA[self.current_maid_key]
        if mode == "PAID_REAL_MONEY":
            header_text = "<a:922779969082519603:1451954184659275989> VIP เรียกเมด!"
            desc_text = "✨ สมาชิกรายเดือน (Unlimited Access)"
            embed_color = 0xFFD700
        else:
            header_text = "💰 ลูกค้าใช้เครดิตเรียกเมด"
            desc_text = "💸 ชำระเงินด้วยเครดิตเรียบร้อย"
            embed_color = 0x2ecc71

        embed = discord.Embed(title=header_text, description=f"เมด: **{target_maid['name']}**\n{desc_text}", color=embed_color)
        
        # 3. ใส่ข้อมูลลงใน Embed
        embed.add_field(name="<:1685member:1451949628412006490> ลูกค้า", value=interaction.user.mention, inline=True)
        embed.add_field(name="<a:68230questionexclaimanimated:1465006064276607283> ระดับ", value=f"**{rank_display}**", inline=True) # ✅ โชว์ยศที่เช็คจาก Discord
        embed.add_field(name="📍 ห้อง", value=interaction.channel.mention, inline=True)
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        # 4. ส่ง
        accept_view = JobAcceptView(interaction.user.id, interaction.channel.id)
        await staff_channel.send(content=f"<@{target_maid['id']}>", embed=embed, view=accept_view)
# =========================================================
# 5. Main Cog Setup
# =========================================================
class MaidSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def maids(self, ctx):
        # 1. เลือกเมดคนแรกมาโชว์
        first_key = list(MAID_DATA.keys())[0]
        maid_info = MAID_DATA[first_key]
        
        # 2. เตรียมปุ่ม
        view = MaidDirectoryView(default_maid_key=first_key)
        
        # 3. เช็คสถานะ
        status_text, is_disabled, btn_style = get_status_info(ctx.guild, maid_info["id"])
        
        for child in view.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "btn_call_maid":
                child.disabled = is_disabled
                child.style = btn_style
                child.label = "เรียกเมดคนนี้" if not is_disabled else "⛔ ไม่เข้างาน"

        # 4. สร้าง Embed
        embed = discord.Embed(
            title=f"**ข้อมูลเมด:** {maid_info['name']}",
            description=f"{maid_info['desc']}\n\n**สถานะปัจจุบัน:** {status_text}",
            color=maid_info['color']
        )
        embed.set_image(url=maid_info["image"])
        
        try:
            real_user = await self.bot.fetch_user(maid_info["id"])
            if real_user.avatar: embed.set_thumbnail(url=real_user.avatar.url)
            embed.set_footer(text=f"User: {real_user.name}")
        except: pass
        
        # 5. ส่ง
        await ctx.send(embed=embed, view=view)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def topup(self, ctx, member: discord.Member, amount: int):
        # ... (โค้ด topup เดิมของคุณ) ...
        pass

    @commands.command()
    async def promotion(self, ctx):
        # ... (โค้ด promotion เดิมของคุณ) ...
        pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_welcome(self, ctx):
        # ... (โค้ด setup_welcome เดิมของคุณ) ...
        view = WelcomeButtonView()
        await ctx.send(embed=embed, view=view)

    # ------------------------------------------------------------------
    # 👇 จุดที่แก้ไข: ย้าย setup_queue และ next เข้ามา "ใน Class" (ย่อหน้าเท่ากับ def อื่นๆ)
    # ------------------------------------------------------------------

    # --- คำสั่งสร้างป้ายกดบัตรคิว ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_queue(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="🏨 จุดรับบัตรคิว (Queue Station)",
            description=(
    "❝ ยินดีต้อนรับกลับบ้านค่ะ นายท่าน! ❞\n"  # คำโปรย ใส่เครื่องหมายคำพูดเท่ๆ
    "━━━━━━━━━━━━━━━━━━━━━━\n"         # เส้นคั่น (พระเอกของเรา)
    "บริการของเรามีดังนี้ค่ะ:\n\n"
    "☕ **Maid Service**\n"
    "└ เรียกน้องเมดมาพูดคุยดูแลใจ\n\n"         # ใช้สัญลักษณ์ Tree structure
    "🎟️ **Queue System**\n"
    "└ จองคิวล่วงหน้าเมื่อร้านเต็ม\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "*กดปุ่มด้านล่างเพื่อเลือกบริการได้เลยนะคะ* 👇"
),
            color=0x3498db
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        # เรียกใช้ QueueView ที่อยู่ด้านล่างไฟล์
        await ctx.send(embed=embed, view=QueueView())
        
    # ------------------------------------------------------------------
    # 👇 พื้นที่สำหรับคำสั่งบอท (ต้องย่อหน้าเข้าไปใน Class MaidSystem)
    # ------------------------------------------------------------------

    # --- คำสั่งเรียกคิวต่อไป (Staff ใช้) ---
    @commands.command()
    async def next(self, ctx):
        # โหลดข้อมูล
        data = load_db()
        if "queue_system" not in data or not data["queue_system"]["waiting_list"]:
            await ctx.send("✅ **ตอนนี้ไม่มีคิวค้างค่ะ!** ว่างยาวๆ เลย~")
            return
            
        queue_sys = data["queue_system"]
        waiting_list = queue_sys["waiting_list"]
        
        # ดึงคนแรกออก
        next_customer = waiting_list.pop(0) 
        save_db(data) 

        # แจ้งเตือน
        user_id = int(next_customer['id'])
        queue_no = next_customer['number']
        
        embed = discord.Embed(
            title=f"🔔 ขอเชิญหมายเลข: {queue_no}",
            description=f"คุณ <@{user_id}> ถึงคิวแล้วค่ะ!\nเชิญที่ห้องรับรองได้เลยค่า 💕",
            color=0xE91E63
        )
        await ctx.send(content=f"<@{user_id}>", embed=embed)

    # --- คำสั่งเรียกแผงควบคุมคิว (Staff ใช้) ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def queue_panel(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="🎮 แผงควบคุมคิว (Staff Only)",
            description="กดปุ่มด้านล่างเพื่อเรียกคิวถัดไป\n(ข้อความจะเด้งไปที่ห้อง Lobby)",
            color=0x2ecc71
        )
        await ctx.send(embed=embed, view=QueueStaffView())

# =========================================================
# 📦 CLASS VIEW ต่างๆ (วางไว้ "นอก Class MaidSystem" ชิดซ้ายสุด)
# =========================================================

class WelcomeButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="กดรับ 30 เครดิต ฟรี!", style=discord.ButtonStyle.success, emoji="🧧", custom_id="welcome_bonus_30")
    async def claim_bonus(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ... (โค้ด claim_bonus เดิมของคุณ) ...
        # ขออนุญาตย่อไว้เพื่อความสั้น (ใช้โค้ดเดิมข้างในได้เลยครับ)
        user_id = str(interaction.user.id)
        data = load_db()
        user_data = data.get(user_id, {})
        
        if user_data.get("welcome_claimed", False):
            await interaction.response.send_message("❌ รับไปแล้วค่ะ", ephemeral=True)
            return

        user_data["credit"] = user_data.get("credit", 0) + 30
        user_data["welcome_claimed"] = True
        data[user_id] = user_data
        save_db(data)
        await interaction.response.send_message("✅ รับ 30 เครดิตเรียบร้อย!", ephemeral=True)

class QueueView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="รับบัตรคิว (Get Queue)", style=discord.ButtonStyle.primary, emoji="🎟️", custom_id="get_queue_btn")
    async def get_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        data = load_db()
        
        if "queue_system" not in data:
            data["queue_system"] = { "current_run_number": 0, "waiting_list": [] }
        
        queue_sys = data["queue_system"]
        waiting_list = queue_sys["waiting_list"]

        # 1. เช็คซ้ำ
        for q in waiting_list:
            if q['id'] == user_id:
                await interaction.response.send_message(f"⚠️ คุณมีคิวอยู่แล้วค่ะ: **{q['number']}**", ephemeral=True)
                return

        # 2. รันเลข
        queue_sys["current_run_number"] += 1
        run_num = queue_sys["current_run_number"]
        queue_number = f"A-{run_num:03d}"
        
        # 3. บันทึก
        waiting_list.append({
            "id": user_id,
            "number": queue_number,
            "name": interaction.user.display_name
        })
        save_db(data)

        # 4. แจ้งผล
        queue_left = len(waiting_list) - 1
        msg = f"✅ **ออกบัตรคิวสำเร็จ!**\n🎫 หมายเลขของคุณ: **{queue_number}**\n⏳ มีคิวรอหน้าคุณ: {queue_left} คิว"
        await interaction.response.send_message(msg, ephemeral=True)

class QueueStaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="เรียกคิวถัดไป (Call Next)", style=discord.ButtonStyle.success, emoji=discord.PartialEmoji.from_str("<a:4381anouncementsanimated:1452658197625180322>"), custom_id="staff_call_next")
    async def call_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        # โหลดข้อมูล
        data = load_db()
        if "queue_system" not in data or not data["queue_system"]["waiting_list"]:
            await interaction.response.send_message("✅ **ตอนนี้ไม่มีคิวค้างค่ะ!** ว่างยาวๆ เลย~", ephemeral=True)
            return
            
        queue_sys = data["queue_system"]
        waiting_list = queue_sys["waiting_list"]
        
        # ดึงคนแรกออก
        next_customer = waiting_list.pop(0) 
        save_db(data) 
# (ใน class QueueStaffView ฟังก์ชัน call_next)

        # ... (โค้ดส่วนดึงข้อมูล ดึงคนแรกออก เหมือนเดิม) ...
        # next_customer = waiting_list.pop(0) 
        # save_db(data) 

        # ---------------------------------------------------------
        # 👇 แก้ไขส่วนการประกาศ (Announcement) ให้ระบุชื่อคนเรียก 👇
        # ---------------------------------------------------------
        
        # ดึงชื่อเมดที่กดปุ่ม (คนกดคือ interaction.user)
        maid_name = interaction.user.display_name 

        # แจ้งเตือนเมด (คนกด)
        await interaction.response.send_message(f"✅ คุณรับลูกค้า **{next_customer['number']}** แล้วค่ะ", ephemeral=True)

        # ประกาศเรียกในห้องลูกค้า
        LOBBY_CHANNEL_ID = 1463522099309314205 # เช็ค ID ห้องให้ถูกนะ
        lobby_channel = interaction.guild.get_channel(LOBBY_CHANNEL_ID)
        
        if lobby_channel:
            user_id = int(next_customer['id'])
            
            embed = discord.Embed(
                title=f"🔔 เชิญหมายเลข: {next_customer['number']}",
                description=(
                    f"คุณ <@{user_id}> ถึงคิวแล้วค่าา!\n"
                    f"👉 กรุณามาที่โต๊ะ/ห้องเสียง เพื่อพบกับ: **{maid_name}** 💕\n" 
                    f"(Please proceed to see **{maid_name}**)"
                ),
                color=0xE91E63
            )
            # ใส่รูปเมดคนเรียกโชว์หราเลย (ถ้ามี)
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)
            
            await lobby_channel.send(content=f"<@{user_id}>", embed=embed)

    @discord.ui.button(label="ดูรายการคิว (List)", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="staff_view_list")
    async def view_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_db()
        waiting_list = data.get("queue_system", {}).get("waiting_list", [])
        
        if not waiting_list:
            await interaction.response.send_message("📭 ตอนนี้ไม่มีคิวรอเลยค่ะ", ephemeral=True)
            return
            
        text = "**📋 รายการคิวที่รออยู่:**\n"
        for q in waiting_list:
            text += f"`{q['number']}` - <@{q['id']}>\n"
            
        await interaction.response.send_message(text, ephemeral=True)
 
# 🏁 SETUP FUNCTION (บรรทัดท้ายสุดของไฟล์)
# =========================================================
async def setup(bot):
    await bot.add_cog(MaidSystem(bot))