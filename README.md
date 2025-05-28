# 🤖 Dpp.gg - Discord Bot for League of Legends

Um bot completo para Discord focado em League of Legends, com funcionalidades úteis para jogadores e fãs do cenário competitivo.

---

## 🇧🇷 Em Português

### 🎯 Funcionalidades

- 🔍 Buscar perfis de invocadores no [League of Graphs](https://www.leagueofgraphs.com/)
- 🛠️ Acessar as últimas notas de atualização diretamente do site oficial do LoL
- 🏟️ Obter informações detalhadas de times profissionais (jogadores, país, logo) via [Liquipedia](https://liquipedia.net/)
- 🔗 Vincular perfis do LoL a usuários do Discord para consulta rápida
- 📊 Visualizar estatísticas, partidas recentes, KDA, campeões usados e mais

### 🧠 Tecnologias

- Python 3.10+
- [discord.py](https://discordpy.readthedocs.io/)
- `aiohttp` para requisições assíncronas
- `BeautifulSoup` para scraping
- Slash Commands via `discord.app_commands`

### 💻 Como rodar

```bash
git clone https://github.com/only-dpp/dpp.gg.git
cd dppgg
pip install -r requirements.txt
cp .env.example .env  # Coloque seu token do bot aqui
python bot.py
