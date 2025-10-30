# Neural Nexus v3.0 - Setup Guide

## Step-by-Step Implementation

### ✅ Phase 1: Repository & File Setup (You're here!)

**Your current status:**
- ✅ Created `archive/v2-final` branch with old code
- ✅ Cleaned `main` branch
- ✅ Local directory exists: `F:\Projects\neural-nexus`

**Next actions:**

1. **Copy all generated files to your local repo:**
   ```powershell
   cd F:\Projects\neural-nexus
   
   # Copy structure generator
   # Copy .env.example
   # Copy .gitignore
   # Copy README.md
   # Copy requirements.txt
   # Copy schema_v3.sql
   # Copy IMPLEMENTATION_GUIDE_V3.md (from your project)
   ```

2. **Run structure generator:**
   ```powershell
   python setup_v3_structure.py
   ```

3. **Create your .env file:**
   ```powershell
   copy .env.example .env
   # Then edit .env with your actual API keys
   ```

4. **Commit initial structure:**
   ```bash
   git add .
   git commit -m "Initial v3.0 structure - Dual-key parallel architecture"
   git push origin main
   ```

---

### 📦 Phase 2: Environment Setup

1. **Create Python virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Verify installations:**
   ```powershell
   python -c "import psycopg2; import requests; import dotenv; print('All packages installed!')"
   ```

---

### 🗄️ Phase 3: Database Setup

1. **Create database:**
   ```powershell
   psql -U postgres
   ```
   ```sql
   CREATE DATABASE neural_nexus_v3;
   \q
   ```

2. **Run schema:**
   ```powershell
   psql -U postgres -d neural_nexus_v3 -f schema_v3.sql
   ```

3. **Verify schema:**
   ```powershell
   psql -U postgres -d neural_nexus_v3
   ```
   ```sql
   \dt
   -- Should show: players, matches, match_participants, match_bans,
   --              match_locks, collection_queues, system_status
   
   SELECT * FROM system_health;
   SELECT * FROM system_status;
   \q
   ```

---

### 📁 Phase 4: Data Directory Setup

1. **Create F: drive structure:**
   ```powershell
   $base = "F:\neural_nexus_data_v3"
   $services = @("apex", "nexus")
   $regions = @("na1", "euw1", "kr")
   $dirs = @("matches", "timelines", "logs")
   
   foreach ($dir in $dirs) {
       foreach ($service in $services) {
           foreach ($region in $regions) {
               New-Item -ItemType Directory -Path "$base\$dir\$service\$region" -Force
           }
       }
   }
   
   Write-Host "✓ Data directories created!"
   ```

2. **Verify structure:**
   ```powershell
   tree F:\neural_nexus_data_v3 /F
   ```

---

### 🔧 Phase 5: Core Component Development

**Build order (as per implementation guide):**

#### 5.1 Shared Components (Foundation)
- [ ] `shared/config/settings.py` - Environment loader
- [ ] `shared/database/connection.py` - PostgreSQL connection pool
- [ ] `services/shared/api/riot_client.py` - Dual-key API client
- [ ] `services/shared/api/rate_limiter.py` - Per-key rate limiting
- [ ] `services/shared/storage/match_lock.py` - Match locking system
- [ ] `services/shared/storage/json_handler.py` - Gzipped JSON storage
- [ ] `services/shared/models/player.py` - Player data models
- [ ] `services/shared/models/match.py` - Match data models
- [ ] `database/operations/player_ops.py` - Player CRUD
- [ ] `database/operations/match_ops.py` - Match CRUD
- [ ] `database/operations/queue_ops.py` - Queue management
- [ ] `database/operations/status_ops.py` - System status

#### 5.2 APEX Service (High Elo Collection)
- [ ] `services/apex/seeder.py` - Seed Challenger/GM
- [ ] `services/apex/player_processor.py` - Get Riot IDs + ranks
- [ ] `services/apex/collector.py` - Deep match collection (200 games)
- [ ] `services/apex/queue_manager.py` - APEX work queue
- [ ] `services/apex/main.py` - Orchestrator

#### 5.3 NEXUS Service (Network Expansion)
- [ ] `services/nexus/activator.py` - Auto-activation watcher
- [ ] `services/nexus/puuid_resolver.py` - Riot ID → NEXUS PUUID
- [ ] `services/nexus/collector.py` - Match collection
- [ ] `services/nexus/queue_manager.py` - NEXUS work queue
- [ ] `services/nexus/main.py` - Orchestrator

#### 5.4 Scripts & Utilities
- [ ] `scripts/test_dual_keys.py` - Verify both API keys work
- [ ] `scripts/init_db_v3.py` - Database initialization helper
- [ ] `scripts/monitor_system.py` - Live monitoring dashboard
- [ ] `scripts/cleanup_locks.py` - Remove expired locks

---

### 🧪 Phase 6: Testing & Validation

1. **Test API keys:**
   ```powershell
   python scripts/test_dual_keys.py
   ```

2. **Test database connection:**
   ```powershell
   python scripts/init_db_v3.py
   ```

3. **Start APEX service:**
   ```powershell
   python -m services.apex.main
   ```

4. **Monitor in another terminal:**
   ```powershell
   python scripts/monitor_system.py
   ```

5. **Watch for NEXUS auto-activation:**
   - Should trigger when first non-Challenger/GM player discovered
   - Check monitor for "🌐 NEXUS Activated!" message

---

### 🎯 Success Criteria

**Phase 1 Complete:**
- ✅ All 3,000 Challenger/GM players seeded
- ✅ Players have Riot IDs
- ✅ 200-game history collected per player
- ✅ 600,000+ matches in database

**Phase 2 Complete:**
- ✅ NEXUS auto-activated
- ✅ Lower-rank players have nexus_puuid
- ✅ No duplicate matches
- ✅ Both services running in parallel

---

### 📊 Expected Timeline

- **Setup (Phases 1-4):** 1-2 hours
- **Core Components (Phase 5.1):** 4-6 hours
- **APEX Service (Phase 5.2):** 3-4 hours
- **NEXUS Service (Phase 5.3):** 3-4 hours
- **Testing & Validation:** 2-3 hours

**Total:** ~15-20 hours development time

---

### 🆘 Troubleshooting

**Issue: Database connection fails**
- Check PostgreSQL is running: `Get-Service postgresql*`
- Verify credentials in .env
- Test connection: `psql -U postgres -d neural_nexus_v3`

**Issue: API key invalid**
- Check keys in .env (no quotes, no spaces)
- Verify keys at: https://developer.riotgames.com
- Test with curl/Postman first

**Issue: Import errors**
- Activate venv: `.\venv\Scripts\activate`
- Verify packages: `pip list`
- Reinstall: `pip install -r requirements.txt`

**Issue: Directory not found**
- Check F: drive accessible
- Verify DATA_PATH in .env
- Run directory setup script again

---

### 📝 Development Tips

1. **Start small:** Build and test each component individually
2. **Use logging:** Add extensive logging from the start
3. **Test with limits:** Start with count=5 instead of 200
4. **Monitor database:** Keep pgAdmin or psql open
5. **Git commit often:** Commit after each working component

---

### 🎓 Key Architecture Points to Remember

1. **Riot ID is primary identifier:** (region, gameName, tagLine)
2. **Both PUUIDs stored:** apex_puuid + nexus_puuid for same player
3. **Match locking is critical:** Prevents duplicate collection
4. **Deep collection:** Always fetch 200 games, not just recent
5. **NEXUS auto-activates:** No manual trigger needed

---

## You Are Here: 📍

```
[✅ Phase 1: Files Generated]
    ⬇️
[ ⏳ Phase 2: Copy to Local & Setup Env]
    ⬇️
[ ⏸️  Phase 3: Database Setup]
    ⬇️
[ ⏸️  Phase 4: Data Directories]
    ⬇️
[ ⏸️  Phase 5: Component Development]
    ⬇️
[ ⏸️  Phase 6: Testing & Launch]
```

**Next immediate steps:**
1. Copy all files to `F:\Projects\neural-nexus`
2. Run `setup_v3_structure.py`
3. Create `.env` with your API keys
4. Commit to GitHub

Ready to proceed? Let me know when you've copied the files!
