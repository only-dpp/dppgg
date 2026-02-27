import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import asyncio

TIERS = r"(Iron|Bronze|Silver|Gold|Platinum|Emerald|Diamond|Master|Grandmaster|Challenger)"

def _display_name_from_slug(slug: str) -> str:
    if "-" in slug:
        name, tag = slug.rsplit("-", 1)
        return f"{name}#{tag}"
    return slug

def _extract_profile_img(soup: BeautifulSoup) -> str | None:
    # prioridade 1: ícone do invocador no banner (src contém "summonerIcons")
    img = soup.find("img", src=re.compile(r"summonerIcons", re.I))
    if img and img.get("src"):
        src = img["src"].strip()
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("/"):
            return "https://www.leagueofgraphs.com" + src
        if src.startswith("http://") or src.startswith("https://"):
            return src
        return None

    # prioridade 2: og:image (fallback)
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        c = og["content"].strip()
        if c.startswith("//"):
            return "https:" + c
        if c.startswith("/"):
            return "https://www.leagueofgraphs.com" + c
        if c.startswith("http://") or c.startswith("https://"):
            return c

    return None

def _abs_url(u: str | None) -> str | None:
    if not u:
        return None
    u = u.strip()
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return "https://www.leagueofgraphs.com" + u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return None


def _extract_rank_info(soup: BeautifulSoup) -> tuple[str, str, str | None]:
    """
    Retorna (rank_text, lp_text, rank_icon_url)
    Ex: ("Silver IV", "55", "https://lolg-cdn....png")
    """
    rank = "Unranked"
    lp = "–"
    rank_img = None

    box = soup.find("div", class_=re.compile(r"mainRankingDescriptionText", re.I))
    if not box:
        return rank, lp, rank_img

    # rank text
    tier_div = box.find("div", class_=re.compile(r"leagueTier", re.I))
    if tier_div:
        rank = tier_div.get_text(" ", strip=True) or rank

    # lp text (às vezes vem "55 LP" ou só "55")
    lp_div = box.find("div", class_=re.compile(r"league-points", re.I))
    if lp_div:
        lp_text = lp_div.get_text(" ", strip=True)
        m = re.search(r"(\d+)", lp_text or "")
        if m:
            lp = m.group(1)

    # rank image icon
    img = box.find("img")
    if img and img.get("src"):
        rank_img = _abs_url(img["src"])

    return rank, lp, rank_img

def _extract_level(text: str) -> str:
    m = re.search(r"\bLevel\s+(\d+)\b", text)
    return m.group(1) if m else "Nível não encontrado"

def _extract_winrate(text: str) -> tuple[int, int, str]:
    wins = losses = 0
    winrate = "Unranked"

    m = re.search(r"\bWins:\s*(\d+)\s+Losses:\s*(\d+)\b", text)
    if m:
        wins = int(m.group(1))
        losses = int(m.group(2))
        total = wins + losses
        winrate = f"{(wins / total) * 100:.2f}%" if total else "0.00%"

    return wins, losses, winrate

def _extract_last_matches(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai os últimos jogos da tabela:
    table.recentGamesTable
    """
    last_matches: list[dict] = []

    table = soup.find("table", class_=re.compile(r"\brecentGamesTable\b", re.I))
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    # pega só linhas que tenham td (ignora headers/filters)
    rows = [tr for tr in tbody.find_all("tr") if tr.find("td")]

    for row in rows[:5]:
        # campeão
        champ = "–"
        champ_td = row.find("td", class_=re.compile(r"\bchampionCell", re.I))
        if champ_td:
            img = champ_td.find("img", alt=True)
            if img and img.get("alt"):
                champ = img["alt"].strip()
            else:
                champ = champ_td.get_text(" ", strip=True) or champ

        # resultado + modo + data + duração + LP (tudo costuma estar dentro do resultCell)
        result = "Unknown"
        date = "–"
        mode = "–"
        duration = "–"
        lp_delta = ""

        result_td = row.find("td", class_=re.compile(r"\bresultCell", re.I))
        if result_td:
            txt = result_td.get_text(" ", strip=True)

            low = txt.lower()
            if "victory" in low or "vitória" in low:
                result = "Victory"
            elif "defeat" in low or "derrota" in low:
                result = "Defeat"
            elif "remake" in low:
                result = "Remake"

            # tenta extrair duração "34min 35s" ou "17min 10s"
            m_dur = re.search(r"\b(\d+)\s*min\b(?:\s*(\d+)\s*s\b)?", txt)
            if m_dur:
                # reconstrói
                mins = m_dur.group(1)
                secs = m_dur.group(2)
                duration = f"{mins}min" + (f" {secs}s" if secs else "")

            # "38 days ago" / "2 hours ago"
            m_date = re.search(r"\b(\d+)\s+(day|days|hour|hours|minute|minutes)\s+ago\b", txt, flags=re.I)
            if m_date:
                date = f"{m_date.group(1)} {m_date.group(2)} ago"

            # modo (Soloqueue, Flex, ARAM etc). Se achar “Soloqueue” usa isso.
            for candidate in ["Soloqueue", "Flex", "ARAM", "Normal", "Ranked", "Clash"]:
                if re.search(rf"\b{re.escape(candidate)}\b", txt, flags=re.I):
                    mode = candidate
                    break

            # delta LP tipo "+23 LP" ou "-17 LP"
            m_lp = re.search(r"([+-]\d+)\s*LP\b", txt)
            if m_lp:
                lp_delta = m_lp.group(1) + " LP"

        # KDA (coluna específica)
        kda = "KDA não disponível"
        kda_td = row.find("td", class_=re.compile(r"\bkdaColumn\b", re.I))
        if kda_td:
            # geralmente vem "3/6/8"
            kda_txt = kda_td.get_text(" ", strip=True)
            mkda = re.search(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", kda_txt)
            if mkda:
                kda = f"{mkda.group(1)}/{mkda.group(2)}/{mkda.group(3)}"
            else:
                # fallback
                if kda_txt:
                    kda = kda_txt

        last_matches.append({
            "champion": champ,
            "result": result,
            "date": date,
            "mode": mode,
            "duration": (duration + (f" | {lp_delta}" if lp_delta else "")).strip(),
            "kda": kda,
        })

    return last_matches

async def get_league_of_graphs_profile_async(summoner_slug: str, region: str = "br"):
    region = (region or "br").strip().lower()
    summoner_slug = (summoner_slug or "").strip()

    summoner_encoded = quote(summoner_slug, safe="")
    url = f"https://www.leagueofgraphs.com/summoner/{region}/{summoner_encoded}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    for attempt in range(3):
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 429:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    if response.status != 200:
                        return None
                    html = await response.text()
        except Exception:
            await asyncio.sleep(1.0 * (attempt + 1))
            continue

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)

        # valida se é uma página real de summoner
        if "Personal Ratings" not in text and "Wins:" not in text:
            return None

        display_name = _display_name_from_slug(summoner_slug)

        level = _extract_level(text)
        rank, lp, rank_img = _extract_rank_info(soup)
        wins, losses, winrate = _extract_winrate(text)

        profile_img = _extract_profile_img(soup)
        last_matches = _extract_last_matches(soup)

        return {
            "name": display_name,
            "url_name": summoner_slug,
            "region": region,
            "level": level,
            "rank": rank,
            "lp": lp,
            "wins": wins,
            "losses": losses,
            "winrate": winrate,
            "profile_img": profile_img,
            "rank_img": rank_img,
            "last_matches": last_matches,
        }

    return None