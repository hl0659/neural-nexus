# 🧠 Neural Nexus v3.0

**Revolutionary Dual-Key Parallel Collection System for League of Legends Match Data**

## 🎯 What's New in v3.0

- **Dual-Key Architecture**: Two API keys working in parallel (APEX + NEXUS)
- **Deep Historical Collection**: 200 games per player, not just new matches
- **Intelligent Coordination**: Match locking prevents duplication
- **Automatic Activation**: NEXUS auto-starts when lower-rank players discovered
- **Maximum Throughput**: ~3,000 matches/hour potential

## 🏗️ Architecture

```
APEX Key (Challenger/GM)  →  Deep Collection (200 games/player)
                          ↓
                     Discovers Lower Ranks
                          ↓
NEXUS Key (Master+)    →  Network Expansion (200 games/player)
                          ↓
                  Unified Database (No Duplicates)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 18
- Two Riot API keys
- 50GB+ free space on F: drive

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/neural-nexus.git
cd neural-nexus

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys

# Create database
psql -U postgres
CREATE DATABASE neural_nexus_v3;
\q

# Initialize schema
psql -U postgres -d neural_nexus_v3 < database/schema_v3.sql

# Create data directories
python scripts/setup_directories.py
```

### Running

```bash
# Start APEX service (Terminal 1)
python -m services.apex.main

# Monitor system (Terminal 2)
python scripts/monitor_system.py

# NEXUS will auto-start when lower-rank players discovered
```

## 📊 Key Features

### APEX Service (High Elo Focus)
- Seeds Challenger/Grandmaster players (~3,000 total)
- Collects 200-game history for each
- Extracts Riot IDs for all match participants
- Discovers network connections

### NEXUS Service (Network Expansion)
- Automatically activates on lower-rank discovery
- Converts Riot IDs to NEXUS PUUIDs
- Branches through Master/Diamond/Emerald
- Parallel collection with APEX

### Match Locking System
- Prevents duplicate collection
- Database-backed coordination
- Auto-expiry after 1 hour
- Safe for parallel operation

## 🗄️ Database Schema

- **players**: Universal registry (Riot ID + both PUUIDs)
- **matches**: Match metadata + file paths
- **match_participants**: Player performance data
- **match_bans**: Champion bans per match
- **match_locks**: Coordination mechanism
- **collection_queues**: Work queues for both services
- **system_status**: Real-time monitoring

## 📈 Expected Performance

- **APEX**: ~1,500 matches/hour
- **NEXUS**: ~1,500 matches/hour
- **Combined**: ~3,000 matches/hour
- **Time to 1M matches**: ~14 days continuous

## 🔑 Critical Concepts

### PUUID Encryption
Each API key generates different encrypted PUUIDs for the same player. Solution: Use Riot ID (gameName#tagLine) as universal identifier.

### Deep Collection
Fetch full 200-game history, not just recent matches. Provides comprehensive historical context.

### Match Locking
Prevents both services from collecting the same match. Essential for parallel operation.

## 📚 Documentation

- [Complete Implementation Guide](IMPLEMENTATION_GUIDE_V3.md)
- API Documentation: Coming soon
- Architecture Deep Dive: Coming soon

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Riot Games API
- League of Legends community
- All contributors to v2.0 (archived in `archive/v2-final` branch)

---

**Version**: 3.0.0  
**Status**: 🟢 Active Development  
**Last Updated**: October 2025
