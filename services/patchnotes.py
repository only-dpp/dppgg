import aiohttp
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}


async def get_patch_details_async(patch_url: str, session: aiohttp.ClientSession) -> dict | None:
    try:
        async with session.get(patch_url, headers=HEADERS) as response:
            if response.status != 200:
                return None
            text = await response.text()

        soup = BeautifulSoup(text, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Sem título"

        content_border_div = soup.find("div", class_="content-border")
        skin_img_url, skin_text = None, None
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
    except Exception:
        return None


async def get_latest_patch_note_with_skins_async() -> dict | None:
    url = "https://www.leagueoflegends.com/pt-br/news/tags/patch-notes/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    return None
                text = await response.text()

            soup = BeautifulSoup(text, "html.parser")
            cards = soup.find_all("a", {"data-testid": "articlefeaturedcard-component"})

            for card in cards:
                category = card.find("div", {"data-testid": "card-category"})
                if category and "Atualizações do jogo" in category.text:
                    href = card.get("href")
                    if not href:
                        continue

                    patch_url = f"https://www.leagueoflegends.com{href}"

                    patch_details = await get_patch_details_async(patch_url, session)
                    if not patch_details:
                        continue

                    description_div = card.find("div", {"data-testid": "card-description"})
                    description = (
                        description_div.text.strip()
                        if description_div else (patch_details.get("summary") or "Sem descrição")
                    )

                    return {
                        "title": patch_details["title"],
                        "description": description,
                        "url": patch_details["url"],
                        "skin_img": patch_details["skin_img"],
                        "skin_text": patch_details["skin_text"],
                    }

        return None
    except Exception:
        return None