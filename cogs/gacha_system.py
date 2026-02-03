import discord
from discord.ext import commands
from discord import ui
import json
import os
import random
import asyncio

# =========================================================
# ⚙️ ตั้งค่าฐานข้อมูล
# =========================================================
DB_FILE = "users_data.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

# =========================================================
# 🧩 ของรางวัล & ชิ้นส่วนจิ๊กซอว์
# =========================================================
GACHA_POOL = [
    # --- เกลือ (Salt) 60% ---
    {"id": "item_salt", "name": "เกลือแกง (ไม่มีค่า)", "rarity": "N", "rate": 69, "type": "junk", "img": "https://cdn-icons-png.flaticon.com/512/2600/2600234.png"},
    
    # --- ชิ้นส่วนหัวใจ (Puzzle Pieces) 36% (ชิ้นละ 9%) ---
    {"id": "puzzle_1", "name": "🧩 จิ๊กซอว์: หัวใจบนซ้าย", "rarity": "R", "rate": 15, "type": "shard", "img": "https://cdn-icons-png.flaticon.com/512/7650/7650965.png"},
    {"id": "puzzle_2", "name": "🧩 จิ๊กซอว์: หัวใจบนขวา", "rarity": "R", "rate": 8, "type": "shard", "img": "https://cdn-icons-png.flaticon.com/512/7650/7650965.png"},
    {"id": "puzzle_3", "name": "🧩 จิ๊กซอว์: หัวใจล่างซ้าย", "rarity": "R", "rate": 5, "type": "shard", "img": "https://cdn-icons-png.flaticon.com/512/7650/7650965.png"},
    {"id": "puzzle_4", "name": "🧩 จิ๊กซอว์: หัวใจล่างขวา", "rarity": "R", "rate": 2, "type": "shard", "img": "https://cdn-icons-png.flaticon.com/512/7650/7650965.png"},

    # --- แจ็คพอต (Instant Win) 4% ---
    {"id": "ticket_free", "name": "🎟️ ตั๋วเรียกเมดฟรี", "rarity": "SSR", "rate": 1, "type": "item", "img": "https://cdn-icons-png.flaticon.com/512/10328/10328082.png"}
]

# =========================================================
# 🎰 ระบบกาชา
# =========================================================
class GachaMachineView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_rarity_color(self, rarity):
        if rarity == "N": return 0x95a5a6
        if rarity == "R": return 0x3498db
        if rarity == "SSR": return 0xe91e63
        return 0xffffff

    @discord.ui.button(label="หมุนกาชา (100 เครดิต)", style=discord.ButtonStyle.danger, emoji="🎰", custom_id="btn_gacha_roll_v2")
    async def roll_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        data = load_db()
        cost = 100
        
        # 1. เช็คเงิน
        current_points = data.get(user_id, {}).get("points", 0)
        if current_points < cost:
            await interaction.response.send_message(f"💸 **เงินไม่พอค่ะ!** ขาดอีก {cost - current_points} เครดิต", ephemeral=True)
            return

        # 2. หักเงิน
        data[user_id]["points"] -= cost
        save_db(data)

        # 3. อนิเมชั่น
        await interaction.response.send_message("🎲 **กำลังหมุนหาจิ๊กซอว์...** 🧩\n*(ขอให้ได้ชิ้นที่ขาดนะ!)*", ephemeral=True)
        await asyncio.sleep(2)

        # 4. สุ่มของ
        items = GACHA_POOL
        weights = [item["rate"] for item in items]
        result = random.choices(items, weights=weights, k=1)[0]

        if result.get("type") == "shard":
            # ดึงข้อมูลว่า user มีจิ๊กซอว์กี่ชิ้นแล้ว
            user_inventory = data.get(user_id, {}).get("inventory", [])
            # เช็คเฉพาะจิ๊กซอว์ (ที่ชื่อ id ขึ้นต้นด้วย puzzle_)
            owned_puzzles = list(set([x for x in user_inventory if x.startswith("puzzle_")]))
            
            # เงื่อนไข: ถ้ามีครบ 3 ชิ้นแล้ว และกำลังจะได้ชิ้นใหม่ (ชิ้นที่ 4)
            if len(owned_puzzles) == 3 and result["id"] not in owned_puzzles:
                
                # 🔥 สุ่มโอกาส "เกลือซ้ำ" 80% (ปรับเลขตรงนี้ได้)
                if random.random() < 0.80:
                    # บังคับเปลี่ยนผลลัพธ์ -> ให้กลายเป็น "ชิ้นที่เขามีอยู่แล้ว" (Duplicate)
                    if owned_puzzles: # (กันเหนียว เผื่อลิสต์ว่าง)
                        result_id = random.choice(owned_puzzles) 
                        # หา item object จาก ID
                        result = next(item for item in GACHA_POOL if item["id"] == result_id)
                        
                        print(f"😈 แกล้ง user {interaction.user.name} สำเร็จ! เปลี่ยนชิ้นใหม่เป็นของซ้ำ")

        # 5. เก็บของ (ถ้าเป็นเกลือ ไม่ต้องเก็บก็ได้ แต่นี่เก็บไว้ดูเล่น)
        if "inventory" not in data[user_id]: data[user_id]["inventory"] = []
        data[user_id]["inventory"].append(result["id"])
        save_db(data)

        # 6. แจ้งผล
        color = self.get_rarity_color(result["rarity"])
        embed = discord.Embed(
            title=f"✨ ผลกาชา: [{result['rarity']}]",
            description=f"🎉 ยินดีด้วย! ได้รับ:\n**{result['name']}**",
            color=color
        )
        embed.set_thumbnail(url=result["img"])
        embed.set_footer(text=f"เครดิตคงเหลือ: {data[user_id]['points']}")

        await interaction.edit_original_response(content=None, embed=embed)
    
    @discord.ui.button(label="เช็คจิ๊กซอว์ที่ขาด", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="btn_gacha_check")
    async def check_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        data = load_db()
        inventory = data.get(user_id, {}).get("inventory", [])

        # 1. เช็คจิ๊กซอว์ทั้ง 4 ชิ้น
        puzzles = ["puzzle_1", "puzzle_2", "puzzle_3", "puzzle_4"]
        found_count = 0
        progress_bar = ""
        
        desc = ""
        for p_id in puzzles:
            # หาชื่อไอเทมจาก ID
            item_name = next((x["name"] for x in GACHA_POOL if x["id"] == p_id), "Unknown")
            
            if p_id in inventory:
                found_count += 1
                progress_bar += "🟩" # สีเขียว = มีแล้ว
                desc += f"✅ **มีแล้ว:** {item_name}\n"
            else:
                progress_bar += "⬛" # สีดำ = ยังไม่มี
                desc += f"❌ **ยังขาด:** {item_name}\n"

        # 2. สร้าง Embed โชว์ (เห็นคนเดียว)
        embed = discord.Embed(
            title=f"🎒 กระเป๋าของ {interaction.user.name}",
            description=f"**ความคืบหน้า:** `{progress_bar}` ({found_count}/4)\n\n{desc}",
            color=0x00ff00 if found_count == 4 else 0xffcc00
        )
        
        if found_count == 4:
            embed.set_footer(text="✨ ครบแล้ว! พิมพ์ !craft เพื่อรับรางวัลได้เลย!")
        else:
            embed.set_footer(text=f"ขาดอีก {4 - found_count} ชิ้น! สู้ต่อไป!")

        # ส่งแบบ Ephemeral (เห็นแค่คนกด)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================================================
# 🛠️ ระบบคราฟต์ของ (Crafting System)
# =========================================================
class GachaSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_gacha(self, ctx):
        """ตั้งตู้กาชา (เวอร์ชันอัปเกรด UI)"""
        await ctx.message.delete()
        
        # สร้าง Embed
        embed = discord.Embed(
            title="✨ MAID CAFE GACHA PON ✨",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🧩 **ภารกิจ: ตามหาหัวใจเมดให้ครบ 4 ส่วน!**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💎 **รางวัลใหญ่:** ยศ **True Love VIP** 👑\n"
                "*(สิทธิพิเศษเข้าห้องลับ + ชื่อสีชมพูสุดเท่)*\n\n"
                "📜 **กติกาการเล่น:**\n"
                "1️⃣ กดปุ่มสีแดงเพื่อหมุน (100 เครดิต)\n"
                "2️⃣ สะสมจิ๊กซอว์ให้ครบ 4 มุม (🧩x4)\n"
                "3️⃣ พิมพ์ `!craft` เพื่อแลกรางวัลทันที!"
            ),
            color=0xFF69B4 # สีชมพู Hot Pink
        )

        # 🖼️ 1. รูปเล็กขวาบน (Thumbnail) -> สื่อถึงการสุ่ม/จิ๊กซอว์
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4522/4522434.png") 

        # 🖼️ 2. รูปใหญ่ด้านล่าง (Banner) -> เลือกเอา 1 อันด้านล่างนี้ไปใส่ครับ 👇
        
        # [Option A] รูปหัวใจครบส่วน (ตามที่คุณต้องการ)
        # embed.set_image(url="https://i.pinimg.com/736x/88/24/7a/88247a83d7224208bd4bc45722a36214.jpg")
        
        # [Option B] รูปตู้กาชาขยับได้ (ดูน่าตื่นเต้น) *ผมแนะนำอันนี้*
        embed.set_image(url="https://media1.tenor.com/m/72w9tT2C4sQAAAAC/genshin-impact-wish.gif")

        # Footer เท่ๆ
        embed.set_footer(text="📢 คำเตือน: ระวังเกลือ! โปรดใช้วิจารณญาณในการหมุน", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await ctx.send(embed=embed, view=GachaMachineView())

    @commands.command()
    async def collection(self, ctx):
        """เช็คกระเป๋าว่ามีจิ๊กซอว์ครบยัง"""
        user_id = str(ctx.author.id)
        data = load_db()
        inventory = data.get(user_id, {}).get("inventory", [])

        if not inventory:
            await ctx.send("🎒 **กระเป๋าโล่งโจ้ง...** ไปหมุนกาชาก่อนสิคะ!", ephemeral=True)
            return

        from collections import Counter
        counts = Counter(inventory)
        
        desc = ""
        # เช็คจิ๊กซอว์ 4 ชิ้น
        puzzles = ["puzzle_1", "puzzle_2", "puzzle_3", "puzzle_4"]
        found_count = 0
        
        for p_id in puzzles:
            count = counts.get(p_id, 0)
            status = "✅ มีแล้ว" if count > 0 else "❌ ยังขาด"
            name = next(item["name"] for item in GACHA_POOL if item["id"] == p_id)
            desc += f"{name} : {status} (x{count})\n"
            if count > 0: found_count += 1
            
        embed = discord.Embed(title="🧩 สมุดสะสมจิ๊กซอว์", description=desc, color=0x00ff00)
        
        if found_count == 4:
            embed.add_field(name="✨ ยินดีด้วย!", value="คุณมีครบทุกชิ้นแล้ว! พิมพ์ `!craft` เพื่อรับยศเลย!", inline=False)
        else:
            embed.add_field(name="💡 ขาดอีกนิด!", value=f"สะสมให้ครบ 4 ชิ้นเพื่อแลกรางวัล (ตอนนี้ {found_count}/4)", inline=False)
            
        await ctx.send(embed=embed)

    @commands.command()
    async def craft(self, ctx):
        """แลกรางวัลเมื่อครบ 4 ชิ้น"""
        user_id = str(ctx.author.id)
        data = load_db()
        inventory = data.get(user_id, {}).get("inventory", [])

        # 1. เช็คว่าครบไหม
        required = ["puzzle_1", "puzzle_2", "puzzle_3", "puzzle_4"]
        for item in required:
            if item not in inventory:
                await ctx.send(f"❌ **ยังไม่ครบค่ะ!** ขาดชิ้นส่วนบางอัน ลองเช็ค `!collection` ดูนะ", ephemeral=True)
                return

        # 2. หักของออกจากกระเป๋า (Burn Items)
        for item in required:
            inventory.remove(item) # ลบออกอย่างละ 1 ชิ้น
        data[user_id]["inventory"] = inventory
        save_db(data)

        # 3. ให้รางวัล (แจกยศ)
        # ⚠️⚠️ แก้ ID ยศตรงนี้ให้เป็นของเซิร์ฟท่านนะครับ ⚠️⚠️
        VIP_ROLE_ID = 1467444157759881380 
        
        role = ctx.guild.get_role(VIP_ROLE_ID)
        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f"🎉 **ยินดีด้วย!** {ctx.author.mention} สะสมจิ๊กซอว์หัวใจครบแล้ว! ❤️\nได้รับยศ **{role.name}** เป็นรางวัล!")
        else:
            await ctx.send("✅ แลกรางวัลสำเร็จ! (แต่แอดมินลืมตั้งค่ายศ แจ้งแอดมินด่วน!)")

async def setup(bot):
    await bot.add_cog(GachaSystem(bot))