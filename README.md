# DPP.GG  Discord Bot for League of Legends

Backend-oriented Discord bot built with Python and discord.py, designed to provide structured League of Legends data directly inside Discord.
This project focuses on clean architecture, asynchronous programming, and modular design.

---


### OVERVIEW

DPP.GG integrates external data sources to retrieve player statistics and patch information in real time.- 🛠️ Acessar as últimas notas de atualização diretamente do site oficial do LoL
The project was structured with maintainability and scalability in mind, using clear separation between command layer, services, and utilities.

### FEATURES
- `/perfil` → Retrieve player statistics from League of Graphs
- `/patch` → Fetch latest League of Legends patch notes
- `/ajuda` → List available commands


# ARCHITECTURE PRINCIPLES
- Modular design (Cogs pattern)
- Separation of concerns
- Asynchronous I/O
- Environment-based configuration
- Token isolation via `.env`

---

### TECHNOLOGIES
- `Python 3.11+`
- `discord.py 2.x`
- `aiohttp`
- `BeautifulSoup4`
- `python-dotenv`

### INSTALLATION
#### 1 - Clone the repository
```bash
pip install -r requirements.txt
python bot.py
```
#### 2 - Create virtual environment
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

#### 3 - Install dependencies
```bash
pip install -r requirements.txt
```

#### 4 - Create .env file
```bash
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
```

#### 5 - Run the bot
```bash
python bot.py
```

### SECURITY
- The Discord bot token is not stored in the repository.
- `.env` is ignored via `.gitignore.`
- Designed for safe deployment in VPS or cloud environments.

### DEVELOPMENT FOCUS
This project demonstrates:
- Backend-focused Python development
- Asynchronous programming
- Clean project structuring
- External data integration
- Maintainable command architecture

### FUTURE IMPROVEMENTS
- Caching layer to reduce repeated external requests
- Structured logging
- Rate-limit handling improvements
- Deployment automation

### AUTHOR
**Developed by Dopplin** Backend Developer focused on Python, APIs and automation systems.
