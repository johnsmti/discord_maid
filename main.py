import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

from myserver import server_on

# --- ตั้งค่า (ใส่ Token ของคุณ) ---


# --- ระบบจัดการไฟล์ข้อมูล (ยังต้องมีไว้สำหรับปุ่มลงทะเบียน) ---
DATA_FILE = "users_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Modal ลงทะเบียน (เก็บไว้ให้คนใหม่กดสมัคร) ---
class RegistrationModal(ui.Modal):
    def __init__(self, dynamic_title):
        super().__init__(title=dynamic_title)
     
    name = ui.TextInput(
        label="🍮ชื่อเล่น",
        placeholder="ชื่อที่อยากให้เมดเรียก",
        style=discord.TextStyle.short,
        required=True
    )
    
    age = ui.TextInput(
        label="🌸อายุ", 
        placeholder="ตัวเลขเท่านั้น", 
        style=discord.TextStyle.short, 
        max_length=2,
        required=True
    )
    
    gender = ui.TextInput(
        label="🎀เพศ", 
        placeholder="ชาย / หญิง / อื่นๆ", 
        style=discord.TextStyle.short,
        required=True
    )
    
    status = ui.TextInput(
        label="สเตตัส💭", 
        placeholder="สถานะตอนนี้", 
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if not self.age.value.isdigit():
             await interaction.response.send_message("❌ **ผิดพลาด:** กรุณากรอกอายุเป็น **ตัวเลข** เท่านั้นค่ะ!", ephemeral=True)
             return
        
        user = interaction.user
        data = load_data()
        
        old_points = 0
        old_oshi = None
        old_checkin = ""
        
        if str(user.id) in data:
            user_info = data[str(user.id)]
            old_points = user_info.get("points", 0)
            old_oshi = user_info.get("oshi_id", None)
            old_checkin = user_info.get("last_checkin", "")

        data[str(user.id)] = {
            "name": self.name.value,
            "age": self.age.value,
            "gender": self.gender.value,
            "status": self.status.value,
            "avatar_url": user.avatar.url if user.avatar else "",
            "points": old_points,
            "oshi_id": old_oshi,
            "last_checkin": old_checkin
        }
        save_data(data)
        
        try:
            role_id = 1446776080873685043 
            role = interaction.guild.get_role(role_id)
            if role:
                await user.add_roles(role)
                print(f"✅ แจกยศ {role.name} ให้ {user.name} เรียบร้อย")
            else:
                print(f"❌ หา Role ID: {role_id} ไม่เจอ!")
        except Exception as e:
            print(f"❌ แจกยศไม่ได้: {e}")

        # เปลี่ยนข้อความบอกให้ไปใช้เมนูใหม่
        await interaction.response.send_message("✅ **ลงทะเบียนเรียบร้อยค่ะ!**\nเชิญเรียกน้องเมด หรือดูบัตรสมาชิกได้ที่คำสั่ง `!maids` หรือเมนูหลักได้เลยนะคะ 💕", ephemeral=True)

# --- The Main Menu View (เหลือแค่ปุ่มลงทะเบียน) ---
class CafeMenu(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ปุ่มเช็คอิน -> ลบแล้ว
    # ปุ่มดูบัตร -> ลบแล้ว

    @ui.button(label="ลงทะเบียน", style=discord.ButtonStyle.secondary, emoji="<a:a6c11ff717404110ab1f8359f7a3e119:1449346222233092117>", custom_id="btn_register")
    async def register_button(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        data = load_data()
        
        if user_id in data:
            await interaction.response.send_message("🚫 ท่านลงทะเบียนไปแล้วคะ! (สามารถใช้ระบบเมดได้เลย)", ephemeral=True)
            return 
        
        user_roles = [role.name for role in interaction.user.roles]
        
        if "คุณหนู" in user_roles:
            modal_title = "ลงทะเบียนคุณหนู 🎀"
        elif "นายท่าน" in user_roles:
            modal_title = "ลงทะเบียนนายท่าน 🎩"
        else:
            modal_title = "ลงทะเบียนนายท่าน/คุณหนู"

        await interaction.response.send_modal(RegistrationModal(dynamic_title=modal_title))

# --- 2. ตั้งค่าบอทและโหลด Cogs ---
class MyMaidBot(commands.Bot):
    async def setup_hook(self):
        # โหลดระบบแยกไฟล์
        await self.load_extension("cogs.maid_system")
        # await self.load_extension("cogs.time_system") # (ถ้ามีก็เปิดใช้)
        
        await self.tree.sync()
        
        # โหลดปุ่มเมนูหลัก (ที่มีแค่ปุ่มลงทะเบียน)
        self.add_view(CafeMenu()) 
        print("✅ โหลดระบบแยกไฟล์ (Cogs) เรียบร้อยแล้ว!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = MyMaidBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Maid Bot Online: {bot.user}')

@bot.command()
async def menu(ctx):
    exact_path = r"C:\xampp\htdocs\Maid\banner.jpg"
    
    if os.path.exists(exact_path):
        file = discord.File(exact_path, filename="banner.jpg")
        embed = discord.Embed(
            title="☕ Maid Cafe Service Counter",
            description="ยินดีต้อนรับสู่งานบริการอัตโนมัติค่ะ\n**กรุณากดลงทะเบียน** เพื่อเริ่มต้นใช้งานระบบเมดคาเฟ่นะคะ 💕",
            color=0xff69b4
        )
        embed.set_image(url="attachment://banner.jpg")
        
        # ส่งเมนูที่มีแค่ปุ่มลงทะเบียน
        await ctx.send(file=file, embed=embed, view=CafeMenu())
        print(f"✅ เจอไฟล์รูปที่: {exact_path}")
    else:
        await ctx.send(f"❌ บอทหาไฟล์ไม่เจอครับ!\nบอทมองหาที่: `{exact_path}`")
        print(f"❌ ไม่เจอไฟล์ที่: {exact_path}") 

server_on()

bot.run(os.getenv('TOKEN'))