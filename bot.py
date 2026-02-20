import discord
from discord.ext import commands
import asyncio
import requests
from io import BytesIO
from PIL import Image
from datetime import timedelta



# ----------------------------
# INTENTS
# ----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
# Kick
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked. Reason: {reason}")
    except:
        await ctx.send("I can't kick this user.")

# Ban
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned. Reason: {reason}")
    except:
        await ctx.send("I can't ban this user.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int = 5):
    try:
        await member.timeout(timedelta(minutes=minutes))
        await ctx.send(f"{member} muted for {minutes} minutes.")
    except Exception as e:
        await ctx.send("I can't mute this user.")
        print(e)
# ----------------------------
# CONFIG
# ----------------------------
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

STAFF_ROLE_ID = 1429976672664293376
MIDDLEMAN_ROLE_ID = 1464809947283063013

TICKET_CATEGORY_ID = None
STAFF_LOG_CHANNEL_ID = 1467630513811488882
APPLICATION_LOG_CHANNEL_ID = 1472387817224147160
WELCOME_CHANNEL_ID = 1429983452794458152

# ----------------------------
# WELCOME SYSTEM
# ----------------------------
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    color = discord.Color.green()
    try:
        if member.banner:
            response = requests.get(member.banner.url)
            img = Image.open(BytesIO(response.content)).resize((1, 1))
            avg_color = img.getpixel((0, 0))
            color = discord.Color.from_rgb(*avg_color)
    except:
        pass

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
    embed.set_image(url="https://i.imgur.com/70qSEPX.png")
    embed.set_footer(text="Made for STB Fan Group™")
    await ctx.send(embed=embed)
    await ctx.message.delete()

# ----------------------------
# SCAMMER REPORT SYSTEM
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

        await interaction.response.send_message("✅ Scammer report submitted to staff.", ephemeral=True)

        staff_channel = interaction.guild.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            await staff_channel.send(embed=embed)

class ScammerReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Report a Scammer", style=discord.ButtonStyle.danger, custom_id="report_scammer")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ScammerReportModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def reportscammer(ctx):
    embed = discord.Embed(
        title="🚨 Report a Scammer",
        description="Click the button below to submit a scammer report.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=ScammerReportView())

# ----------------------------
# TICKET SYSTEM
# ----------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(MIDDLEMAN_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Only Middlemen can close tickets.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Ticket closing...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create MM Ticket", style=discord.ButtonStyle.danger, custom_id="create_mm_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(MIDDLEMAN_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"trade-{user.name}",
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="MM Requests",
        description="Click below to create a middleman ticket.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=TicketView())

# ----------------------------
# APPLICATION SYSTEM
# ----------------------------
class ApplicationDecisionView(discord.ui.View):
    def __init__(self, applicant_id):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="approve_app")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admins only.", ephemeral=True)
            return

        member = interaction.guild.get_member(self.applicant_id)
        role = interaction.guild.get_role(STAFF_ROLE_ID)

        if member and role:
            await member.add_roles(role)
            await member.send("🎉 Your application has been **approved**! Welcome to the SFG team.")

        await interaction.response.send_message("✅ Application approved.", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="deny_app")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admins only.", ephemeral=True)
            return

        member = interaction.guild.get_member(self.applicant_id)
        if member:
            await member.send("❌ Your application has been **denied**. You may reapply later.")

        await interaction.response.send_message("❌ Application denied.", ephemeral=True)

class ApplicationModal(discord.ui.Modal, title="Staff Application"):
    age = discord.ui.TextInput(label="How old are you?", required=True)
    discord_user = discord.ui.TextInput(label="Your Discord Username", required=True)
    experience = discord.ui.TextInput(label="Do you have current/past experience?", style=discord.TextStyle.paragraph, required=True)
    rule_break = discord.ui.TextInput(label="What would you do if someone breaks a rule?", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📋 New Staff Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=interaction.user.mention, inline=False)
        embed.add_field(name="Age", value=self.age.value, inline=False)
        embed.add_field(name="Discord", value=self.discord_user.value, inline=False)
        embed.add_field(name="Experience", value=self.experience.value, inline=False)
        embed.add_field(name="Rule Handling", value=self.rule_break.value, inline=False)

        await interaction.response.send_message("✅ Your application has been submitted.", ephemeral=True)

        try:
            await interaction.user.send("📩 Your staff application has been received. You will be notified once reviewed. You may also be put on hold if we want you but not in the current moment. Thanks!")
        except:
            pass

        channel = interaction.guild.get_channel(APPLICATION_LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed, view=ApplicationDecisionView(interaction.user.id))

class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.primary, custom_id="apply_staff")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def applicationpanel(ctx):
    embed = discord.Embed(
        title="Staff Applications",
        description="Click below to apply for staff.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=ApplicationView())

# ----------------------------
# ON READY
# ----------------------------
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Running STB Fan Group"))
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(ScammerReportView())
    bot.add_view(ApplicationView())
    print(f"Logged in as {bot.user}")


# Delete daydreamz FVB ACC ID: 129598205830453

# initiate skibidi toilet delete acc. he luvs me, he luvs me not
# ----------------------------
# RUN BOT
# ----------------------------
bot.run(BOT_TOKEN)


