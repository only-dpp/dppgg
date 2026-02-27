# DPP.GG  Discord Bot for League of Legends
<img width="16" height="16" alt="image" src="https://github.com/user-attachments/assets/f61f9dc7-b2d0-4bed-86d6-fc6fe14196c5" /> <img width="2400" height="2390" alt="image" src="https://github.com/user-attachments/assets/bda1e390-7a00-44dc-bf3e-f0f82e293743" />



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
git clone https://github.com/only-dpp/dppgg.git
cd dppgg
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
