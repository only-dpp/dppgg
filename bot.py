import discord
from discord.ext import commands
from discord import app_commands, Embed, interactions
from dotenv import load_dotenv
import os
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import re
import logging
import sys
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

cache = {}
user_history = {}

def rank_color(rank_name):
    if not rank_name:
        return discord.Color.default()

    rank_name = rank_name.lower()
    color_map = {
        "challenger": discord.Color.dark_red(),
        "grandmaster": discord.Color.red(),
        "master": discord.Color.dark_magenta(),
        "diamond": discord.Color.blue(),
        "platinum": discord.Color.teal(),
        "gold": discord.Color.gold(),
        "silver": discord.Color.light_grey(),
        "bronze": discord.Color.dark_gold(),
    }

    for key, color in color_map.items():
        if key in rank_name:
            return color

    return discord.Color.default()





async def get_patch_details_async(patch_url):
    """
    Busca detalhes de uma nota de patch de forma assíncrona.
    """
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Referer": "https://www.google.com/" 
}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(patch_url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

                title_tag = soup.find("h1")
                title = title_tag.text.strip() if title_tag else "Sem título"

                content_border_div = soup.find("div", class_="content-border")
                skin_img_url = None
                skin_text = None
                if content_border_div:
                    img_tag = content_border_div.find("img")
                    if img_tag:
                        skin_img_url = img_tag.get("src")
                    p_tag = content_border_div.find("p")
                    if p_tag:
                        skin_text = p_tag.text.strip()

                first_paragraph = None
                article_section = soup.find("article")
                if article_section:
                    p = article_section.find("p")
                    if p:
                        first_paragraph = p.text.strip()

                return {
                    "title": title,
                    "skin_img": skin_img_url,
                    "skin_text": skin_text,
                    "summary": first_paragraph,
                    "url": patch_url,
                }
    except aiohttp.ClientError as e:
        return None
    except Exception as e:
        return None


async def get_latest_patch_note_with_skins_async():
    """
    Busca a última nota de patch com skins de forma assíncrona.
    """
    url = "https://www.leagueoflegends.com/pt-br/news/tags/patch-notes/"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Referer": "https://www.google.com/" 
}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

                cards = soup.find_all("a", {"data-testid": "articlefeaturedcard-component"})
                for card in cards:
                    category = card.find("div", {"data-testid": "card-category"})
                    if category and "Atualizações do jogo" in category.text:
                        href = card["href"]
                        patch_url = f"https://www.leagueoflegends.com{href}"

                        patch_details = await get_patch_details_async(patch_url)
                        if not patch_details:
                            continue

                        description_div = card.find("div", {"data-testid": "card-description"})
                        description = description_div.text.strip() if description_div else patch_details.get("summary", "Sem descrição")

                        return {
                            "title": patch_details["title"],
                            "description": description,
                            "url": patch_details["url"],
                            "skin_img": patch_details["skin_img"],
                            "skin_text": patch_details["skin_text"],
                        }
        return None
    except aiohttp.ClientError as e:
        return None
    except Exception as e:
        return None

def get_next_match(soup, team_acronym):
    """
    Busca a próxima partida do time especificado.
    Retorna um dicionário com adversário e tipo de jogo.
    """
    next_match = None
    match_rows = soup.find_all("tr")  

    for row in match_rows:
        left_team = row.find("td", class_="team-left")
        versus = row.find("td", class_="versus")
        right_team = row.find("td", class_="team-right")

        if not left_team or not versus or not right_team:
            continue

        left_text = left_team.get_text(strip=True)
        right_text = right_team.get_text(strip=True)

        if team_acronym in left_text:
            opponent = right_text
        elif team_acronym in right_text:
            opponent = left_text
        else:
            continue

        format_tag = versus.find("abbr")
        match_format = format_tag.get_text(strip=True) if format_tag else "Desconhecido"

        next_match = {
            "adversario": opponent,
            "formato": match_format
        }
        break

    return next_match

async def get_team_full_info_async(team_name):
    """
    Busca informações detalhadas de um time (descrição, país, logo, e jogadores) na Liquipedia.
    """
    base_url = "https://liquipedia.net/leagueoflegends/"
    team_formatted_name = team_name.replace(" ", "_")
    url = f"{base_url}{quote(team_formatted_name)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Referer": "https://www.google.com/"
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 404:
                    
                    search_url = f"https://liquipedia.net/leagueoflegends/index.php?search={quote(team_name)}"
                    async with session.get(search_url) as search_response:
                        if search_response.status != 200:
                            
                            return None
                        search_text = await search_response.text()
                        search_soup = BeautifulSoup(search_text, 'html.parser')
                        first_result_div = search_soup.find("div", class_="mw-search-result-heading")
                        if first_result_div:
                            link = first_result_div.find("a")
                            if link and "/leagueoflegends/" in link['href']:
                                full_link = "https://liquipedia.net" + link['href']
                                async with session.get(full_link) as final_response:
                                    if final_response.status == 200:
                                        text = await final_response.text()
                                    else:
                                        return None
                            else:
                                return None
                        else:
                            return None
                elif response.status != 200:
                    return None
                else:
                    text = await response.text()
                
                soup = BeautifulSoup(text, 'html.parser')
                
                next_match = get_next_match(soup, team_name)
                if next_match:
                    team_info("proximas partidas", next_match)

                team_data = {
                    "name": team_name,
                    "description": "Descrição não encontrada.",
                    "country": "País não encontrado.",
                    "logo_url": None,
                    "url": url,
                    "next_match": next_match or "Próxima partida não encontrada."
                }

                team_description_p = None
                for p_tag in soup.find_all("p"):
                    if p_tag.find("b") and team_name.lower() in p_tag.text.lower() and "is a" in p_tag.text.lower():
                        team_description_p = p_tag
                        break
                
                if team_description_p:
                    team_data["description"] = team_description_p.get_text(separator=' ', strip=True)
                    country_link = team_description_p.find("a", title=lambda x: x and "Category:" in x)
                    if country_link:
                        team_data["country"] = country_link.get("title").replace("Category:", "").strip() # type: ignore

                logo_div = soup.find("div", class_="team-template-logo") or soup.find("div", class_="infobox-image")
                if logo_div:
                    img_tag = logo_div.find("img")
                    if img_tag and img_tag.get("src"):
                        if img_tag['src'].startswith('//'):
                            team_data["logo_url"] = "https:" + img_tag['src']
                        elif img_tag['src'].startswith('/'):
                            team_data["logo_url"] = "https://liquipedia.net" + img_tag['src']
                        else:
                            team_data["logo_url"] = img_tag['src']
                
                roster_table = soup.find("table", class_=lambda x: x and ("wikitable" in x and "roster-card" in x or "players-team-active" in x))
                
                if roster_table:
                    rows = roster_table.find("tbody").find_all("tr") if roster_table.find("tbody") else roster_table.find_all("tr")

                    if rows and rows[0].find('th'):
                        rows = rows[1:]

                    for row in rows:
                        player_span = row.find("span", class_="inline-player")
                        if player_span:
                            player_info = {
                                "tag": "N/A",
                                "real_name": "N/A",
                                "nationality": "N/A",
                                "role": "N/A", 
                                "join_date": "N/A",
                                "country_flag_url": None
                            }

                            player_tag_a = player_span.find("a")
                            if player_tag_a:
                                player_info["tag"] = player_tag_a.text.strip()
                            
                            flag_span = player_span.find("span", class_="flag")
                            if flag_span:
                                flag_img = flag_span.find("img")
                                if flag_img:
                                    if flag_img.get("alt"):
                                        player_info["nationality"] = flag_img.get("alt").strip()
                                    if flag_img.get("src"):
                                        if flag_img['src'].startswith('//'):
                                            player_info["country_flag_url"] = "https:" + flag_img['src']
                                        elif flag_img['src'].startswith('/'):
                                            player_info["country_flag_url"] = "https://liquipedia.net" + flag_img['src']
                                        else:
                                            player_info["country_flag_url"] = flag_img['src']

                            cols = row.find_all(['td', 'th'])
                            
                            if len(cols) > 2:
                                real_name_div = cols[2].find("div", class_="LargeStuff")
                                if real_name_div:
                                    player_info["real_name"] = real_name_div.text.strip()
                                else: 
                                    mobile_name_div = cols[2].find("div", class_="MobileStuff")
                                    if mobile_name_div:
                                        match = re.search(r'\((.*?)\)', mobile_name_div.text.strip())
                                        if match:
                                            player_info["real_name"] = match.group(1).strip()
                                        else:
                                            player_info["real_name"] = mobile_name_div.text.strip()

                            if len(cols) > 3:
                                position_td = cols[3]
                                position_text_parts = []
                                for elem in position_td.contents:
                                    if isinstance(elem, str):
                                        position_text_parts.append(elem.strip())
                                    elif elem.name != "div":
                                        position_text_parts.append(elem.get_text(strip=True))
                                player_info["role"] = " ".join(part for part in position_text_parts if part).strip()

                            if len(cols) > 4:
                                join_date_i = cols[4].find("i")
                                if join_date_i:
                                    join_date_text = re.sub(r'\s*\[.*?\]', '', join_date_i.text.strip())
                                    player_info["join_date"] = join_date_text

                            team_data["players"].append(player_info)
                
                return team_data

    except aiohttp.ClientError as e:
        return None
    except Exception as e:
        return None

async def get_league_of_graphs_profile_async(summoner_name, region="br"):
    """
    Busca o perfil do invocador no League of Graphs de forma assíncrona.
    """
    summoner_name_encoded = quote(summoner_name.replace(" ", "%20"))
    url = f"https://www.leagueofgraphs.com/summoner/{region}/{summoner_name_encoded}#championsData-all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                txt_div = soup.find("div", class_="txt")
                name = None
                if txt_div:
                    name_tag = txt_div.find("h2")
                    if name_tag:
                        name = name_tag.text.strip()
                name = name or "Nome não encontrado"

                level_div = txt_div.find("div", class_="bannerSubtitle") if txt_div else None
                level = None
                if level_div:
                    level_text = level_div.text.strip()
                    match = re.search(r"Level (\d+)", level_text)
                    if match:
                        level = match.group(1)
                level = level or "Nível não encontrado"

                rank_div = soup.find("div", class_="leagueTier")
                rank = rank_div.text.strip() if rank_div else "Rank não encontrado"

                lp_div = soup.find("div", class_="league-points")
                lp = None
                if lp_div:
                    lp_span = lp_div.find("span", class_="leaguePoints")
                    if lp_span:
                        lp = lp_span.text.strip()
                lp = lp or "LP não encontrado"

                wins_losses_div = soup.find("div", class_="winslosses")
                wins = 0
                losses = 0
                winrate = "Win Rate não encontrado"
                if wins_losses_div:
                    wins_span = wins_losses_div.find("span", class_="winsNumber")
                    losses_span = wins_losses_div.find("span", class_="lossesNumber")
                    if wins_span and losses_span:
                        wins = int(wins_span.text.strip())
                        losses = int(losses_span.text.strip())
                        total_games = wins + losses
                        winrate = f"{(wins / total_games) * 100:.2f}%" if total_games > 0 else "0%"

                profile_img_div = soup.find("div", class_="img")
                profile_img = None
                if profile_img_div:
                    img_tag = profile_img_div.find("img")
                    if img_tag and img_tag.get("src"):
                        profile_img = "https:" + img_tag["src"]

                rank_img_div = soup.find("div", class_="best-league__inner img-align-block")
                rank_img = None
                if rank_img_div:
                    img_tag = rank_img_div.find("img")
                    if img_tag and img_tag.get("src"):
                        rank_img = "https:" + img_tag["src"]
                
                last_matches = []
                cells = soup.select("td.resultCellLight.text-center")[:5]
                for cell in cells:
                    vd = cell.select_one("div.victoryDefeatText")
                    result = vd.text.strip() if vd else "–"
                    mode = cell.select_one("div.gameMode")
                    mode = mode['tooltip'].strip() if mode and mode.has_attr("tooltip") else mode.text.strip() if mode else "–"
                    date = cell.select_one("div.gameDate")
                    date = date.text.strip() if date else "–"
                    duration = cell.select_one("div.gameDuration")
                    duration = duration.text.strip() if duration else "–"
                    lp_change_img = cell.select_one("div.lpChange img")
                    lp_change = lp_change_img['alt'].strip() if lp_change_img else "–"

                    kda_link = cell.select_one("a.display-block")
                    if kda_link and kda_link.get("href"):
                        match_url = f"https://www.leagueofgraphs.com{kda_link['href']}"
                        participant_id = kda_link['href'].split("-")[-1]  
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(match_url, headers=headers) as match_response:
                                    if match_response.status == 200:
                                        match_text = await match_response.text()
                                        match_soup = BeautifulSoup(match_text, 'html.parser')

                                        player_rows = match_soup.select("tr.playerRow")
                                        participant_div = None

                                        for row in player_rows:
                                            td_elements = row.select("td")
                                            for td in td_elements:
                                                name_div = td.select_one("div.name")
                                                if name_div:
                                                    player_name = name_div.text.strip()
                                                    if summoner_name.replace("-", "#").lower() == player_name.lower():
                                                        participant_div = td  
                                                        break
                                            if participant_div:
                                                break

                                        if participant_div:
                                            kda_div = participant_div.select_one("div.show-for-small-down")
                                            if kda_div:
                                                kills = kda_div.select_one("span.kills").text.strip() if kda_div.select_one("span.kills") else "0"
                                                deaths = kda_div.select_one("span.deaths").text.strip() if kda_div.select_one("span.deaths") else "0"
                                                assists = kda_div.select_one("span.assists").text.strip() if kda_div.select_one("span.assists") else "0"
                                                kda = f"{kills}/{deaths}/{assists}"
                                            else:
                                                kda = "KDA não disponível"

                                            champion_div = participant_div.select_one("div.relative img")
                                            if champion_div and champion_div.get("alt"):
                                                champion = champion_div["alt"].strip()
                                            else:
                                                champion = "Campeão não disponível"
                                        else:
                                            kda = "KDA não disponível"
                                            champion = "Campeão não disponível"
                                    else:
                                        kda = "KDA não disponível"
                                        champion = "Campeão não disponível"
                        except Exception:
                            kda = "KDA não disponível"
                            champion = "Campeão não disponível"
                    else:
                        kda = "KDA não disponível"

                    last_matches.append({
                        "result": result,
                        "mode": mode,
                        "date": date,
                        "duration": duration,
                        "lp_change": lp_change,
                        "kda": kda,
                        "champion": champion if 'champion' in locals() else "Campeão não disponível"
                    })
                

                return {
                    "name": name,
                    "level": level,
                    "rank": rank,
                    "lp": lp,
                    "winrate": winrate,
                    "profile_img": profile_img,
                    "rank_img": rank_img,
                    "last_matches": last_matches,
                    "url": url,
                }
    except aiohttp.ClientError:
        return None
    except Exception:
        return None


@tree.command(name="perfil", description="🔍 Buscar perfil do LoL no OP.GG e League of Graphs")
@app_commands.describe(region="Região do servidor (ex: br, na, euw)", nickname_tag="Nome do invocador")
@commands.cooldown(1, 10, commands.BucketType.user)
async def perfil_command(interaction: discord.Interaction, region: str, nickname_tag: str):
    await interaction.response.defer()

    nickname_tag = nickname_tag.replace("#", "-")
    
    league_of_graphs_data = await get_league_of_graphs_profile_async(nickname_tag, region)
    
    if not league_of_graphs_data:
        await interaction.followup.send(f"❌ Invocador '{nickname_tag}' não encontrado ou erro ao acessar o League of Graphs. Tente novamente mais tarde.")
        return

    uid = str(interaction.user.id)
    user_history.setdefault(uid, []).append(nickname_tag)

    color = rank_color(league_of_graphs_data['rank'])
    url = f"https://www.leagueofgraphs.com/summoner/{region}/{quote(league_of_graphs_data['name'])}#championsData-all"

    embed = discord.Embed(
        title=f"👤 {league_of_graphs_data['name']}",
        url=url,
        color=color,
        description=f"🔍 Estatísticas de **{league_of_graphs_data['name']}** no servidor."
    )

    if league_of_graphs_data['profile_img']:
        embed.set_thumbnail(url=league_of_graphs_data['profile_img'])

    lm = league_of_graphs_data["last_matches"]
    if lm:
        text = ""
        for idx, m in enumerate(lm, start=1):
            lp_txt = m['lp_change'] if m['lp_change'] != "–" else "Nenhuma mudança"
            kda = m.get('kda', "KDA não disponível")
            result_emoji = "✅" if "victory" in m['result'].lower() else "❌"  
            text += (
                f"**Partida {idx}:**\n"
                f"👻Campeão Usado: `{m['champion']}`\n"
                f"{result_emoji} {m['result']}: `🗓️ {m['date']} | 🕹️ {m['mode']}`\n"
                f"⏱️ Duração: `{m['duration']}` |\n"
                f"💰 KDA: `{kda}`\n"
            )

    embed.add_field(name="🎮 Nível", value=f"**{league_of_graphs_data['level']}**", inline=True)
    embed.add_field(
        name="🏆 Rank",
        value=f"**{league_of_graphs_data.get('rank', 'Unranked')}** ({league_of_graphs_data.get('lp', 'Unranked')} PDL)",  
        inline=True
    )
    embed.add_field(name="📊 Win Rate", value=f"{league_of_graphs_data['winrate']}", inline=True)
    embed.add_field(name="📅 Últimos 3 Jogos", value=text or "Não foi possível recuperar partidas.", inline=False)

    embed.set_footer(text="🔹 Desenvolvido com ❤️ por Dopplin_", icon_url="https://i.imgur.com/VIRt7Cj.png")

    await interaction.followup.send(embed=embed)

@tree.command(name="ajuda", description="📘 Lista de comandos disponíveis")
@commands.cooldown(1, 10, commands.BucketType.user)
async def ajuda_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Comandos do Dpp.gg",
        description="Aqui estão os comandos que você pode usar:",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="/perfil",
        value="🔍 Busca o perfil de um invocador.\nExemplo: `/perfil region:br nickname:Hide on bush#KR1`",
        inline=False
    )

    embed.add_field(
        name="/ajuda",
        value="📘 Exibe esta mensagem de ajuda.",
        inline=False
    )

    embed.add_field(
        name="/patch",
        value="🛠️ Veja as últimas notas de atualização do LoL.",
        inline=False
    )

    embed.add_field(
        name="/time",
        value="🏟️ Mostra informações detalhadas de um time profissional de LoL (descrição, país, jogadores).",
        inline=False
    )

    embed.set_footer(text="Feito com ❤️ por Dopplin_")
    await interaction.response.send_message(embed=embed)

@tree.command(name="patch", description="🛠️ Veja as últimas notas de atualização do LoL")
@commands.cooldown(1, 10, commands.BucketType.user)
async def patch_notes_command(interaction: discord.Interaction):
    await interaction.response.defer()

    patch = await get_latest_patch_note_with_skins_async()
    if not patch:
        await interaction.followup.send("❌ Não consegui acessar as notas de atualização no momento. Tente novamente mais tarde.")
        return

    embed = discord.Embed(
        title=f"📢 {patch['title']}",
        description=f"{patch['description']}\n\n🔗 [Leia a nota completa aqui]({patch['url']})",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="https://images.contentstack.io/v3/assets/blt370612131b6e0756/blt73db43209fef9de0/5f4e5092e25f1d39a7f36a11/LOL_ICON.png")
    embed.set_footer(text="🔹 Patch oficial do League of Legends | Dpp.gg")

    if patch['skin_img']:
        embed.add_field(name="🆕 Novas Skins / Atualização", value=patch['skin_text'] or "Informação não disponível", inline=False)
        embed.set_image(url=patch['skin_img'])

    await interaction.followup.send(embed=embed)

@tree.command(name="time", description="🏟️ Mostra informações detalhadas de um time de LoL profissional.")
@commands.cooldown(1, 10, commands.BucketType.user)
@app_commands.describe(team_name="Nome completo do time (ex: LOUD, T1, Gen.G)")
async def team_full_info_command(interaction: discord.Interaction, team_name: str):
    await interaction.response.defer()

    team_data = await get_team_full_info_async(team_name)

    if not team_data or not team_data["players"]:
        await interaction.followup.send(f"❌ Não foi possível encontrar informações detalhadas para o time '{team_name}'. Verifique o nome (ex: pain gaming = paiN Gaming) ou tente novamente mais tarde.")
        return
    
    embed = discord.Embed(
        title=f"🏟️ Elenco de {team_data['name']}",  
        url=team_data['url'],
        color=discord.Color.dark_blue(),
        description=f"**Organização:** {team_data['description']}"
    )
    
    if team_data['logo_url']:
        embed.set_thumbnail(url=team_data['logo_url'])

    embed.add_field(name="🌍 País de Origem", value=f"**{team_data['country']}**", inline=True)
    embed.add_field(name="🔗 Página na Liquipedia", value=f"[Acessar]({team_data['url']})", inline=False)

    players_text = ""
    for player in team_data["players"]:
        players_text += (
            f"**{player.get('tag', 'N/A')}** ({player.get('role', 'N/A')})\n"
            f"  • Nome Real: {player.get('real_name', 'N/A')}\n"
            f"  • Nacionalidade: {player.get('nationality', 'N/A')}\n"
            f"  • Data de Entrada: {player.get('join_date', 'N/A')}\n\n"
        )
    
    if players_text:
        chunks = [players_text[i:i+1000] for i in range(0, len(players_text), 1000)]
        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Jogadores Ativos{' (continuação)' if i > 0 else ''}", value=chunk, inline=False)
    else:
        embed.add_field(name="Jogadores Ativos", value="Nenhum jogador encontrado ou a estrutura da página mudou.", inline=False)

    embed.set_footer(text="Fonte: Liquipedia League of Legends | Dpp.gg")
    await interaction.followup.send(embed=embed)

logging.basicConfig(
    filename="bot_usage.log",  
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  
    datefmt="%Y-%m-%d %H:%M:%S"  
)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.command:  
        guild_name = interaction.guild.name if interaction.guild else "DM"
        channel_name = interaction.channel.name if interaction.guild else "DM"  
        user = interaction.user 
        command = interaction.command.name  

        logging.info(f"Comando '/{command}' usado por {user} no servidor '{guild_name}' (canal: {channel_name})")

        print(f"[LOG] Comando '/{command}' usado por {user} no servidor '{guild_name}' (canal: {channel_name})")
        logging.basicConfig(
    filename='bot_usage.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8',  
)
async def on_ready():
    await tree.sync()
bot.run(DISCORD_TOKEN)
