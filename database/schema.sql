-- Neural Nexus Database Schema

-- Player tracking and scheduling
CREATE TABLE IF NOT EXISTS players (
    puuid VARCHAR(78) PRIMARY KEY,
    summoner_id VARCHAR(63),
    account_id VARCHAR(56),
    summoner_name VARCHAR(32),
    tag_line VARCHAR(16),
    tier VARCHAR(20),
    rank VARCHAR(4),
    league_points INTEGER,
    wins INTEGER,
    losses INTEGER,
    region VARCHAR(10),
    last_match_id VARCHAR(30),
    last_rank_update TIMESTAMP,
    next_check_after TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match metadata and storage paths
CREATE TABLE IF NOT EXISTS matches (
    match_id VARCHAR(30) PRIMARY KEY,
    region VARCHAR(10),
    game_version VARCHAR(20),
    game_duration INTEGER,
    game_creation BIGINT,
    patch VARCHAR(10),
    json_path TEXT,
    timeline_json_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Links players to matches with performance data
CREATE TABLE IF NOT EXISTS match_participants (
    match_id VARCHAR(30) REFERENCES matches(match_id),
    puuid VARCHAR(78) REFERENCES players(puuid),
    participant_id INTEGER,
    champion_id INTEGER,
    champion_name VARCHAR(50),
    team_id INTEGER,
    team_position VARCHAR(20),
    won BOOLEAN,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    total_damage_dealt_to_champions INTEGER,
    gold_earned INTEGER,
    cs_score INTEGER,
    vision_score INTEGER,
    PRIMARY KEY (match_id, puuid)
);

-- Ban phase tracking with order
CREATE TABLE IF NOT EXISTS match_bans (
    match_id VARCHAR(30) REFERENCES matches(match_id),
    team_id INTEGER,
    champion_id INTEGER,
    pick_turn INTEGER,
    PRIMARY KEY (match_id, team_id, pick_turn)
);

-- Work queue for collection
CREATE TABLE IF NOT EXISTS collection_queue (
    puuid VARCHAR(78) PRIMARY KEY REFERENCES players(puuid),
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    next_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Work queue for enrichment
CREATE TABLE IF NOT EXISTS enrichment_queue (
    puuid VARCHAR(78) PRIMARY KEY REFERENCES players(puuid),
    needs_summoner_id BOOLEAN DEFAULT FALSE,
    needs_rank BOOLEAN DEFAULT FALSE,
    needs_riot_id BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_players_region_tier ON players(region, tier);
CREATE INDEX IF NOT EXISTS idx_players_next_check ON players(next_check_after);
CREATE INDEX IF NOT EXISTS idx_matches_region_patch ON matches(region, patch);
CREATE INDEX IF NOT EXISTS idx_participants_puuid ON match_participants(puuid);
CREATE INDEX IF NOT EXISTS idx_participants_champion ON match_participants(champion_id);
CREATE INDEX IF NOT EXISTS idx_collection_queue_next ON collection_queue(next_attempt, status);