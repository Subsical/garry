import asyncio
import os
import random
from datetime import datetime, timedelta

import discord
import sqlcipher3 as sqlite3
from discord import app_commands
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)

conn = sqlite3.connect('garry.db')
conn.execute(f"PRAGMA key = \"x'{os.environ['GARRY_DB_KEY']}'\"")
cur = conn.cursor()

with open('blacklist.txt') as f:
	BLACKLIST = [int(line) for line in f.read().split()]

GUILD_ID = 1373106664785580032
GARRY_ROLE_ID = 1395927802171232366
VERIFIED_ROLE_ID = 1373107349669281792
MUTED_ROLE_ID = 1381107817498284144
NOMINATED_ROLE_ID = 1407109877935116408
GARRY_CHANNEL_ID = 1381108247687200849
GARRY_HISTORY_CHANNEL_ID = 1400498446594478221
IGNORED_EDIT_ROLES = [1381251184630960288, 1378494048586825809, 1373107494913573084, 1387495886720073818, 1373788332051529738, 1378093307066056736, GARRY_ROLE_ID]

@bot.event
async def on_ready():
	await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
	print("---OUTPUT----------\nGarry is here.")
	garry.start()

@bot.event
async def on_resumed():
	print("// resumed session")

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
	error_messages = {
		commands.MemberNotFound: "Couldn't find the user specified. Can only lookup by **user ID**, **mention**, **username#tag** or **username**.",
		commands.ChannelNotFound: "Couldn't find the channel specified. Can only lookup by **channel ID** or **mention**.",
		commands.RoleNotFound: "Couldn't find the role specified. Can only lookup by **role ID**, **mention** and **name**.",
		commands.MessageNotFound: "Couldn't find the message specified. Can only lookup by **chnl_id-msg_id** or **message link**.",
		commands.MissingRequiredArgument: "Missing required parameter.",
		commands.BadArgument: "Invalid parameter.",
		discord.Forbidden: "I don't have permission to do that.",
		AssertionError: str(error.original) if hasattr(error, "original") else ""
	}

	if isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
		pass
	elif type(error) in error_messages:
		await ctx.send(error_messages[type(error)], delete_after=5)
	elif hasattr(error, "original") and type(error.original) in error_messages:
		await ctx.send(error_messages[type(error.original)], delete_after=5)
	else:
		raise error

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
	if isinstance(error.original, AssertionError):
		await interaction.response.send_message(str(error.original), ephemeral=True)
	else:
		raise error

@bot.tree.command(name="optout")
async def optout(interaction: discord.Interaction):
	"""Leave the Garry nomination pool. (removes your Nominated role)"""
	nominated = interaction.guild.get_role(NOMINATED_ROLE_ID)
	if nominated not in interaction.user.roles:
		await interaction.response.send_message("You're not currently in the Garry nomination pool.", ephemeral=True)
		return
	await interaction.user.remove_roles(nominated)
	await interaction.response.send_message("You've been removed from the Garry nomination pool.\nYou can be re-nominated later if you opt back in through <#1387840239929790584>.", ephemeral=True)

########## ======================================================================== ##########

cur.execute("SELECT last_picked FROM Garry")
last_picked_iso, = cur.fetchone()
conn.commit()
last_picked = datetime.fromisoformat(last_picked_iso)
GARRY_DELAY = timedelta(hours=1)

@tasks.loop(seconds=5)
async def garry():
	guild = bot.get_guild(GUILD_ID)
	garry_role = guild.get_role(GARRY_ROLE_ID)
	verified_role = guild.get_role(VERIFIED_ROLE_ID)
	muted_role = guild.get_role(MUTED_ROLE_ID)
	try:
		cur.execute("SELECT cur_garry_id FROM Garry")
		cur_garry_id, = cur.fetchone()
		cur_garry = guild.get_member(cur_garry_id)
		no_one_garry = False
	except IndexError:
		cur_garry = guild.get_member(bot.user.id)  # if the garry left, pretend bot was garry
		no_one_garry = True

	if cur_garry is None or not hasattr(cur_garry, "status"):
		cur_garry = guild.get_member(bot.user.id)
		no_one_garry = True

	for member in garry_role.members:
		if member.id != cur_garry.id:
			print(f"!! {member} has the garry role but isn't the current garry ({cur_garry.id}) -- removing")
			try:
				await member.remove_roles(garry_role)
			except (discord.Forbidden, discord.HTTPException) as err:
				print(f"Failed to remove stale garry role from {member} :: {err}")

	global last_picked
	if no_one_garry or datetime.now() >= last_picked + GARRY_DELAY:
		garry_chnl = guild.get_channel(GARRY_CHANNEL_ID)
		nominated = guild.get_role(NOMINATED_ROLE_ID)
		nominees = list(nominated.members)
		random.shuffle(nominees)

		if not no_one_garry:
			try:
				await cur_garry.remove_roles(garry_role)
			except (discord.Forbidden, discord.HTTPException) as err:
				print(f"Failed to remove garry role :: {err}")

		def is_eligible(member):
			return (
				hasattr(member, "status")
				and member.status != discord.Status.offline
				and verified_role in member.roles
				and muted_role not in member.roles
				and not member.bot
				and member.id not in BLACKLIST
			)

		for member in nominees:
			member = guild.get_member(member.id)  # refresh member object
			if is_eligible(member):
				next_garry = member
				break

		overwrite = garry_chnl.overwrites_for(garry_role)
		overwrite.send_messages = True
		await garry_chnl.set_permissions(garry_role, overwrite=overwrite)

		await next_garry.add_roles(garry_role)
		await garry_chnl.send(f"{next_garry.mention}, you are now garry for one hour.")
		print(f"{next_garry} is garry now")
		last_picked = datetime.now()
		cur.execute("UPDATE Garry SET last_picked = ?, cur_garry_id = ?", (last_picked.isoformat(), next_garry.id))
		conn.commit()

@garry.error
async def garry_error(err: Exception):
	print("!!! Garry loop ran into an error:")
	print(err)
	if not garry.is_running():
		print("!! Garry loop stopped running, started again")
		garry.start()
	else:
		print("!! Garry loop has been restarted just in case")
		garry.restart()

########## ======================================================================== ##########

@bot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
	if payload.guild_id and payload.channel_id == GARRY_CHANNEL_ID and isinstance(payload.data, dict) and "edited_timestamp" in payload.data:
		guild = bot.get_guild(payload.guild_id)
		channel = guild.get_channel(payload.channel_id)
		if channel is not None:
			message = await channel.fetch_message(payload.message_id)
			ignored_members = [target.id for target, overwrite in channel.overwrites.items() if isinstance(target, discord.Member) and overwrite.send_messages is True]
			if message.edited_at is not None and message.author.id not in ignored_members and not any(role.id in IGNORED_EDIT_ROLES for role in message.author.roles):
				await message.delete()

@bot.event
async def on_message(message: discord.Message):
	# await bot.process_commands(message)
	guild = bot.get_guild(GUILD_ID)
	if message.channel.id == GARRY_CHANNEL_ID:
		garry_role = guild.get_role(GARRY_ROLE_ID)
		if garry_role in message.author.roles:
			cur.execute("SELECT cur_garry_id FROM Garry")
			cur_garry_id, = cur.fetchone()
			if cur_garry_id == message.author.id:
				overwrite = message.channel.overwrites_for(garry_role)
				overwrite.send_messages = False
				await message.channel.set_permissions(garry_role, overwrite=overwrite)

				garry_history = guild.get_channel(GARRY_HISTORY_CHANNEL_ID)
				webhook = discord.utils.get(await garry_history.webhooks(), name='garry history')
				file_attachments = await asyncio.gather(*(attachment.to_file() for attachment in message.attachments))
				content = message.clean_content or None
				await webhook.send(content=content, files=file_attachments, username=message.author.display_name, avatar_url=message.author.display_avatar.url)
				await asyncio.sleep(5)  # to make sure the other message is sent first
				await webhook.send(f"-# [Original message]({message.jump_url})", username=message.author.display_name, avatar_url=message.author.display_avatar.url)

########## ======================================================================== ##########

async def main():
	async with bot:
		await bot.start(os.environ["GARRY_BOT_TOKEN"])

asyncio.run(main())