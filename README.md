# 🧠 Neural Nexus v3.0

**Revolutionary Dual-Key Parallel Collection System for League of Legends Match Data**

## 📊 Project Status

**Phase:** Both Services Operational - Unified Pipeline Active  
**Data Collected:** 17,600+ matches with full timeline data  
**Players Discovered:** 2,300+ (894 Challenger seeds + 1,400+ network discovered)  
**Storage:** ~1.1 GB compressed JSON data

---

## 🎯 Overview

Neural Nexus v3.0 is a sophisticated data collection system that maximizes Riot API throughput by using two separate API keys operating in parallel across multiple regions. The system intelligently collects match data, discovers player networks, and expands from high-elo into lower ranks.

### Key Innovation: Dual-Key Architecture

- **APEX Key** - Focuses on Challenger/Grandmaster players
- **NEXUS Key** - Expands network through Master and below
- **Parallel Processing** - All 3 regions (NA1, EUW1, KR) simultaneously
- **Match Locking** - Prevents duplicate collection between keys
- **Unified Pipeline** - Automatic APEX → NEXUS fallback when queues empty

---

## ✨ Features

### Data Collection
- ✅ **Deep Historical Collection** - 200 games per player (not just recent)
- ✅ **Full Match Data** - Complete match + timeline data for every game
- ✅ **Participant Processing** - Extracts all 10 players from each match
- ✅ **Network Discovery** - Automatically expands from seeds into connected players
- ✅ **Compressed Storage** - Gzipped JSON files (~60KB per match avg)
- ✅ **Unified Collection** - Seamless APEX → NEXUS fallback

### Performance Optimization
- ✅ **Parallel Regional Collection** - 3 regions simultaneously
- ✅ **Intelligent Rate Limiting** - Per-key, per-region tracking
- ✅ **Match Locking System** - Database-backed coordination
- ✅ **Smart Participant Processing** - Checks database before API calls (50% reduction)
- ✅ **Zero Duplication** - Both keys coordinate seamlessly
- ✅ **Automatic Queue Management** - PUUID resolution on-demand

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
│   ├── apex/                              # APEX Service (High Elo)
│   │   ├── seeder.py                      ✅ Seeds Challenger players (parallel)
│   │   ├── collector.py                   ✅ Deep match collection (200 games)
│   │   ├── player_processor.py           ✅ Participant extraction (optimized)
│   │   └── run_collection_parallel_unified.py  ✅ Unified APEX+NEXUS pipeline
│   │
│   ├── nexus/                             # NEXUS Service (Network Expansion)
│   │   ├── collector.py                   ✅ Deep match collection
│   │   ├── player_processor.py           ✅ Participant extraction
│   │   ├── activator.py                   ✅ On-demand PUUID resolution
│   │   └── run_collection_parallel.py    ✅ Parallel collection runner
│   │
│   └── shared/                            # Shared Utilities
│       ├── api/
│       │   ├── riot_client.py             ✅ Dual-key API client
│       │   └── rate_limiter.py            ✅ Per-key, per-region limits
│       ├── storage/
│       │   ├── json_handler.py            ✅ Gzipped match storage
│       │   └── match_lock.py              ✅ Coordination system
│       └── models/
│           ├── player.py                  ✅ Player data structures
│           └── match.py                   ✅ Match data structures
│
├── database/
│   ├── operations/
│   │   ├── player_ops.py                  ✅ Player CRUD with Riot ID
│   │   ├── match_ops.py                   ✅ Match CRUD with locking
│   │   ├── queue_ops.py                   ✅ Queue management
│   │   └── status_ops.py                  ✅ System status tracking
│   └── schema_v3.sql                      ✅ Complete database schema
│
├── scripts/
│   ├── preflight_nexus.py                 ✅ NEXUS pre-flight check
│   ├── verify_nexus_test.py              ✅ NEXUS test verification
│   ├── cleanup_locks.py                   ✅ Match lock cleanup
│   ├── fix_nexus_status.py               ✅ Status metric fixes
│   ├── check_nexus_queue.py              ✅ Queue composition analysis
│   └── show_table_structure.py           ✅ Database structure display
│
├── shared/
│   ├── config/
│   │   └── settings.py                    ✅ Environment configuration
│   └── database/
│       └── connection.py                  ✅ Connection pooling
│
└── data/ (F: drive)
    └── F:/neural_nexus_data_v3/
        ├── matches/                       ✅ 17,600+ match files
        │   ├── apex/                      ✅ APEX-collected matches
        │   └── nexus/                     ✅ NEXUS-collected matches
        └── timelines/                     ✅ Complete timeline data
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

5. **Initialize database**
```bash
# In psql:
CREATE DATABASE neural_nexus_v3;
\q

# Load schema:
psql -U postgres -d neural_nexus_v3 -f schema_v3.sql
```

6. **Create data directories**
```bash
python setup_v3_structure.py
```

---

## 💻 Usage

### Phase 1: Seed Challenger Players (One-time)
```bash
python -m services.apex.seeder
```

Seeds ~900 Challenger players from NA1, EUW1, and KR in parallel.

### Phase 2: Run Unified Collection
```bash
# Short test (30 minutes)
python -m services.apex.run_collection_parallel_unified --hours 0.5

# Standard run (2 hours)
python -m services.apex.run_collection_parallel_unified --hours 2

# Overnight run (8 hours)
python -m services.apex.run_collection_parallel_unified --hours 8
```

**What it does:**
- Processes APEX queue (Challenger/GM) first
- Automatically switches to NEXUS queue (Master/Diamond/etc.)
- Runs all 3 regions in parallel
- Coordinates via match locks to prevent duplicates
- Discovers new players from match participants

---

## 📊 Current Statistics
```
Players:
  - Challenger Seeds: 894
  - Discovered Players: 1,400+
  - Total: 2,300+
  
Queues:
  - APEX Queue: 1,000+ players
  - NEXUS Queue: 1,200+ players
  
Matches:
  - Total Collected: 17,600+
  - APEX Matches: 17,500+
  - NEXUS Matches: 100+
  - Storage Size: ~1.1 GB (compressed)
  - Average: ~60 KB per match
  
API Efficiency:
  - Match Collection: 2 calls per new match
  - Participant Processing: ~4-6 calls per match (optimized)
  - Rate Limit Compliance: 100%
```

---

## 🏗️ Architecture

### Unified Pipeline
```
┌─────────────────────────────────────────────────────────┐
│           UNIFIED COLLECTION PIPELINE                   │
│                                                         │
│  ┌─────────────────┐      ┌──────────────────┐       │
│  │   APEX Queue    │ ───→ │ Region Thread 1  │       │
│  │  (Challenger/   │      │  (NA1)           │       │
│  │   Grandmaster)  │      └──────────────────┘       │
│  └─────────────────┘                                  │
│          ↓ (when empty)                               │
│  ┌─────────────────┐      ┌──────────────────┐       │
│  │   NEXUS Queue   │ ───→ │ Region Thread 2  │       │
│  │  (Master+)      │      │  (EUW1)          │       │
│  └─────────────────┘      └──────────────────┘       │
│                                                         │
│                           ┌──────────────────┐       │
│                           │ Region Thread 3  │       │
│                           │  (KR)            │       │
│                           └──────────────────┘       │
│                                                         │
│  Features:                                             │
│  - Automatic fallback (APEX → NEXUS)                  │
│  - Match locks prevent duplicates                      │
│  - On-demand PUUID resolution                          │
│  - Tier-based queue routing                            │
└─────────────────────────────────────────────────────────┘
```

### Key Discoveries

**PUUID Encryption:** Each API key encrypts PUUIDs differently. Solution: Use Riot ID (gameName#tagLine) as universal identifier, store both encrypted PUUIDs.

**Match Locking:** Database-backed coordination prevents both keys from collecting the same match.

**Participant Optimization:** Checking database before API calls reduced processing from 20 → 4-6 calls per match.

---

## 🔧 Maintenance Scripts
```bash
# Pre-flight check before collection
python scripts/preflight_nexus.py

# Verify test results
python scripts/verify_nexus_test.py

# Clean up stale match locks
python scripts/cleanup_locks.py

# Fix system status metrics
python scripts/fix_nexus_status.py

# Analyze queue composition
python scripts/check_nexus_queue.py
```

---

## 🗺️ Next Steps

### Immediate (Completed ✅)
- [x] Dual-key API client
- [x] APEX service (Challenger collection)
- [x] NEXUS service (Network expansion)
- [x] Unified pipeline (automatic fallback)
- [x] Maintenance scripts

### Short-term
- [ ] Monitoring dashboard (real-time stats)
- [ ] Health checks & alerts
- [ ] Error recovery & retry logic
- [ ] Graceful shutdown handling
- [ ] Progress persistence across restarts

### Medium-term
- [ ] Data analysis pipeline
- [ ] Champion win rates by patch
- [ ] Player performance metrics
- [ ] Meta evolution tracking
- [ ] Timeline event extraction

### Long-term
- [ ] Machine learning features
- [ ] Draft Prophet (pick/ban predictions)
- [ ] Build Optimizer (item recommendations)
- [ ] Macro Advisor (objective timing)

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Matches/hour (per region) | ~600 |
| Matches/hour (all regions) | ~1,800 |
| Matches/day (theoretical) | ~43,200 |
| Storage per match | ~60 KB |
| API calls per match | 2-6 |
| Duplicate rate | 0% |

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

**Built with ☕ and 🧠**