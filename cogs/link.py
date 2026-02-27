import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote
from typing import Dict

from services.leagueofgraphs import get_league_of_graphs_profile_async
from utils.formatting import rank_color
from utils.storage import load_user_history, save_user_history
from utils.constants import EMBED_FOOTER_TEXT, EMBED_FOOTER_ICON


class LinkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Carrega histórico ao subir o bot
        self.user_history: Dict[str, Dict[str, str]] = load_user_history()

    def _persist(self) -> None:
        save_user_history(self.user_history)

    @app_commands.command(
        name="vincular",
        description="🔗 Vincula sua conta do Discord a um perfil do League of Graphs."
    )
    @app_commands.describe(
        region="Região do servidor (ex: br, na, euw)",
        nickname_tag="Nome do invocador (ex: Nome#TAG)"
    )
    async def vincular(self, interaction: discord.Interaction, region: str, nickname_tag: str):
        user_id = str(interaction.user.id)
        nickname_tag = nickname_tag.replace("#", "-").strip()
        region = region.strip().lower()

        valid_regions = {"br", "na", "euw", "eune", "kr", "jp", "lan", "las", "oce", "tr", "ru"}
        if region not in valid_regions:
            await interaction.response.send_message(
                f"❌ Região inválida: `{region}`. Use uma destas: {', '.join(sorted(valid_regions))}",
                ephemeral=True
            )
            return

        self.user_history[user_id] = {"region": region, "nickname": nickname_tag}
        self._persist()

        await interaction.response.send_message(
            f"✅ Vinculado: `{nickname_tag}` na região `{region}`.",
            ephemeral=True
        )

    @app_commands.command(
        name="desvincular",
        description="❌ Remove a vinculação da sua conta do Discord."
    )
    async def desvincular(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id not in self.user_history:
            await interaction.response.send_message(
                "❌ Você não possui nenhuma conta vinculada.",
                ephemeral=True
            )
            return

        del self.user_history[user_id]
        self._persist()

        await interaction.response.send_message(
            "✅ Sua conta foi desvinculada com sucesso.",
            ephemeral=True
        )

    @app_commands.command(
        name="user",
        description="👤 Busca o perfil vinculado de um usuário do Discord."
    )
    @app_commands.describe(discord_user="Usuário do Discord")
    async def user(self, interaction: discord.Interaction, discord_user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        user_id = str(discord_user.id)
        if user_id not in self.user_history:
            await interaction.followup.send(
                f"❌ {discord_user.mention} não vinculou uma conta ainda.",
                ephemeral=True
            )
            return

        linked = self.user_history[user_id]
        region = linked["region"]
        nickname = linked["nickname"]

        data = await get_league_of_graphs_profile_async(nickname, region)
        if not data:
            await interaction.followup.send(
                f"❌ Não encontrei `{nickname}` na região `{region}`.",
                ephemeral=True
            )
            return

        color = rank_color(data.get("rank"))
        url = f"https://www.leagueofgraphs.com/summoner/{region}/{quote(data['name'])}#championsData-all"

        embed = discord.Embed(
            title=f"👤 {data['name']}",
            url=url,
            color=color,
            description=f"🔍 Perfil vinculado de {discord_user.mention}"
        )

        if data.get("profile_img"):
            embed.set_thumbnail(url=data["profile_img"])

        lm = data.get("last_matches", [])
        text = ""
        for idx, m in enumerate(lm, start=1):
            kda = m.get("kda", "KDA não disponível")
            result_emoji = "✅" if "victory" in m.get("result", "").lower() else "❌"
            text += (
                f"**Partida {idx}:**\n"
                f"👻 Campeão: `{m.get('champion','–')}`\n"
                f"{result_emoji} {m.get('result','–')}: `🗓️ {m.get('date','–')} | 🕹️ {m.get('mode','–')}`\n"
                f"⏱️ Duração: `{m.get('duration','–')}`\n"
                f"💰 KDA: `{kda}`\n\n"
            )

        embed.add_field(name="🎮 Nível", value=f"**{data.get('level','–')}**", inline=True)
        embed.add_field(
            name="🏆 Rank",
            value=f"**{data.get('rank','Unranked')}** ({data.get('lp','–')} PDL)",
            inline=True
        )
        embed.add_field(name="📊 Win Rate", value=f"{data.get('winrate','–')}", inline=True)
        embed.add_field(name="📅 Últimos jogos", value=text or "Sem dados de partidas.", inline=False)

        embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_FOOTER_ICON)

        # Como é um comando "sobre outra pessoa", eu manteria ephemeral pra evitar flood.
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LinkCog(bot))