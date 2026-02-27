# DPP.GG — Discord Bot for League of Legends

Backend-oriented Discord bot built with Python and discord.py, designed to provide structured League of Legends data directly inside Discord.
This project focuses on clean architecture, asynchronous programming, and modular design.

---


### OVERVIEW

DPP.GG integrates external data sources to retrieve player statistics and patch information in real time.- 🛠️ Acessar as últimas notas de atualização diretamente do site oficial do LoL
The project was structured with maintainability and scalability in mind, using clear separation between command layer, services, and utilities.

### FEATURES
- /perfil → Retrieve player statistics from League of Graphs
- /patch → Fetch latest League of Legends patch notes
- /ajuda → List available commands


# ARCHITECTURE PRINCIPLES
- Modular design (Cogs pattern)
- Separation of concerns
- Asynchronous I/O
- Environment-based configuration
- Token isolation via `.env`

dppgg/
│
├── cogs/ (Command layer - Discord interactions)
├── services/ (External data integration - scraping / APIs)
├── utils/ (Shared helpers and utilities)
├── config.py (Configuration management)
├── bot.py (Application entry point)
├── requirements.txt
└── README.md
---

## 🇺🇸 In English

### 🎯 Features

- 🔍 Search for summoner profiles on [League of Graphs](https://www.leagueofgraphs.com/)
- 🛠️ Access the latest patch notes directly from the official League of Legends website
- 🏟️ Get detailed information about pro teams (players, country, logo) via [Liquipedia](https://liquipedia.net/)
- 🔗 Link League of Legends profiles to Discord users for quick access
- 📊 View stats, recent matches, KDA, champions played, and more

### 🧠 Technologies

- Python 3.10+
- [discord.py](https://discordpy.readthedocs.io/)
- `aiohttp` for asynchronous requests
- `BeautifulSoup` for web scraping
- Slash commands via `discord.app_commands`


