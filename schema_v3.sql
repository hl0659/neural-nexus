-- ============================================================================
-- Neural Nexus v3.0 - Complete Database Schema
-- ============================================================================
-- Dual-Key Parallel Collection Architecture
-- Date: October 30, 2025
-- ============================================================================

-- Drop existing tables if rebuilding
DROP TABLE IF EXISTS match_bans CASCADE;
DROP TABLE IF EXISTS match_participants CASCADE;
DROP TABLE IF EXISTS match_locks CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS collection_queues CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS system_status CASCADE;

-- ============================================================================
-- PLAYERS TABLE - Unified player registry
-- ============================================================================
CREATE TABLE players (
    -- PRIMARY IDENTIFIER (unique per region)
    region VARCHAR(10) NOT NULL,
    game_name VARCHAR(32) NOT NULL,
    tag_line VARCHAR(16) NOT NULL,
    
    -- KEY-SPECIFIC PUUIDs (same player, different encrypted IDs)
    apex_puuid VARCHAR(78),        -- PUUID from APEX key
    nexus_puuid VARCHAR(78),       -- PUUID from NEXUS key
    
    -- RANK DATA (latest known rank)
    tier VARCHAR(20),
    rank VARCHAR(4),
    league_points INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    league_id VARCHAR(50),         -- For tracking league membership
    
    -- COLLECTION TRACKING
    last_apex_check TIMESTAMP,     -- When APEX last checked this player
    last_nexus_check TIMESTAMP,    -- When NEXUS last checked this player
    apex_match_count INTEGER DEFAULT 0,
    nexus_match_count INTEGER DEFAULT 0,
    
    -- METADATA
    discovered_by VARCHAR(10),     -- 'apex' or 'nexus'
    is_seed_player BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (region, game_name, tag_line)
);

-- Indexes for efficient queries
CREATE INDEX idx_players_tier ON players(tier);
CREATE INDEX idx_players_apex_check ON players(last_apex_check);
CREATE INDEX idx_players_nexus_check ON players(last_nexus_check);
CREATE INDEX idx_players_apex_puuid ON players(apex_puuid);
CREATE INDEX idx_players_nexus_puuid ON players(nexus_puuid);
CREATE INDEX idx_players_discovered ON players(discovered_by);
CREATE INDEX idx_players_seed ON players(is_seed_player) WHERE is_seed_player = TRUE;

COMMENT ON TABLE players IS 'Universal player registry using Riot ID as primary identifier';
COMMENT ON COLUMN players.apex_puuid IS 'Encrypted PUUID from APEX API key';
COMMENT ON COLUMN players.nexus_puuid IS 'Encrypted PUUID from NEXUS API key';

-- ============================================================================
-- MATCHES TABLE - Match metadata and file paths
-- ============================================================================
CREATE TABLE matches (
    match_id VARCHAR(30) PRIMARY KEY,
    region VARCHAR(10) NOT NULL,
    
    -- COLLECTION METADATA
    collected_by VARCHAR(10) NOT NULL,  -- 'apex' or 'nexus'
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- GAME INFO
    game_version VARCHAR(20),
    game_duration INTEGER,
    game_creation BIGINT,
    patch VARCHAR(10),
    game_mode VARCHAR(20),
    
    -- FILE STORAGE PATHS
    json_path TEXT NOT NULL,
    timeline_json_path TEXT,
    
    -- METADATA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_matches_region ON matches(region);
CREATE INDEX idx_matches_patch ON matches(patch);
CREATE INDEX idx_matches_collected_by ON matches(collected_by);
CREATE INDEX idx_matches_creation ON matches(game_creation);
CREATE INDEX idx_matches_collected_at ON matches(collected_at);

COMMENT ON TABLE matches IS 'Match metadata with references to JSON files on disk';
COMMENT ON COLUMN matches.collected_by IS 'Which service collected this match (apex or nexus)';

-- ============================================================================
-- MATCH_PARTICIPANTS TABLE - Links players to matches
-- ============================================================================
CREATE TABLE match_participants (
    match_id VARCHAR(30) NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    
    -- PLAYER IDENTIFIER (uses Riot ID, not PUUID)
    region VARCHAR(10) NOT NULL,
    game_name VARCHAR(32) NOT NULL,
    tag_line VARCHAR(16) NOT NULL,
    
    -- MATCH PERFORMANCE
    participant_id INTEGER,
    champion_id INTEGER,
    champion_name VARCHAR(50),
    team_id INTEGER,
    team_position VARCHAR(20),
    won BOOLEAN,
    
    -- STATS
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    total_damage_dealt_to_champions INTEGER,
    gold_earned INTEGER,
    cs_score INTEGER,
    vision_score INTEGER,
    
    PRIMARY KEY (match_id, region, game_name, tag_line),
    FOREIGN KEY (region, game_name, tag_line) REFERENCES players(region, game_name, tag_line)
);

-- Indexes
CREATE INDEX idx_participants_player ON match_participants(region, game_name, tag_line);
CREATE INDEX idx_participants_champion ON match_participants(champion_id);
CREATE INDEX idx_participants_team ON match_participants(team_id);
CREATE INDEX idx_participants_position ON match_participants(team_position);

COMMENT ON TABLE match_participants IS 'Player performance data for each match participant';

-- ============================================================================
-- MATCH_BANS TABLE - Champion bans with pick order
-- ============================================================================
CREATE TABLE match_bans (
    match_id VARCHAR(30) NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL,
    champion_id INTEGER NOT NULL,
    pick_turn INTEGER NOT NULL,
    
    PRIMARY KEY (match_id, team_id, pick_turn)
);

CREATE INDEX idx_match_bans_champion ON match_bans(champion_id);

COMMENT ON TABLE match_bans IS 'Champion bans for each match with pick order';

-- ============================================================================
-- MATCH_LOCKS TABLE - Prevents duplicate collection
-- ============================================================================
CREATE TABLE match_locks (
    match_id VARCHAR(30) PRIMARY KEY,
    locked_by VARCHAR(10) NOT NULL,  -- 'apex' or 'nexus'
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Auto-expire after 1 hour (in case of crashes)
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour')
);

-- Index for cleanup
CREATE INDEX idx_match_locks_expires ON match_locks(expires_at);
CREATE INDEX idx_match_locks_service ON match_locks(locked_by);

COMMENT ON TABLE match_locks IS 'Coordination mechanism to prevent duplicate match collection';
COMMENT ON COLUMN match_locks.expires_at IS 'Locks auto-expire after 1 hour to recover from crashes';

-- ============================================================================
-- COLLECTION_QUEUES TABLE - Work queues for both services
-- ============================================================================
CREATE TABLE collection_queues (
    region VARCHAR(10) NOT NULL,
    game_name VARCHAR(32) NOT NULL,
    tag_line VARCHAR(16) NOT NULL,
    
    queue_type VARCHAR(10) NOT NULL,  -- 'apex' or 'nexus'
    priority INTEGER DEFAULT 5,
    next_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    
    PRIMARY KEY (region, game_name, tag_line, queue_type),
    FOREIGN KEY (region, game_name, tag_line) REFERENCES players(region, game_name, tag_line)
);

-- Indexes
CREATE INDEX idx_queue_apex ON collection_queues(queue_type, next_check) WHERE queue_type = 'apex';
CREATE INDEX idx_queue_nexus ON collection_queues(queue_type, next_check) WHERE queue_type = 'nexus';
CREATE INDEX idx_queue_priority ON collection_queues(priority DESC, next_check);

COMMENT ON TABLE collection_queues IS 'Work queues for APEX and NEXUS services';
COMMENT ON COLUMN collection_queues.priority IS 'Higher priority processed first (1-10 scale)';

-- ============================================================================
-- SYSTEM_STATUS TABLE - Coordination and monitoring
-- ============================================================================
CREATE TABLE system_status (
    service_name VARCHAR(20) PRIMARY KEY,  -- 'apex' or 'nexus'
    
    -- CURRENT STATE
    current_phase VARCHAR(50),  -- 'seeding', 'deep_collection', 'branching', 'idle'
    is_active BOOLEAN DEFAULT FALSE,
    
    -- PROGRESS TRACKING
    players_processed INTEGER DEFAULT 0,
    matches_collected INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    
    -- PERFORMANCE
    matches_per_hour FLOAT,
    average_response_time_ms FLOAT,
    
    -- TIMESTAMPS
    started_at TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_match_collected_at TIMESTAMP
);

COMMENT ON TABLE system_status IS 'Real-time status and metrics for both services';

-- Initialize both services
INSERT INTO system_status (service_name, current_phase, is_active) VALUES
    ('apex', 'idle', FALSE),
    ('nexus', 'idle', FALSE);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get players without nexus_puuid (triggers NEXUS activation)
CREATE OR REPLACE FUNCTION get_players_needing_nexus_puuid(limit_count INTEGER DEFAULT 100)
RETURNS TABLE (
    region VARCHAR(10),
    game_name VARCHAR(32),
    tag_line VARCHAR(16),
    tier VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT p.region, p.game_name, p.tag_line, p.tier
    FROM players p
    WHERE p.apex_puuid IS NOT NULL
      AND p.nexus_puuid IS NULL
      AND p.tier NOT IN ('CHALLENGER', 'GRANDMASTER')
    ORDER BY 
        CASE p.tier
            WHEN 'MASTER' THEN 1
            WHEN 'DIAMOND' THEN 2
            WHEN 'EMERALD' THEN 3
            WHEN 'PLATINUM' THEN 4
            ELSE 5
        END,
        p.league_points DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired locks
CREATE OR REPLACE FUNCTION cleanup_expired_locks()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM match_locks WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- Overall system health view
CREATE OR REPLACE VIEW system_health AS
SELECT 
    (SELECT COUNT(*) FROM players) as total_players,
    (SELECT COUNT(*) FROM players WHERE apex_puuid IS NOT NULL) as players_with_apex_puuid,
    (SELECT COUNT(*) FROM players WHERE nexus_puuid IS NOT NULL) as players_with_nexus_puuid,
    (SELECT COUNT(*) FROM matches) as total_matches,
    (SELECT COUNT(*) FROM matches WHERE collected_by = 'apex') as apex_matches,
    (SELECT COUNT(*) FROM matches WHERE collected_by = 'nexus') as nexus_matches,
    (SELECT COUNT(*) FROM match_locks) as active_locks,
    (SELECT COUNT(*) FROM collection_queues WHERE queue_type = 'apex') as apex_queue_depth,
    (SELECT COUNT(*) FROM collection_queues WHERE queue_type = 'nexus') as nexus_queue_depth;

-- Player tier distribution
CREATE OR REPLACE VIEW player_tier_distribution AS
SELECT 
    tier,
    COUNT(*) as player_count,
    COUNT(*) FILTER (WHERE apex_puuid IS NOT NULL) as with_apex_puuid,
    COUNT(*) FILTER (WHERE nexus_puuid IS NOT NULL) as with_nexus_puuid
FROM players
GROUP BY tier
ORDER BY 
    CASE tier
        WHEN 'CHALLENGER' THEN 1
        WHEN 'GRANDMASTER' THEN 2
        WHEN 'MASTER' THEN 3
        WHEN 'DIAMOND' THEN 4
        WHEN 'EMERALD' THEN 5
        WHEN 'PLATINUM' THEN 6
        WHEN 'GOLD' THEN 7
        WHEN 'SILVER' THEN 8
        WHEN 'BRONZE' THEN 9
        WHEN 'IRON' THEN 10
        ELSE 11
    END;

-- ============================================================================
-- GRANTS (adjust username as needed)
-- ============================================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_username;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Neural Nexus v3.0 Schema Created!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables: 7';
    RAISE NOTICE 'Indexes: Optimized for dual-key queries';
    RAISE NOTICE 'Functions: 2 helper functions';
    RAISE NOTICE 'Views: 2 monitoring views';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify tables: \dt';
    RAISE NOTICE '2. Check system_status: SELECT * FROM system_status;';
    RAISE NOTICE '3. View health: SELECT * FROM system_health;';
    RAISE NOTICE '========================================';
END $$;
