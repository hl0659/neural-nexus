# 🧠 Neural Nexus v3.0

**Revolutionary Dual-Key Parallel Collection System for League of Legends Match Data**

## 📊 Project Status

**Phase:** APEX Service Complete, NEXUS Service Pending  
**Data Collected:** 17,537+ matches with full timeline data  
**Players Discovered:** 1,567 (894 Challenger seeds + 673 network discovered)  
**Storage:** ~1.1 GB compressed JSON data

---

## 🎯 Overview

Neural Nexus v3.0 is a sophisticated data collection system that maximizes Riot API throughput by using two separate API keys operating in parallel across multiple regions. The system intelligently collects match data, discovers player networks, and expands from high-elo into lower ranks.

### Key Innovation: Dual-Key Architecture

- **APEX Key** - Focuses on Challenger/Grandmaster players
- **NEXUS Key** - Expands network through Master and below
- **Parallel Processing** - All 3 regions (NA1, EUW1, KR) simultaneously
- **Match Locking** - Prevents duplicate collection between keys

---

## ✨ Features

### Data Collection
- ✅ **Deep Historical Collection** - 200 games per player (not just recent)
- ✅ **Full Match Data** - Complete match + timeline data for every game
- ✅ **Participant Processing** - Extracts all 10 players from each match
- ✅ **Network Discovery** - Automatically expands from seeds into connected players
- ✅ **Compressed Storage** - Gzipped JSON files (~60KB per match avg)

### Performance Optimization
- ✅ **Parallel Regional Collection** - 3 regions simultaneously
- ✅ **Intelligent Rate Limiting** - Per-key, per-region tracking
- ✅ **Match Locking System** - Database-backed coordination
- ✅ **Smart Participant Processing** - Checks database before API calls (50% reduction)
- ✅ **Zero Duplication** - Both keys coordinate seamlessly

### Database
- ✅ **PostgreSQL 18** - Robust relational storage
- ✅ **Riot ID Primary Keys** - Universal player identification
- ✅ **Dual PUUID Support** - Stores both APEX and NEXUS encrypted PUUIDs
- ✅ **Queue Management** - Separate work queues for each service
- ✅ **System Monitoring** - Real-time status tracking

---

## 📁 Project Structure

```
neural-nexus/
├── services/
│   ├── apex/                      # APEX Service (High Elo)
│   │   ├── seeder.py              ✅ Seeds Challenger players (parallel)
│   │   ├── collector.py           ✅ Deep match collection (200 games)
│   │   ├── player_processor.py   ✅ Participant extraction (optimized)
│   │   └── run_collection_parallel.py  ✅ Parallel collection runner
│   │
│   ├── nexus/                     # NEXUS Service (Network Expansion)
│   │   └── [Pending Implementation]
│   │
│   └── shared/                    # Shared Utilities
│       ├── api/
│       │   ├── riot_client.py     ✅ Dual-key API client
│       │   └── rate_limiter.py    ✅ Per-key, per-region limits
│       ├── storage/
│       │   ├── json_handler.py    ✅ Gzipped match storage
│       │   └── match_lock.py      ✅ Coordination system
│       └── models/
│           ├── player.py          ✅ Player data structures
│           └── match.py           ✅ Match data structures
│
├── database/
│   ├── operations/
│   │   ├── player_ops.py          ✅ Player CRUD with Riot ID
│   │   ├── match_ops.py           ✅ Match CRUD with locking
│   │   ├── queue_ops.py           ✅ Queue management
│   │   └── status_ops.py          ✅ System status tracking
│   └── schema_v3.sql              ✅ Complete database schema
│
├── shared/
│   ├── config/
│   │   └── settings.py            ✅ Environment configuration
│   └── database/
│       └── connection.py          ✅ Connection pooling
│
└── data/ (F: drive)
    └── F:/neural_nexus_data_v3/
        ├── matches/               ✅ 17,537+ match files
        │   ├── apex/              ✅ APEX-collected matches
        │   └── nexus/             (Empty - pending NEXUS)
        └── timelines/             ✅ Complete timeline data
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 18
- Two Riot API Keys (Development tier or higher)
- ~50GB storage space

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/neural-nexus.git
cd neural-nexus
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

Required `.env` variables:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/neural_nexus_v3
RIOT_API_KEY_APEX=RGAPI-your-apex-key
RIOT_API_KEY_NEXUS=RGAPI-your-nexus-key
REGIONS=na1,euw1,kr
MATCH_HISTORY_DEPTH=200
DATA_PATH=F:/neural_nexus_data_v3
```

5. **Initialize database**
```bash
psql -U postgres
CREATE DATABASE neural_nexus_v3;
\q

psql -U postgres -d neural_nexus_v3 < database/schema_v3.sql
```

6. **Create data directories**
```bash
python scripts/init_directories.py
```

---

## 💻 Usage

### Phase 1: Seed Challenger Players

```bash
python -m services.apex.seeder
```

Seeds ~900 Challenger players from NA1, EUW1, and KR in parallel.

**Output:** ~894 players in APEX queue, ready for collection

### Phase 2: Collect Matches (Parallel)

```bash
python -m services.apex.run_collection_parallel --hours 5
```

Runs parallel collection across all 3 regions for specified duration.

**Performance:**
- ~20 matches per region per rate limit window
- ~600 matches/hour per region
- ~1,800 matches/hour total (all regions)

### Phase 3: Process Participants

Automatically integrated into collector. Extracts all 10 players from each match, discovers network connections, and queues non-Challenger players for NEXUS.

---

## 📊 Current Statistics

```
Players:
  - Challenger Seeds: 894
  - Discovered Players: 673
  - Total: 1,567
  
Queues:
  - APEX Queue: 1,010 players
  - NEXUS Queue: 555 players (ready for expansion!)
  
Matches:
  - Total Collected: 17,537
  - Storage Size: ~1.1 GB (compressed)
  - Average: ~60 KB per match
  
API Efficiency:
  - Match Collection: 2 calls per new match
  - Participant Processing: ~4-6 calls per match (optimized)
  - Rate Limit Compliance: 100%
```

---

## 🏗️ Architecture

### Dual-Key Coordination

```
┌─────────────────────────────────────────────────────────┐
│                    APEX KEY (High Elo)                  │
│                                                         │
│  1. Seed Challenger/GM (894 players)                   │
│  2. Collect 200 games each                             │
│  3. Extract all participants                            │
│  4. Discover lower-rank players → NEXUS Queue          │
└─────────────────────────────────────────────────────────┘
                           ↓
                  Discovers Master/Diamond
                           ↓
┌─────────────────────────────────────────────────────────┐
│                NEXUS KEY (Network Expansion)            │
│                                                         │
│  1. Activate when non-Challenger players found         │
│  2. Resolve Riot ID → NEXUS PUUID                      │
│  3. Collect 200 games each                             │
│  4. Expand network exponentially                        │
└─────────────────────────────────────────────────────────┘
                           ↓
                  Both store to unified DB
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Unified PostgreSQL Database                │
│                                                         │
│  - Players identified by Riot ID (universal)           │
│  - Both PUUIDs stored per player                        │
│  - Match locks prevent duplication                      │
│  - Full participant linkage                             │
└─────────────────────────────────────────────────────────┘
```

### Key Discoveries

**PUUID Encryption:** Each API key encrypts PUUIDs differently. We use Riot ID (gameName#tagLine) as the universal identifier and store both encrypted PUUIDs.

**Match Locking:** Database-backed coordination prevents both keys from collecting the same match simultaneously.

**Participant Optimization:** Checking database before API calls reduces participant processing from 20 → 4-6 calls per match.

---

## 🔧 Configuration

### Rate Limits

```python
RATE_LIMIT_REQUESTS = 100      # Per 2 minutes
RATE_LIMIT_WINDOW_SECONDS = 120
```

Each region has independent rate limits, so 3 regions = 300 calls per 2 minutes per key.

### Match History Depth

```python
MATCH_HISTORY_DEPTH = 200  # Games per player
```

API limit is 100 per request, so we make 2 requests per player.

### Regional Routing

```python
REGIONAL_ROUTING = {
    'na1': 'americas',
    'euw1': 'europe',
    'kr': 'asia'
}
```

Some endpoints use platform routing (na1, euw1), others use regional (americas, europe, asia).

---

## 🧪 Testing

Each component has standalone tests:

```bash
# Test configuration
python -m shared.config.settings

# Test database connection
python -m shared.database.connection

# Test API clients
python -m services.shared.api.riot_client

# Test rate limiter
python -m services.shared.api.rate_limiter

# Test match locking
python -m services.shared.storage.match_lock

# Test player operations
python -m database.operations.player_ops

# Test match operations
python -m database.operations.match_ops

# Test queue operations
python -m database.operations.queue_ops

# Test status operations
python -m database.operations.status_ops

# Test seeder
python -m services.apex.seeder

# Test collector
python -m services.apex.collector

# Test participant processor
python -m services.apex.player_processor
```

---

## 📈 Performance Metrics

### Collection Throughput

| Metric | Value |
|--------|-------|
| Matches/hour (per region) | ~600 |
| Matches/hour (all regions) | ~1,800 |
| Matches/day (theoretical) | ~43,200 |
| Storage per match | ~60 KB |

### Database Performance

| Operation | Time |
|-----------|------|
| Insert player | <1ms |
| Insert match | <2ms |
| Insert participant | <1ms |
| Match lock acquire | <5ms |
| Queue depth check | <1ms |

---

## 🗺️ Roadmap

### Phase 1: APEX Service ✅ COMPLETE
- [x] Dual-key API client
- [x] Parallel region seeding
- [x] Deep match collection (200 games)
- [x] Optimized participant processing
- [x] Match locking coordination
- [x] Database operations

### Phase 2: NEXUS Service 🚧 IN PROGRESS
- [ ] NEXUS Activator (watches for lower-rank players)
- [ ] PUUID Resolver (Riot ID → NEXUS PUUID)
- [ ] NEXUS Collector (parallel collection)
- [ ] NEXUS Participant Processor
- [ ] Automatic expansion into lower ranks

### Phase 3: System Integration
- [ ] Monitoring dashboard
- [ ] Health checks
- [ ] Error recovery
- [ ] Graceful shutdown
- [ ] Progress persistence

### Phase 4: Data Analysis
- [ ] Champion win rates by patch
- [ ] Player performance metrics
- [ ] Meta evolution tracking
- [ ] Network analysis (player connections)
- [ ] Timeline event extraction

---

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Riot Games for providing the API
- PostgreSQL team for the excellent database
- Python community for amazing libraries

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ☕ and 🧠**