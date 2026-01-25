import discord
from discord.ext import commands
import aiosqlite
import datetime
import os

# --- ตั้งค่า Token ---


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True #
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # สร้าง Database และตารางเก็บคิว
        async with aiosqlite.connect("queue_system.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS queues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    status TEXT DEFAULT 'waiting',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
        
        # ทำให้ปุ่มทำงานตลอดเวลาแม้บอทจะรีสตาร์ท
        self.add_view(CustomerView())
        self.add_view(StaffView())
        print("Bot & Database Ready!")

bot = MyBot()

# --- 1. หน้าตาปุ่มสำหรับลูกค้า (Customer View) ---
class CustomerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # ปุ่มไม่หมดอายุ

    @discord.ui.button(label="รับบัตรคิว (Get Queue)", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="cust_get")
    async def get_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        async with aiosqlite.connect("queue_system.db") as db:
            # เช็กว่ามีคิวค้างอยู่ไหม
            async with db.execute("SELECT id FROM queues WHERE user_id = ? AND status = 'waiting'", (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                await interaction.response.send_message(f"⚠️ คุณมีคิวอยู่แล้วค่ะ: **A-{row[0]:03}**", ephemeral=True)
                return

            # เพิ่มคิวใหม่
            await db.execute("INSERT INTO queues (user_id) VALUES (?)", (user_id,))
            await db.commit()
            
            async with db.execute("SELECT last_insert_rowid()") as cursor:
                q_id = (await cursor.fetchone())[0]

        await interaction.response.send_message(f"✅ **รับคิวสำเร็จ!** หมายเลขของคุณคือ **A-{q_id:03}**\nกรุณารอการเรียกจากเมดนะคะ", ephemeral=True)

    @discord.ui.button(label="ยกเลิกคิว (Cancel)", style=discord.ButtonStyle.danger, emoji="✖️", custom_id="cust_cancel")
    async def cancel_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        async with aiosqlite.connect("queue_system.db") as db:
            await db.execute("UPDATE queues SET status = 'cancelled' WHERE user_id = ? AND status = 'waiting'", (user_id,))
            await db.commit()
        await interaction.response.send_message("❌ ยกเลิกคิวของคุณเรียบร้อยแล้วค่ะ", ephemeral=True)

# --- 2. แผงควบคุมสำหรับเมด (Staff View) ---
class StaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="เรียกคิวถัดไป", style=discord.ButtonStyle.success, emoji="🔔", custom_id="staff_next")
    async def next_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect("queue_system.db") as db:
            async with db.execute("SELECT id, user_id FROM queues WHERE status = 'waiting' ORDER BY id ASC LIMIT 1") as cursor:
                row = await cursor.fetchone()
            
            if row:
                q_id, u_id = row
                await db.execute("UPDATE queues SET status = 'called' WHERE id = ?", (q_id,))
                await db.commit()
                # ส่งข้อความเรียกแบบประกาศให้ทุกคนเห็น
                await interaction.channel.send(f"🔔 **คิว A-{q_id:03}** <@{u_id}> เชิญรับบริการได้เลยค่ะ!")
                await interaction.response.send_message(f"เรียกคิว A-{q_id:03} แล้ว", ephemeral=True)
            else:
                await interaction.response.send_message("❌ ไม่มีคิวรออยู่ในขณะนี้", ephemeral=True)

    @discord.ui.button(label="ล้างคิวทั้งหมด", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="staff_clear")
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ตรวจสอบสิทธิ์ (เฉพาะแอดมินหรือเจ้าของร้าน)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("เฉพาะ Admin เท่านั้นที่ล้างคิวได้ค่ะ", ephemeral=True)
            
        async with aiosqlite.connect("queue_system.db") as db:
            await db.execute("UPDATE queues SET status = 'cleared' WHERE status = 'waiting'")
            await db.commit()
        await interaction.response.send_message("🧹 ล้างคิวรอทั้งหมดเรียบร้อยแล้วค่ะ", ephemeral=True)

# --- คำสั่ง Setup (พิมพ์ครั้งเดียวเพื่อวางแผงปุ่ม) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_system(ctx):
    # ส่งแผงกดของลูกค้า
    embed_cust = discord.Embed(title="🏨 จุดรับบัตรคิว", description="กดปุ่มด้านล่างเพื่อรับคิวค่ะ", color=discord.Color.blue())
    await ctx.send(embed=embed_cust, view=CustomerView())

    # ส่งแผงควบคุมของเมด (ควรทำในห้องลับสำหรับ Staff)
    embed_staff = discord.Embed(title="👩‍💼 แผงควบคุมเมด", description="กดเรียกคิวลูกค้าจากตรงนี้ได้เลยค่ะ", color=discord.Color.green())
    await ctx.send(embed=embed_staff, view=StaffView())

bot.run(os.getenv('TOKEN'))