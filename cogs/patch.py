import discord
from discord import app_commands
from discord.ext import commands

from services.patchnotes import get_latest_patch_note_with_skins_async
from utils.constants import LOL_ICON

class PatchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="patch", description="🛠️ Veja as últimas notas de atualização do LoL")
    async def patch(self, interaction: discord.Interaction):
        await interaction.response.defer()

        patch = await get_latest_patch_note_with_skins_async()
        if not patch:
            await interaction.followup.send("❌ Não consegui acessar as notas agora. Tente mais tarde.")
            return

        embed = discord.Embed(
            title=f"📢 {patch['title']}",
            description=f"{patch['description']}\n\n🔗 [Leia a nota completa aqui]({patch['url']})",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=LOL_ICON)
        embed.set_footer(text="🔹 Patch oficial do League of Legends | Dpp.gg")

        if patch.get("skin_img"):
            embed.add_field(name="🆕 Novas Skins / Atualização", value=patch.get("skin_text") or "Info não disponível", inline=False)
            embed.set_image(url=patch["skin_img"])

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(PatchCog(bot))