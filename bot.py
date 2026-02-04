import discord
from discord.ext import commands
import asyncio
import random
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO
from PIL import Image

# ----------------------------
# INTENTS
# ----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# CONFIG
# ----------------------------
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

STAFF_ROLE_ID = 1429976672664293376
TICKET_CATEGORY_ID = None
STAFF_LOG_CHANNEL_ID = 1467630513811488882
WELCOME_CHANNEL_ID = 1429983452794458152
GIVEAWAY_CHANNEL_ID = 1429967315512070244
BOOSTER_ROLE_ID = 1464860869375688745
MIDDLEMAN_ROLE_ID = 1464809947283063013  # Middleman role ID


# ----------------------------
# WELCOME SYSTEM
# ----------------------------
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        print("Welcome channel not found.")
        return

    color = discord.Color.green()
    if member.banner:
        try:
            banner_url = member.banner.url
            response = requests.get(banner_url)
            img = Image.open(BytesIO(response.content))
            img = img.resize((1, 1))
            avg_color = img.getpixel((0, 0))
            color = discord.Color.from_rgb(*avg_color)
        except Exception as e:
            print(f"Could not fetch banner color: {e}")

    embed = discord.Embed(
        title=f"Welcome {member.name}!",
        description=f"🎉 Welcome to {member.guild.name}, {member.mention}! Check the rules and have fun!",
        color=color
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    await channel.send(embed=embed)

# ----------------------------
# ANNOUNCEMENTS
# ----------------------------
@bot.command()
async def announce(ctx, *, message):
    embed = discord.Embed(description=message, color=discord.Color.red())
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.display_avatar.url)
    embed.set_image(url="https://i.imgur.com/bk7c3Ih.png")
    embed.set_footer(text="Made for STB Fan Group™")
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ----------------------------
# SCAMMER REPORT
# ----------------------------
class ScammerReportModal(discord.ui.Modal, title="Scammer Report"):
    scammer = discord.ui.TextInput(label="Scammer Username / ID", required=True)
    reason = discord.ui.TextInput(label="What happened?", style=discord.TextStyle.paragraph, required=True)
    loss = discord.ui.TextInput(label="Amount / Items Lost", required=True)
    proof = discord.ui.TextInput(label="Proof (links or explanation)", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🚨 Scammer Report", color=discord.Color.red())
        embed.add_field(name="Reporter", value=interaction.user.mention, inline=False)
        embed.add_field(name="Scammer", value=self.scammer.value, inline=False)
        embed.add_field(name="What Happened", value=self.reason.value, inline=False)
        embed.add_field(name="Loss", value=self.loss.value, inline=False)
        embed.add_field(name="Proof", value=self.proof.value, inline=False)

        await interaction.response.send_message("✅ **Scammer report submitted to staff.**", ephemeral=True)
        staff_channel = interaction.guild.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            await staff_channel.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ Staff channel not found.", ephemeral=True)

class ScammerReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Report a Scammer", style=discord.ButtonStyle.danger, custom_id="report_scammer_panel")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ScammerReportModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def reportscammer(ctx):
    embed = discord.Embed(title="🚨 Report a Scammer",
                          description="Click the button below to submit a scammer report.",
                          color=discord.Color.red())
    await ctx.send(embed=embed, view=ScammerReportView())

# ----------------------------
# TICKET SYSTEM
# ----------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(MIDDLEMAN_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Only staff can close tickets.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Ticket closed. Deleting in 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Create MM Ticket", style=discord.ButtonStyle.danger, custom_id="create_ticket_button")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(MIDDLEMAN_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
        channel = await guild.create_text_channel(name=f"trade-{user.name}", overwrites=overwrites, category=category)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

        def check(m): return m.author == user and m.channel == channel
        while True:
            try:
                await channel.send("**1️⃣ Who are you trading with?**")
                trader = await bot.wait_for("message", check=check, timeout=120)
                await channel.send("**2️⃣ Are you buying, selling, or trading?**")
                trade_type = await bot.wait_for("message", check=check, timeout=120)
                trade_detail = None
                trade_type_lower = trade_type.content.lower()
                if "buy" in trade_type_lower:
                    await channel.send("**➡️ What are you buying?**")
                    trade_detail = await bot.wait_for("message", check=check, timeout=120)
                elif "sell" in trade_type_lower:
                    await channel.send("**➡️ What are you selling?**")
                    trade_detail = await bot.wait_for("message", check=check, timeout=120)
                if trade_detail:
                    trade = trade_detail
                else:
                    await channel.send("**3️⃣ What is the trade?**")
                    trade = await bot.wait_for("message", check=check, timeout=300)
                await channel.send("**4️⃣ Are you providing a tip? (Yes / No)**")
                tip = await bot.wait_for("message", check=check, timeout=120)
            except asyncio.TimeoutError:
                await channel.send("❌ Ticket timed out.")
                return

            embed = discord.Embed(title="📄 Middleman Ticket Summary", color=discord.Color.red())
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Trading With", value=trader.content, inline=False)
            type_text = trade_type.content
            if trade_detail:
                type_text += f"\n**Details:** {trade_detail.content}"
            embed.add_field(name="Type", value=type_text, inline=False)
            embed.add_field(name="Trade Details", value=trade.content, inline=False)
            embed.add_field(name="Providing a Tip?", value=tip.content, inline=False)
            await channel.send(embed=embed)
            await channel.send("✅ **Please confirm this deal (Yes / No)**")
            confirm = await bot.wait_for("message", check=check, timeout=120)
            if confirm.content.lower() in ["yes", "y"]:
                await channel.send("✅ **Deal confirmed. Staff may now review.**", view=CloseTicketView())
                break
            else:
                await channel.send("🔁 **Re-enter the details.**")

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(title="MM Requests", description="Click the button below to create a middleman ticket.", color=discord.Color.red())
    await ctx.send(embed=embed, view=TicketView())

# ----------------------------
# GIVEAWAY SYSTEM
# ----------------------------
giveaways = {}

class GiveawayEntryView(discord.ui.View):
    def __init__(self, prize, winners_count, duration, required_roles, extra_roles, creator):
        super().__init__(timeout=None)
        self.prize = prize
        self.winners_count = winners_count
        self.required_roles = required_roles
        self.extra_roles = extra_roles
        self.entries = {}
        self.end_time = datetime.utcnow() + timedelta(seconds=duration)
        self.creator = creator
        self.message = None
        self.ended = False
        self.countdown_task = None

    @discord.ui.button(label="🎊 Enter Giveaway", style=discord.ButtonStyle.danger)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_roles = [r.id for r in interaction.user.roles]
        count = 1
        if BOOSTER_ROLE_ID in member_roles:
            count = 3
        for role_name in self.extra_roles:
            if role_name in [r.name for r in interaction.user.roles]:
                count += 1
        self.entries[interaction.user.id] = count

        # Update participant count immediately
        embed = self.message.embeds[0]
        embed.set_field_at(1, name="Participants", value=str(len(self.entries)), inline=False)
        await self.message.edit(embed=embed)

        await interaction.response.send_message(f"✅ Entered giveaway with {count} entries!", ephemeral=True)

    async def start_countdown(self):
        while not self.ended:
            remaining = self.end_time - datetime.utcnow()
            if remaining.total_seconds() <= 0:
                break
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            hours, mins = divmod(mins, 60)
            days, hours = divmod(hours, 24)
            time_text = f"{days}d {hours}h {mins}m {secs}s remaining"
            embed = self.message.embeds[0]
            embed.set_field_at(0, name="Time Left", value=time_text, inline=False)
            await self.message.edit(embed=embed)
            await asyncio.sleep(30)
        await self.end_giveaway()

    async def end_giveaway(self):
        if self.ended:
            return
        self.ended = True
        if self.countdown_task:
            self.countdown_task.cancel()

        all_entries = []
        for user_id, weight in self.entries.items():
            all_entries.extend([user_id]*weight)

        winners = []
        try:
            for _ in range(self.winners_count):
                winner_id = random.choice(all_entries)
                if winner_id not in winners:
                    winners.append(winner_id)
        except IndexError:
            pass

        winner_mentions = ", ".join([f"<@{w}>" for w in winners]) or "No entries"

        embed = self.message.embeds[0]
        embed.color = discord.Color.gold()
        embed.title = f"🎉 Giveaway Ended: {self.prize}"
        embed.set_field_at(0, name="Winners", value=winner_mentions, inline=False)
        embed.set_field_at(1, name="Participants", value=str(len(self.entries)), inline=False)
        await self.message.edit(embed=embed)
        await self.message.channel.send(f"🎉 **Giveaway ended!** Prize: **{self.prize}**\nWinners: {winner_mentions}")
        giveaways.pop(self.message.id, None)

@bot.command()
async def giveaway(ctx):
    if ctx.channel.id != GIVEAWAY_CHANNEL_ID:
        await ctx.send(f"❌ Use this command only in <#{GIVEAWAY_CHANNEL_ID}>", delete_after=10)
        return

    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    questions = [
        "**1️⃣ Prize?**",
        "**2️⃣ Number of winners?**",
        "**3️⃣ Duration (e.g., 10m, 2h)?**",
        "**4️⃣ Roles required (comma or 'none')?**",
        "**5️⃣ Roles with extra entries (comma or 'none')?**"
    ]
    answers = []
    for q in questions:
        question_msg = await ctx.send(q)
        try:
            msg = await bot.wait_for("message", check=check, timeout=300)
            answers.append(msg.content)
            await question_msg.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await ctx.send("❌ Giveaway setup timed out.")
            return

    prize = answers[0]
    try:
        winners_count = max(1, int(answers[1]))
    except:
        winners_count = 1
    duration_text = answers[2]
    required_roles = [r.strip() for r in answers[3].split(",")] if answers[3].lower() != "none" else []
    extra_roles = [r.strip() for r in answers[4].split(",")] if answers[4].lower() != "none" else []

    match = re.match(r"(\d+)([smhd])", duration_text)
    if not match:
        await ctx.send("❌ Invalid duration format!")
        return
    amount, unit = int(match[1]), match[2].lower()
    seconds = amount * {"s":1, "m":60, "h":3600, "d":86400}[unit]

    embed = discord.Embed(title=f"🎉 Giveaway: {prize}",
                          description=f"Click the 🎊 button below to enter!\nRequired Roles: {'None' if not required_roles else ', '.join(required_roles)}\nExtra Roles: {'None' if not extra_roles else ', '.join(extra_roles)}",
                          color=discord.Color.red())
    embed.add_field(name="Time Left", value=duration_text, inline=False)
    embed.add_field(name="Participants", value="0", inline=False)
    embed.set_footer(text=f"Created by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    view = GiveawayEntryView(prize, winners_count, seconds, required_roles, extra_roles, ctx.author)
    message = await ctx.send(embed=embed, view=view)
    view.message = message
    giveaways[message.id] = view
    view.countdown_task = bot.loop.create_task(view.start_countdown())

# ----------------------------
# END GIVEAWAY COMMAND
# ----------------------------
@bot.command()
async def end(ctx, message_id: int):
    view = giveaways.get(message_id)
    if not view:
        await ctx.send("❌ Giveaway not found.")
        return
    await view.end_giveaway()
    await ctx.send(f"✅ Giveaway **{view.prize}** ended early by {ctx.author.mention}.")

# ----------------------------
# ON READY
# ----------------------------
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Running STB Fan Group"))
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(ScammerReportView())
    print(f"Logged in as {bot.user}")

# ----------------------------
# RUN BOT
# ----------------------------
bot.run(BOT_TOKEN)
