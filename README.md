# 🧠 Neural Nexus v3.0

**Revolutionary Dual-Key Parallel Collection System for League of Legends Match Data**

## 📊 Project Status

**Phase:** Production Ready - Unified Pipeline with Full Tooling  
**Data Collected:** 17,600+ matches with full timeline data  
**Players Discovered:** 2,300+ (894 Challenger seeds + 1,400+ network discovered)  
**Storage:** ~1.1 GB compressed JSON data  
**Uptime:** Stable with graceful shutdown and progress persistence

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

### Operational Features
- ✅ **Progress Tracking** - Resume collection after interruption
- ✅ **Graceful Shutdown** - Clean exit with Ctrl+C handling
- ✅ **Live Health Monitoring** - Check system status during collection
- ✅ **Automated Maintenance** - Clean locks, reset stuck queues
- ✅ **Pre-flight Checks** - Validate system readiness before collection
- ✅ **Error Recovery** - Automatic retry logic and failure handling

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
│   ├── health_check.py                    ✅ Live system monitoring (safe during collection)
│   ├── database_maintenance.py            ✅ Automated cleanup tasks
│   ├── preflight_nexus.py                 ✅ NEXUS pre-flight validation
│   ├── cleanup_locks.py                   ✅ Manual match lock cleanup
│   ├── fix_nexus_status.py               ✅ Status metric recalculation
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
- **Saves progress automatically** - Resume after interruption
- **Graceful shutdown** - Press Ctrl+C for clean exit
- **Real-time statistics** - Updated every 5 players per region

**Monitoring during collection:**
```bash
# Open a second terminal while collection is running:
python scripts/health_check.py

# Check queue status:
python scripts/check_nexus_queue.py
```

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

## 🛠️ Operational Features

### Progress Tracking & Recovery
The unified runner automatically saves progress to disk:
- **Location:** `F:/neural_nexus_data_v3/progress/unified_progress.json`
- **Saves every:** Player processed
- **Resume:** Automatically offers to resume on restart
- **Reset:** Delete progress file to start fresh

### Graceful Shutdown
Press **Ctrl+C** at any time for clean exit:
1. Stops accepting new work
2. Finishes current players (with timeout)
3. Saves final progress
4. Updates database status
5. Shows final statistics

**Recovery:** Simply restart the command to resume where you left off.

### Live Monitoring
Run health checks while collection is active (separate terminal):
```bash
# Quick health check
python scripts/health_check.py

# Detailed queue analysis
python scripts/check_nexus_queue.py
```

### Error Handling
- **Automatic retries:** Failed players go back to queue with cooldown
- **Attempt tracking:** Players with >5 failures are marked for review
- **Error logging:** All errors saved to database with timestamps
- **Rate limit recovery:** Automatic backoff and resume

### Best Practices
1. **Before long runs:** Run `python scripts/preflight_nexus.py`
2. **Check health periodically:** Use `health_check.py` during collection
3. **Clean up weekly:** Run `database_maintenance.py` to optimize
4. **Monitor queue balance:** Keep both APEX and NEXUS queues populated
5. **Backup database:** Regular PostgreSQL dumps recommended

---

## 🔧 Operational Scripts

### Pre-Collection
```bash
# Verify system is ready for collection
python scripts/preflight_nexus.py

# Shows:
# - NEXUS API key status
# - Queue depths by region
# - Sample players to process
# - Current database stats
```

### During Collection
```bash
# Live health monitoring (safe to run while collecting)
python scripts/health_check.py

# Shows:
# - Service status (APEX/NEXUS active/inactive)
# - Queue depths by status
# - Recent activity (last 5 minutes)
# - Active match locks
# - Database and storage stats
```

### Maintenance
```bash
# Automated cleanup (run periodically)
python scripts/database_maintenance.py

# Performs:
# - Removes expired match locks
# - Resets stuck processing entries
# - Cleans failed queue entries (>5 attempts)
# - Refreshes queue schedules
# - Analyzes tables for optimization

# Manual lock cleanup
python scripts/cleanup_locks.py

# Fix system status metrics
python scripts/fix_nexus_status.py

# Analyze queue composition
python scripts/check_nexus_queue.py
```

---

## 🗺️ Development Roadmap

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] Dual-key API client with rate limiting
- [x] Database schema with Riot ID primary keys
- [x] Match locking coordination system
- [x] APEX service (Challenger collection)
- [x] NEXUS service (Network expansion)
- [x] Unified pipeline with automatic fallback

### Phase 2: Operational Tools ✅ COMPLETE
- [x] Progress tracking and persistence
- [x] Graceful shutdown handling (Ctrl+C)
- [x] Live health monitoring during collection
- [x] Automated maintenance scripts
- [x] Pre-flight validation checks
- [x] Error recovery and retry logic

### Phase 3: Production Optimization 🚧 IN PROGRESS
- [ ] Real-time monitoring dashboard (web UI)
- [ ] Automated alerts (Discord/Slack webhooks)
- [ ] Performance metrics visualization
- [ ] Enhanced logging with log levels
- [ ] Configuration management UI
- [ ] Backup and restore utilities

### Phase 4: Data Analysis Pipeline 📋 PLANNED
- [ ] Champion win rate analysis by patch
- [ ] Player performance metrics and trends
- [ ] Meta evolution tracking over time
- [ ] Timeline event extraction and analysis
- [ ] Build path optimization analysis
- [ ] Matchup win rates by champion

### Phase 5: Machine Learning Features 🔮 FUTURE
- [ ] Draft Prophet (pick/ban predictions)
- [ ] Build Optimizer (item recommendations)
- [ ] Macro Advisor (objective timing)
- [ ] Win probability calculator
- [ ] Player performance predictor

---

## 📈 Performance Metrics

### Collection Performance
| Metric | Value |
|--------|-------|
| Matches/hour (per region) | ~600 |
| Matches/hour (all regions) | ~1,800 |
| Matches/day (theoretical) | ~43,200 |
| Storage per match | ~60 KB |
| API calls per match | 2-6 |
| Duplicate rate | 0% |

### Operational Metrics
| Metric | Value |
|--------|-------|
| Average shutdown time | <5 seconds |
| Progress save frequency | Per player |
| Recovery success rate | 100% |
| Match lock expiry | 1 hour |
| Queue retry cooldown | 1 hour |
| Max retry attempts | 5 |

---

## 🔍 Troubleshooting

### Collection Issues

**Problem:** "No players in queue"
```bash
# Check queue status
python scripts/check_nexus_queue.py

# If APEX empty but NEXUS has players:
# - System will automatically switch to NEXUS
# - Just wait for the fallback

# If both empty:
# - Run seeder to add more players
# - Check if players need NEXUS PUUID resolution
```

**Problem:** "Rate limited"
```bash
# This is normal! The system will wait automatically
# You'll see: "⏳ [APEX:NA1] Rate limited. Waiting 45.2s..."

# To check current rate limit usage:
python scripts/health_check.py
# Look for "Recent Activity (last 5 minutes)"
```

**Problem:** "Stuck processing entries"
```bash
# Run maintenance to reset stuck entries
python scripts/database_maintenance.py

# This will reset any entries stuck in "processing" for >1 hour
```

**Problem:** "Too many match locks"
```bash
# Clean expired locks
python scripts/cleanup_locks.py

# For aggressive cleanup (all locks):
# Answer 'yes' when prompted
```

### Database Issues

**Problem:** "Connection failed"
```bash
# Check PostgreSQL is running
# Windows: Check Services
# Linux: systemctl status postgresql

# Test connection manually
psql -U postgres -d neural_nexus_v3
```

**Problem:** "Duplicate key violation"
```bash
# Usually means data already exists (this is good!)
# The ON CONFLICT clauses should handle this automatically
# If persistent, check error logs in database
```

### Performance Issues

**Problem:** "Collection seems slow"
```bash
# Check health
python scripts/health_check.py

# Look for:
# - High error rate (should be <5%)
# - Stuck locks (should be minimal)
# - Queue imbalance (both queues should have work)

# Common fixes:
python scripts/database_maintenance.py  # Optimize tables
python scripts/cleanup_locks.py         # Remove stale locks
```

**Problem:** "High API call count per match"
```bash
# Normal range: 2-6 calls per match
# High (>10): Might indicate database lookup issues

# Check if database indexes are healthy:
python scripts/database_maintenance.py
```

### Getting Help

1. **Check logs:** Look for error messages in console output
2. **Run health check:** `python scripts/health_check.py`
3. **Check database:** Query `system_status` table for service status
4. **Review queue:** `python scripts/check_nexus_queue.py`

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