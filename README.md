# 🧠 Neural Nexus - League of Legends ML Coaching Platform

**Version:** 2.0.0  
**Current Status:** 🟢 Collector Service Operational | 🟡 Enrichment Service In Progress  
**Last Updated:** October 29, 2025

---

## 📊 Project Status

### ✅ Completed Components

- **Core Infrastructure**
  - PostgreSQL database with full schema (6 tables, optimized indexes)
  - Environment configuration system (.env with dual API key management)
  - Connection pooling with psycopg3
  - Project structure and Python packages

- **Data Collection System**
  - Multi-threaded regional collectors (NA1, EUW1, KR)
  - Riot API client with per-region rate limiting (100 req/2min)
  - Smart match scanner with deduplication
  - Queue manager with tier-based priorities
  - Player discovery from match participants
  - Gzipped JSON storage (~63KB per match)

- **Database**
  - 3,500+ players tracked (Challenger, Grandmaster, Master, discovered players)
  - 300+ matches collected
  - 18+ MB compressed data
  - Enrichment queue with 66+ players pending

### 🔄 In Progress

- **Enrichment Service**
  - Player rank updates using RIOT_API_KEY_ENRICHMENT
  - Summoner name/Riot ID updates
  - Processing enrichment queue

### 📋 Planned

- Web Dashboard (FastAPI + React)
- Statistics and monitoring endpoints
- ML features (Draft Prophet, Build Optimizer, Macro Advisor)
- Advanced analytics and visualizations

---

## 🚀 Quick Start Guide

### Prerequisites

You should have these installed:
- **Python 3.12.7** (3.12.x required - 3.13 not compatible with some packages)
- **PostgreSQL 18** (password: `admin`)
- **VSCode** (recommended IDE)
- **Git** for version control

### Initial Setup (First Time Only)

```bash
# Clone repository
git clone https://github.com/hl0659/neural-nexus.git
cd neural-nexus

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
Copy-Item .env.example .env
# Edit .env with your API keys and settings

# Initialize database
python scripts/init_db.py

# Seed initial players
python scripts/seed_players.py
```

### Daily Startup (Every Session)

```bash
# Navigate to project
cd F:\Projects\neural-nexus

# Activate virtual environment
.\venv\Scripts\activate

# Set Python path (REQUIRED for imports to work)
$env:PYTHONPATH="F:\Projects\neural-nexus"

# Update API keys in .env if expired (they expire every 24 hours)
# Get new keys from: https://developer.riotgames.com/

# Run the collector
python -m services.collector.main
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:admin@localhost:5432/neural_nexus

# Riot API Keys (refresh daily at developer.riotgames.com)
RIOT_API_KEY_COLLECTION=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
RIOT_API_KEY_ENRICHMENT=RGAPI-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy

# Collection Settings
REGIONS=na1,euw1,kr
MIN_TIER=DIAMOND
COLLECTION_BATCH_SIZE=100

# Storage Paths
DATA_PATH=F:/neural_nexus_data
LOG_PATH=F:/neural_nexus_data/logs

# API Server (not yet implemented)
API_HOST=0.0.0.0
API_PORT=8000

# Rate Limiting (per region, per 2 minutes)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=120
```

### Key Configuration Notes

- **Two API Keys Required:** One for match collection, one for player enrichment
- **Keys Expire Daily:** Must be refreshed every 24 hours from Riot Developer Portal
- **Data Path:** All match/timeline JSONs stored on F: drive to save space
- **Rate Limits:** 100 requests per 2 minutes PER REGION (300 total/2min with 3 regions)

---

## 🗃️ Database Schema

### Core Tables

| Table | Purpose | Row Count (Current) |
|-------|---------|---------------------|
| `players` | Player tracking with tier/rank | 3,500+ |
| `matches` | Match metadata and file paths | 300+ |
| `match_participants` | Player performance in matches | 3,000+ |
| `match_bans` | Champion bans with pick order | 600+ |
| `collection_queue` | Automatic (managed by queue_manager) | N/A |
| `enrichment_queue` | Players needing rank updates | 66+ |

### Key Design Decisions

- **PUUID as Primary Key:** Riot's universal player identifier
- **Foreign Key Constraints:** Ensures data integrity
- **Indexed Queries:** Optimized for tier/region/time lookups
- **Gzipped Storage:** Match JSONs stored externally, paths in DB
- **Queue System:** Separate queues for collection vs enrichment

---

## 🏗️ Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Riot API    │────▶│  Collectors  │────▶│  PostgreSQL  │
│              │     │  (Regional)  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                      ▲
       │                    ▼                      │
       │            ┌──────────────┐              │
       │            │ Gzipped JSON │              │
       │            │   Storage    │              │
       │            └──────────────┘              │
       │                                          │
       │            ┌──────────────┐              │
       └───────────▶│  Enrichment  │──────────────┘
                    │   Service    │
                    └──────────────┘
```

### Data Flow

1. **Collection Cycle:**
   - Queue Manager selects next player due for check
   - Match Scanner finds new matches (stops at last known)
   - API Client fetches match + timeline data
   - Storage Handler saves compressed JSON to F: drive
   - Database indexes match metadata
   - Player Discovery extracts participants
   - New players added to enrichment queue

2. **Enrichment Cycle (In Progress):**
   - Get next player from enrichment queue
   - Fetch current rank from Riot API
   - Update player tier/rank/LP
   - Fetch Riot ID (gameName#tagLine)
   - Mark as complete

---

## 📁 Project Structure

```
neural-nexus/
├── services/
│   ├── collector/
│   │   ├── main.py                    # ✅ Multi-threaded orchestrator
│   │   ├── queue_manager.py           # ✅ Tier-based player scheduling
│   │   ├── match_scanner.py           # ✅ Find new matches efficiently
│   │   ├── player_discovery.py        # ✅ Extract players from matches
│   │   ├── api/
│   │   │   ├── riot_client.py         # ✅ API client with retries
│   │   │   └── rate_limiter.py        # ✅ Per-region rate limiting
│   │   └── storage/
│   │       └── json_handler.py        # ✅ Gzip compression & storage
│   │
│   ├── enrichment/                    # 🔄 IN PROGRESS
│   │   └── main.py                    # Next: Build enrichment service
│   │
│   └── api/                           # 📋 PLANNED
│       └── main.py                    # Future: FastAPI endpoints
│
├── shared/
│   ├── config/
│   │   └── settings.py                # ✅ Environment configuration
│   └── database/
│       ├── connection.py              # ✅ Connection pooling
│       ├── player_ops.py              # ✅ Player CRUD operations
│       └── match_ops.py               # ✅ Match CRUD operations
│
├── database/
│   ├── schema.sql                     # ✅ Complete database schema
│   └── migrations/                    # Future: Alembic migrations
│
├── scripts/
│   ├── seed_players.py                # ✅ Seed Challenger/GM players
│   ├── test_db.py                     # ✅ Test database connection
│   ├── check_data.py                  # ✅ View collection statistics
│   ├── check_enrichment_queue.py      # ✅ View enrichment queue
│   └── test_riot_api.py               # ✅ Test API endpoints
│
├── data/ (on F: drive)
│   └── F:/neural_nexus_data/
│       ├── matches/                   # ✅ Match JSONs by region/date
│       ├── timelines/                 # ✅ Timeline JSONs by region/date
│       └── logs/                      # Future: Application logs
│
├── .env                               # ✅ Your local configuration
├── .env.example                       # ✅ Configuration template
├── requirements.txt                   # ✅ Python dependencies
└── README.md                          # ✅ This file
```

---

## 🛠️ Useful Commands

### Data Collection

```bash
# Start the collector (runs until Ctrl+C)
python -m services.collector.main

# Check what's been collected
python scripts/check_data.py

# Check enrichment queue status
python scripts/check_enrichment_queue.py

# Re-seed players (if you want fresh data)
python scripts/seed_players.py
```

### Database

```bash
# Test database connection
python scripts/test_db.py

# Connect to PostgreSQL directly
psql -U postgres -d neural_nexus

# Useful SQL queries:
SELECT COUNT(*) FROM players;
SELECT COUNT(*) FROM matches;
SELECT region, tier, COUNT(*) FROM players GROUP BY region, tier;
```

### Development

```bash
# Test API endpoints
python scripts/test_riot_api.py

# Update requirements
pip freeze > requirements.txt

# Commit changes
git add .
git commit -m "Your message"
git push
```

---

## 📈 Collection Strategy

### Queue Management

Players are checked based on tier priority:

| Tier | Priority | Recheck Interval |
|------|----------|------------------|
| Challenger | 1 | 2 days |
| Grandmaster | 2 | 3 days |
| Master | 3 | 4 days |
| Diamond | 4 | 5 days |
| Emerald | 5 | 7 days |
| Platinum+ | 6 | 10-14 days |
| Unknown | N/A | 10 days |

### Smart Features

- **Incremental Updates:** Only fetches new matches since last check
- **Deduplication:** Skips already-collected matches
- **Player Discovery:** Finds new players from match participants
- **Priority Boosting:** Active players (20+ new matches) checked more frequently
- **Fallback Logic:** If queue empty, checks oldest player to prevent idle time

### Rate Limiting

- 100 requests per 2 minutes **per region**
- Total capacity: 300 requests per 2 minutes (3 regions)
- Automatic sleeping when limit hit
- Regional isolation (one region hitting limit doesn't affect others)

---

## 🎯 How the Collector Works

### Collection Loop (per region)

```python
while running:
    1. Get next player due for check (tier cascading)
    2. Find new matches for player (stop at last known match)
    3. For each new match:
        - Fetch match data (1 API call)
        - Fetch timeline data (1 API call)
        - Save to F:/neural_nexus_data/matches/
        - Insert metadata to database
        - Discover participants → add to enrichment queue
    4. Update player's next_check_after timestamp
    5. If very active (20+ new matches), boost priority
```

### Why Two API Keys?

- **Collection Key:** Used for match/timeline fetching (high volume)
- **Enrichment Key:** Used for player rank updates (separate rate limit)

This allows us to maximize API usage by using both keys simultaneously without conflicts.

---

## 📊 Current Statistics

*As of last check:*

- **Players Tracked:** 3,543
  - Challenger: 900 (300 per region)
  - Grandmaster: 2,100 (700 per region)
  - Master: 185 (discovered)
  - Unknown: 358 (discovered, pending enrichment)

- **Matches Collected:** 261 (database) / 293 (files)
  - NA1: 82 matches
  - EUW1: 88 matches
  - KR: 91 matches

- **Storage:** 18.35 MB compressed
  - Average: ~63 KB per match (match + timeline)

- **Enrichment Queue:** 66 players pending updates

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'shared'"

**Solution:** Set Python path before running:
```bash
$env:PYTHONPATH="F:\Projects\neural-nexus"
```

### "RIOT_API_KEY_COLLECTION is required"

**Solution:** 
1. Go to https://developer.riotgames.com/
2. Sign in with your Riot account
3. Copy your development API key
4. Update `.env` file with the key
5. Note: Keys expire every 24 hours

### "Connection to server at localhost (::1), port 5432 failed"

**Solution:** Start PostgreSQL service:
- Windows: Services → PostgreSQL → Start
- Or run: `net start postgresql-x64-18`

### Collector hangs on shutdown

**Current behavior:** Takes 5-10 seconds to fully shut down after Ctrl+C. This is normal - threads are finishing their current operations gracefully.

### "API Error 400" when discovering players

**Solution:** This is expected. Some players have account transfers or deleted accounts. They're marked as UNKNOWN and queued for enrichment.

### Rate limit errors

**Symptoms:** "⏸️ Rate limit hit for {region}, sleeping X seconds"

**This is normal!** The rate limiter is working correctly. The collector will automatically resume after waiting.

---

## 🔮 Next Steps

### Immediate (Next Session)

1. **Build Enrichment Service**
   - Process enrichment queue
   - Update player ranks using ACCOUNT-V1 → SUMMONER-V4 → LEAGUE-V4 flow
   - Update Riot IDs (gameName#tagLine)
   - Handle API errors gracefully

2. **Test Integration**
   - Run collector + enrichment together
   - Verify queue processing works
   - Confirm UNKNOWN players get proper tiers

### Short Term

3. **Web Dashboard** (FastAPI + React)
   - Real-time collection statistics
   - Player search and profiles
   - Queue management interface
   - API key status/refresh

4. **Monitoring & Logging**
   - Structured logging to files
   - Error tracking
   - Performance metrics
   - Health checks

### Long Term

5. **ML Pipeline**
   - Data preprocessing for model training
   - Feature engineering (champion pools, build paths, etc.)
   - Draft Prophet (win prediction)
   - Build Optimizer (item recommendations)

6. **Production Features**
   - Automated key refresh
   - Data backup system
   - API rate limit optimization
   - Advanced analytics

---

## 📝 Development Notes

### Important Reminders

- **Always set `$env:PYTHONPATH`** when opening new terminal
- **Refresh API keys daily** (they expire after 24 hours)
- **Check PostgreSQL is running** before starting collector
- **Use lowercase region codes** (na1, euw1, kr) in code
- **Commit regularly** to track progress

### Code Patterns

```python
# Always use context managers for database operations
with db_pool.get_cursor() as cursor:
    cursor.execute("SELECT ...")
    # Auto-commit on success, rollback on error

# Regional rate limiting is automatic
api_client = RiotAPIClient(api_key)
match = api_client.get_match(match_id, region)  # Rate limit handled internally

# Player discovery automatically queues for enrichment
player_discovery.process_match_participants(match_data)  # Adds to enrichment_queue
```

### Testing

```bash
# Before making changes, test current functionality:
python scripts/test_db.py          # Database works?
python scripts/test_riot_api.py    # API calls work?
python scripts/check_data.py       # Data looks good?
```

---

## 🤝 Contributing

### Git Workflow

```bash
# Pull latest changes
git pull

# Make changes, test thoroughly

# Stage and commit
git add .
git commit -m "Clear description of changes"

# Push to GitHub
git push
```

### Commit Message Guidelines

- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructuring
- `docs:` Documentation updates
- `test:` Test additions
- `chore:` Maintenance tasks

---

## 📚 Resources

### Riot API Documentation
- Main Portal: https://developer.riotgames.com/
- API Reference: https://developer.riotgames.com/apis
- Rate Limiting: https://developer.riotgames.com/docs/portal#web-apis_rate-limiting

### League of Legends Data
- Data Dragon (static data): https://developer.riotgames.com/docs/lol#data-dragon
- Patch Notes: https://www.leagueoflegends.com/en-us/news/tags/patch-notes/

### Python Libraries Used
- FastAPI: https://fastapi.tiangolo.com/
- psycopg3: https://www.psycopg.org/psycopg3/
- httpx: https://www.python-httpx.org/

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Riot Games for the comprehensive API
- PostgreSQL for reliable data storage
- The League of Legends data science community

---

**Built with ❤️ for the League of Legends community**

*Last updated: October 29, 2025*
*Project maintained by: hl0659*
*Repository: https://github.com/hl0659/neural-nexus*
