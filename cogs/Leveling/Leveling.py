import discord
import functools
import vacefron
import asyncio

from typing import Optional
from datetime import datetime

from discord.ext import commands, tasks
from discord.ext.commands import BucketType

from discordLevelingSystem import LevelUpAnnouncement, DiscordLevelingSystem, RoleAward
from disrank.generator import Generator


from utils.constants import BOT_AVATAR_URL, EMBED_COLOR, SUCCESS_COLOR, CHECKMARK_EMOJI, LOADING_CIRCLE_EMOJI, ERROR_EMOJI, ERROR_COLOR
from utils.logging import log

grovestreet_guild_id = 806599466604953641

role_awards = {
	grovestreet_guild_id: [
		RoleAward(role_id=806627825607245914, level_requirement=10),
		RoleAward(role_id=806600331009720424, level_requirement=20),
		RoleAward(role_id=806599466604953642, level_requirement=30),
		RoleAward(role_id=806627828946829364, level_requirement=40),
		RoleAward(role_id=806599466903011368, level_requirement=50),
		RoleAward(role_id=806627830884073473, level_requirement=60),
		RoleAward(role_id=806630809217925150, level_requirement=70),
		RoleAward(role_id=806626707653525504, level_requirement=80),
		RoleAward(role_id=806599466604953643, level_requirement=90),
		RoleAward(role_id=806599466604953644, level_requirement=100),
	]
}

vac_api = vacefron.Client()


announcement_embed = discord.Embed(
	color=SUCCESS_COLOR, description=f"{CHECKMARK_EMOJI} {LevelUpAnnouncement.Member.mention}, You are now Level `{LevelUpAnnouncement.LEVEL}`"
)
announcement_embed.add_field(name="Rank", value=f"#{LevelUpAnnouncement.RANK}")
announcement_embed.add_field(name="Total XP", value=f"{LevelUpAnnouncement.TOTAL_XP}")

announcement_embed.set_author(name=LevelUpAnnouncement.Member.name, icon_url=LevelUpAnnouncement.Member.avatar_url)
announcement_embed.set_thumbnail(url=LevelUpAnnouncement.Member.avatar_url)
announcement_embed.set_footer(text=f"User ID: {LevelUpAnnouncement.Member.id}", icon_url=LevelUpAnnouncement.Member.avatar_url)


grovestreet_level_up_channel_id = 892515478180855858

class Leveling(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.announcement = LevelUpAnnouncement(message=announcement_embed, level_up_channel_ids=[grovestreet_level_up_channel_id], tts=False)
		self.leveling = DiscordLevelingSystem(rate=1, per=60, awards=role_awards, level_up_announcement=self.announcement, bot=self.bot, stack_awards=True)
		self.leveling.connect_to_database_file(path=r'C:\Users\Dante\Documents\Groovestreet Bot\db\Leveling\DiscordLevelingSystem.db')
		self.clean_database.start()

	def cog_unload(self):
		self.clean_database.cancel()

	def get_card(self, args):
		image = Generator().generate_profile(**args)
		return image

	
	@commands.Cog.listener()
	async def on_ready(self):
		log.info(f"[cyan1][MODULE] {type(self).__name__} Loaded.[/cyan1]")


	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):

		await self.leveling.award_xp(amount=[15, 25], message=message, refresh_name=True, bonus=DiscordLevelingSystem.Bonus([806599466903011366, 806599466903011365], bonus_amount=2, multiply=True))

	@commands.command()
	@commands.guild_only()
	@commands.cooldown(1, 5, BucketType.user)
	async def rank(self, ctx: commands.Context, member: Optional[discord.Member]):
		await ctx.message.delete()

		if member is None:
			member = ctx.author

		data = await self.leveling.get_data_for(member)

		needed_xp_for_next_level = self.leveling.get_xp_for_level(int(data.level) + 1)

		args = {
			'bg_image' : 'https://media.discordapp.net/attachments/892360396852326420/892526021054697512/unknown.png', # Background image link (Optional)
			'profile_image' : member.display_avatar.replace(size=128, format="png", static_format="png").url, # User profile picture link
			'level' : int(data.level), # User current level 
			'current_xp' : int(0), # Current level minimum xp 
			'user_xp' : int(data.xp), # User current xp
			'next_xp' : needed_xp_for_next_level, # xp required for next level
			'user_position' : int(data.rank), # User position in leaderboard
			'user_name' : str(member), # user name with descriminator 
			'user_status' : member.status.name, # User status eg. online, offline, idle, streaming, dnd
		}

		func = functools.partial(self.get_card, args)
		image = await asyncio.get_event_loop().run_in_executor(None, func)


		rank_image = discord.File(fp = image, filename = f"{member.name}_rank.png")
		await ctx.author.send(file = rank_image)

	@commands.command()
	@commands.cooldown(1, 5, BucketType.user)
	async def leaderboard(self, ctx: commands.Context):
		await ctx.message.delete()
		data = await self.leveling.each_member_data(ctx.guild, sort_by='rank')
		embed = discord.Embed(
			color=EMBED_COLOR,
			timestamp=datetime.utcnow()
		)
		for i in data:
			embed.add_field(name=ctx.guild.get_member(i.id_number), value=f"**Level:** `{i.level}`", inline=False)
		embed.set_author(name=ctx.guild.name, icon_url=BOT_AVATAR_URL)
		embed.set_thumbnail(url=BOT_AVATAR_URL)
		embed.set_footer(text=f"Requested By {ctx.author.name} | ID: {ctx.author.id}", icon_url=ctx.author.avatar_url)
		await ctx.author.send(embed=embed)

	@commands.group(invoke_without_subcommand=False)
	@commands.is_owner()
	@commands.guild_only()
	async def level(self, ctx: commands.Context):
		pass

	@level.command()
	async def reset(self, ctx: commands.Context, member: discord.Member):
		embed = discord.Embed(
			color=discord.Color.blue(),
			timestamp=datetime.utcnow()
		)
		embed.add_field(name="Are you sure?", value="Deleting someone\'s data **cannot** be reversed. Do you still want to do it?")
		await ctx.send(embed=embed)

		def check(m):
			return m.content == "yes" and m.channel is ctx.channel

		try:
			await self.bot.wait_for('message', timeout=60, check=check)
			embed_1 = discord.Embed(color=SUCCESS_COLOR, description=f"{LOADING_CIRCLE_EMOJI} Resetting {member.mention}'s XP & Level.")
			embed_2 = discord.Embed(color=SUCCESS_COLOR, description=f"{CHECKMARK_EMOJI} XP & Level For {member.mention} Has Been Reset To 0.")
			msg = await ctx.send(embed=embed_1)
			await asyncio.sleep(2)
			await self.leveling.reset_member(member)
			await msg.edit(embed=embed_2)
		except asyncio.TimeoutError:
			embed = discord.Embed(color=ERROR_COLOR, description=f"{ERROR_EMOJI}, {ctx.author.mention} Timeout Hit.")
			await ctx.send(embed=embed, delete_after=10)


	@tasks.loop(hours=1)
	async def clean_database(self):
		for guild in self.bot.guilds:
			if guild.id == 806599466604953641:
				await self.leveling.clean_database(guild=guild)
				log.info("[cyan1][DATABASE] PRUNED DATABASE.[/cyan1]")

	@clean_database.before_loop
	async def before_clean_database(self):
		log.info('[cyan1][MODULE] Leveling Tasks Loading[/cyan1]')
		await self.bot.wait_until_ready()



def setup(bot):
	bot.add_cog(Leveling(bot))