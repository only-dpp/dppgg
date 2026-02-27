import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote

from services.leagueofgraphs import get_league_of_graphs_profile_async
from utils.formatting import rank_color
from utils.constants import EMBED_FOOTER_TEXT, EMBED_FOOTER_ICON


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="perfil",
        description="🔍 Buscar perfil do LoL no League of Graphs"
    )
    @app_commands.describe(
        region="Região do servidor (ex: br, na, euw)",
        nickname_tag="Nome do invocador (ex: Nome#TAG)"
    )
    async def perfil(self, interaction: discord.Interaction, region: str, nickname_tag: str):
        await interaction.response.defer()

        region = (region or "").strip().lower()
        nickname_tag = (nickname_tag or "").strip().replace("#", "-")

        data = await get_league_of_graphs_profile_async(nickname_tag, region)

        if not data:
            await interaction.followup.send(
                f"❌ Não encontrei '{nickname_tag}' na região `{region}`. Confira o nick/tag.",
                ephemeral=True
            )
            return

        color = rank_color(data.get("rank"))
        url = f"https://www.leagueofgraphs.com/summoner/{region}/{quote(data['url_name'])}"

        embed = discord.Embed(
            title=f"👤 {data['name']}",
            url=url,
            color=color,
            description=f"🔍 Estatísticas de **{data['name']}** no servidor."
        )

        # Thumbnail: foto do invocador (quando vier válida)
        thumb = (data.get("profile_img") or "").strip()
        if thumb.startswith("http://") or thumb.startswith("https://"):
            embed.set_thumbnail(url=thumb)

        # Rank + ícone do rank no "author" (não briga com thumbnail)
        rank_line = f"{data.get('rank','Unranked')} ({data.get('lp','–')} PDL)"
        rank_icon = (data.get("rank_img") or "").strip()
        if rank_icon.startswith("http://") or rank_icon.startswith("https://"):
            embed.set_author(name=rank_line, icon_url=rank_icon)
        else:
            embed.add_field(name="🏆 Rank", value=f"**{rank_line}**", inline=True)

        # Últimas partidas
        lm = data.get("last_matches", [])
        text = ""
        for idx, m in enumerate(lm, start=1):
            kda = m.get("kda", "KDA não disponível")
            res = (m.get("result") or "").lower()
            result_emoji = "✅" if "victory" in res else ("❌" if "defeat" in res else "➖")

            text += (
                f"**Partida {idx}:**\n"
                f"👻 Campeão: `{m.get('champion','–')}`\n"
                f"{result_emoji} {m.get('result','–')}: `🗓️ {m.get('date','–')} | 🕹️ {m.get('mode','–')}`\n"
                f"⏱️ Duração: `{m.get('duration','–')}`\n"
                f"💰 KDA: `{kda}`\n\n"
            )

        embed.add_field(name="🎮 Nível", value=f"**{data.get('level','–')}**", inline=True)

        # Só adiciona Win Rate como campo se não estiver usando rank no campo (a gente já adiciona rank acima quando não tem icon)
        embed.add_field(name="📊 Win Rate", value=f"{data.get('winrate','–')}", inline=True)

        embed.add_field(
            name="📅 Últimos 5 Jogos",
            value=text or "Não foi possível recuperar partidas.",
            inline=False
        )

        embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_FOOTER_ICON)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))