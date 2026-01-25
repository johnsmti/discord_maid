import discord
from discord.ext import commands
from discord import ui
import datetime
import pytz 

# เก็บข้อมูลการเข้างาน
ACTIVE_SHIFTS = {} 

# ⚠️ แก้ 2 บรรทัดนี้ให้เป็น ID ของคุณ ⚠️
LOG_CHANNEL_ID = 1459813695872958587  # ID ห้อง Log
ON_DUTY_ROLE_ID = 1453037587135463527 # 👈 เอา ID ยศที่ต้องการแจกมาใส่ตรงนี้!

# ตั้ง Timezone
TH_TIMEZONE = pytz.timezone('Asia/Bangkok')

class TimeClockView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    # --- ปุ่มเข้างาน (สีเขียว) ---
    @ui.button(label="เข้างาน (Clock In)", style=discord.ButtonStyle.success, emoji="⏰", custom_id="btn_clock_in")
    async def clock_in(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        
        # เช็คว่าเข้างานอยู่แล้วหรือเปล่า?
        if user_id in ACTIVE_SHIFTS:
            start_time = ACTIVE_SHIFTS[user_id]
            fmt_time = start_time.strftime('%H:%M') + " น."
            await interaction.response.send_message(f"⚠️ **คุณเข้างานไปแล้วนะคะ!** ตั้งแต่เวลา {fmt_time}", ephemeral=True)
            return

        # เริ่มบันทึกเวลาปัจจุบัน
        now = datetime.datetime.now(TH_TIMEZONE)
        ACTIVE_SHIFTS[user_id] = now
        time_str = now.strftime('%H:%M') + " น."

        # ⭐ [ส่วนเพิ่มใหม่] แจกยศเข้างาน
        role = interaction.guild.get_role(ON_DUTY_ROLE_ID)
        if role:
            try:
                await interaction.user.add_roles(role)
            except:
                # กันเหนียว: เผื่อบอทยศต่ำกว่า หรือไม่มีสิทธิ์
                print(f"Error: ไม่สามารถแจกยศ {role.name} ได้ (เช็คลำดับยศบอทด้วย!)")
        
        # แจ้งเตือนคนกด
        await interaction.response.send_message(f"✅ **ลงเวลาและรับยศเข้างานเรียบร้อยค่ะ!**\n🕒 เริ่มงานเวลา: {time_str}\nขอให้วันนี้เป็นวันที่สดใสนะคะ! ✌️", ephemeral=True)
        
        # ส่ง Log ไปห้องผู้จัดการ
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🟢 มีพนักงานเข้างาน", color=0x2ecc71)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="พนักงาน", value=interaction.user.mention, inline=True)
            log_time = now.strftime('%d/%m/%Y %H:%M') + " น."
            embed.add_field(name="เวลาเข้า", value=log_time, inline=True)
            await log_channel.send(embed=embed)

    # --- ปุ่มออกงาน (สีแดง) ---
    @ui.button(label="ออกงาน (Clock Out)", style=discord.ButtonStyle.danger, emoji="👋", custom_id="btn_clock_out")
    async def clock_out(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        
        # เช็คว่าเข้างานมาหรือยัง?
        if user_id not in ACTIVE_SHIFTS:
            await interaction.response.send_message("❌ **คุณยังไม่ได้กดเข้างานเลยนะคะ!** (หรืออาจจะบอทรีเซ็ตไปแล้ว)", ephemeral=True)
            return

        # คำนวณเวลา
        start_time = ACTIVE_SHIFTS[user_id]
        end_time = datetime.datetime.now(TH_TIMEZONE)
        duration = end_time - start_time
        
        # แปลงเวลาทำงาน
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        # ลบชื่อออกจากระบบ
        del ACTIVE_SHIFTS[user_id]
        start_str = start_time.strftime('%H:%M') + " น."
        end_str = end_time.strftime('%H:%M') + " น."

        # ⭐ [ส่วนเพิ่มใหม่] ปลดออกยศงาน
        role = interaction.guild.get_role(ON_DUTY_ROLE_ID)
        if role:
            try:
                await interaction.user.remove_roles(role)
            except:
                print(f"Error: ไม่สามารถดึงยศ {role.name} คืนได้")

        # แจ้งเตือนคนกด (สรุปยอด)
        await interaction.response.send_message(
            f"👋 **เลิกงานแล้ว คืนยศเรียบร้อยค่ะ!**\n"
            f"🕒 เข้างาน: {start_str}\n"
            f"🕒 ออกงาน: {end_str}\n"
            f"⏱️ **รวมเวลาทำงาน: {hours} ชั่วโมง {minutes} นาที**", 
            ephemeral=True
        )

        # ส่ง Log ไปห้องผู้จัดการ
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🔴 มีพนักงานออกงาน", color=0xe74c3c)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="พนักงาน", value=interaction.user.mention, inline=True)
            log_out_time = end_time.strftime('%d/%m/%Y %H:%M') + " น."
            embed.add_field(name="เวลาออก", value=log_out_time, inline=True)
            embed.add_field(name="รวมระยะเวลา", value=f"**{hours} ชม. {minutes} นาที**", inline=False)
            await log_channel.send(embed=embed)

class TimeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setup_clock(self, ctx):
        embed = discord.Embed(
            title="⏰ ระบบบันทึกเวลาทำงาน (Time Attendance)",
            description="กดปุ่มด้านล่างเพื่อลงเวลาเข้า/ออกงานนะคะ\n\n🟢 **เข้างาน** = รับยศ + เริ่มนับเวลา\n🔴 **ออกงาน** = คืนยศ + สรุปยอดชั่วโมงทำงาน",
            color=0x3498db
        )
        embed.set_image(url="https://media.tenor.com/On7kvXhzml4AAAAd/anime-clock.gif") 
        
        await ctx.send(embed=embed, view=TimeClockView())
        await ctx.message.delete() 

async def setup(bot):
    await bot.add_cog(TimeSystem(bot))