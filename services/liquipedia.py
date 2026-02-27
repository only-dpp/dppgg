import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

BASE = "https://liquipedia.net"
LOL_BASE = f"{BASE}/leagueoflegends"
API = f"{LOL_BASE}/api.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) dppgg-bot/1.0",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "Accept": "application/json,text/html,*/*;q=0.8",
    "Connection": "keep-alive",
}


def _abs(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return BASE + url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return None


async def _api_get(session: aiohttp.ClientSession, params: dict) -> dict | None:
    for attempt in range(3):
        try:
            async with session.get(API, params=params) as r:
                if r.status == 429:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                if r.status != 200:
                    return None
                return await r.json()
        except Exception:
            await asyncio.sleep(1.0 * (attempt + 1))
    return None


async def _resolve_page_title(session: aiohttp.ClientSession, team_name: str) -> str | None:
    # search via MediaWiki
    data = await _api_get(session, {
        "action": "query",
        "list": "search",
        "srsearch": team_name,
        "format": "json",
        "srlimit": 5,
    })
    if not data:
        return None

    results = (((data.get("query") or {}).get("search")) or [])
    if not results:
        return None

    # tenta pegar o melhor match (prioriza igualdade ignorando case)
    team_low = team_name.strip().lower()
    best = results[0]["title"]

    for r in results:
        title = r.get("title", "")
        if title.strip().lower() == team_low:
            best = title
            break

    return best


async def _parse_page_html(session: aiohttp.ClientSession, title: str) -> str | None:
    data = await _api_get(session, {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
    })
    if not data:
        return None

    parse = data.get("parse") or {}
    text = parse.get("text") or {}
    html = text.get("*")
    return html


def _parse_team_info(html: str, title: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    name = title
    # título costuma vir fora do HTML do parse, então usamos title mesmo

    # logo (igual seus prints: span.team-template-image-icon img)
    logo_url = None
    logo_span = soup.find("span", class_=re.compile(r"team-template-image-icon", re.I))
    if logo_span:
        img = logo_span.find("img")
        if img and img.get("src"):
            logo_url = _abs(img["src"])

    if not logo_url:
        infobox_img = soup.find("div", class_=re.compile(r"infobox-image", re.I))
        if infobox_img:
            img = infobox_img.find("img")
            if img and img.get("src"):
                logo_url = _abs(img["src"])

    # location/country (seu print: infobox-description contém Location e tem span.flag img alt="Brazil")
    country = "N/A"
    for desc in soup.find_all("div", class_=re.compile(r"infobox-description", re.I)):
        t = desc.get_text(" ", strip=True).lower()
        if "location" in t:
            flag = desc.find("span", class_=re.compile(r"\bflag\b"))
            if flag:
                img = flag.find("img", alt=True)
                if img and img.get("alt"):
                    country = img["alt"].strip()
                    break

    # descrição (primeiro parágrafo útil)
    description = "Descrição não encontrada."
    p = soup.find("p")
    if p:
        txt = p.get_text(" ", strip=True)
        if txt:
            description = txt

    # roster (seu HTML: table.table2__table)
    players = []
    roster = soup.find("table", class_=re.compile(r"\btable2__table\b"))
    if roster:
        tbody = roster.find("tbody") or roster
        rows = [tr for tr in tbody.find_all("tr") if tr.find("td")]

        # pula header se vier
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            # 0: ID (tag + flag), 1: Name, 2: Position, 3: Join Date (opcional)
            tag = "N/A"
            nationality = "N/A"

            inline_player = cols[0].find("span", class_=re.compile(r"\binline-player\b"))
            if inline_player:
                a = inline_player.find("a")
                if a and a.get_text(strip=True):
                    tag = a.get_text(strip=True)

                flag = inline_player.find("span", class_=re.compile(r"\bflag\b"))
                if flag:
                    img = flag.find("img", alt=True)
                    if img and img.get("alt"):
                        nationality = img["alt"].strip()

            real_name = cols[1].get_text(" ", strip=True) if len(cols) > 1 else "N/A"
            role = cols[2].get_text(" ", strip=True) if len(cols) > 2 else "N/A"
            join_date = cols[3].get_text(" ", strip=True) if len(cols) > 3 else "N/A"

            players.append({
                "tag": tag,
                "real_name": real_name or "N/A",
                "nationality": nationality or "N/A",
                "role": role or "N/A",
                "join_date": join_date or "N/A",
            })

    return {
        "title": title,
        "name": name,
        "url": f"{LOL_BASE}/{quote(title.replace(' ', '_'))}",
        "logo_url": logo_url,
        "country": country,
        "description": description,
        "players": players,
    }


async def get_team_full_info_async(team_name: str) -> dict | None:
    team_name = (team_name or "").strip()
    if not team_name:
        return None

    timeout = aiohttp.ClientTimeout(total=25)
    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
        title = await _resolve_page_title(session, team_name)
        if not title:
            return None

        html = await _parse_page_html(session, title)
        if not html:
            return None

        return _parse_team_info(html, title)