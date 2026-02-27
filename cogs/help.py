import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ajuda", description="📘 Lista de comandos disponíveis")
    async def ajuda(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Comandos do Dpp.gg",
            description="Aqui estão os comandos que você pode usar:",
            color=discord.Color.purple()
        )

        embed.add_field(name="/perfil", value="🔍 Busca o perfil de um invocador.", inline=False)
        embed.add_field(name="/ajuda", value="📘 Exibe esta mensagem.", inline=False)
        embed.add_field(name="/patch", value="🛠️ Veja as últimas notas de atualização.", inline=False)
        embed.add_field(name="/time", value="🏟️ Info de time profissional (Liquipedia).", inline=False)
        embed.add_field(name="/user", value="👤 Perfil vinculado a um usuário.", inline=False)
        embed.add_field(name="/vincular", value="🔗 Vincula sua conta ao LoL.", inline=False)
        embed.add_field(name="/desvincular", value="❌ Remove a vinculação.", inline=False)

        embed.set_footer(text="Feito com ❤️ por Dopplin_")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))