"""
Neural Nexus v3.0 - NEXUS Player Processor
Processes match participants - extracts Riot IDs, rank data, and links to players table
"""

import sys
import os
from typing import Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool
from services.shared.api.riot_client import RiotAPIClient
from database.operations.player_ops import insert_player, get_player, update_rank_data
from database.operations.match_ops import insert_participant, insert_ban
from database.operations.queue_ops import add_to_queue


class NexusPlayerProcessor:
    """Processes match participants and extracts player information using NEXUS key"""
    
    def __init__(self):
        self.api_client = RiotAPIClient('nexus')
        self.players_discovered = 0
        self.participants_processed = 0
        self.api_calls = 0
    
    def process_match_participants(self, match_data: Dict, region: str) -> Dict:
        """
        Process all 10 participants in a match
        
        Args:
            match_data: Full match data from API
            region: Region code
        
        Returns:
            Stats dict with processing results
        """
        stats = {
            'success': True,
            'participants_processed': 0,
            'players_discovered': 0,
            'api_calls': 0,
            'errors': []
        }
        
        match_id = match_data['metadata']['matchId']
        participants = match_data['info']['participants']
        
        for participant in participants:
            try:
                result = self._process_single_participant(participant, match_id, region)
                
                if result['success']:
                    stats['participants_processed'] += 1
                    if result['new_player']:
                        stats['players_discovered'] += 1
                else:
                    stats['errors'].append(result.get('error', 'Unknown error'))
                
                stats['api_calls'] += result['api_calls']
            
            except Exception as e:
                stats['errors'].append(f"Participant {participant.get('participantId', '?')}: {str(e)}")
        
        # Process bans
        if 'teams' in match_data['info']:
            for team in match_data['info']['teams']:
                if 'bans' in team:
                    for ban in team['bans']:
                        insert_ban(
                            match_id=match_id,
                            team_id=team['teamId'],
                            champion_id=ban['championId'],
                            pick_turn=ban['pickTurn']
                        )
        
        self.participants_processed += stats['participants_processed']
        self.players_discovered += stats['players_discovered']
        self.api_calls += stats['api_calls']
        
        return stats
    
    def _process_single_participant(self, participant: Dict, match_id: str, region: str) -> Dict:
        """
        Process one participant from a match (OPTIMIZED)
        
        Args:
            participant: Participant data from match
            match_id: Match ID
            region: Region code
        
        Returns:
            Result dict
        """
        result = {
            'success': False,
            'new_player': False,
            'api_calls': 0,
            'error': None
        }
        
        # Get PUUID from participant (NEXUS-encrypted)
        nexus_puuid = participant.get('puuid')
        if not nexus_puuid:
            result['error'] = 'No PUUID in participant data'
            return result
        
        # OPTIMIZATION: Check if we already have this player by PUUID
        from database.operations.player_ops import get_player_by_puuid
        
        existing_player = get_player_by_puuid(region, nexus_puuid, 'nexus')
        
        if existing_player:
            # Player already in database! Skip all API calls
            game_name = existing_player.game_name
            tag_line = existing_player.tag_line
            
            # Just insert participant and we're done
            insert_participant(
                match_id=match_id,
                region=region,
                game_name=game_name,
                tag_line=tag_line,
                participant_id=participant['participantId'],
                champion_id=participant['championId'],
                champion_name=participant['championName'],
                team_id=participant['teamId'],
                team_position=participant.get('teamPosition', 'UNKNOWN'),
                won=participant['win'],
                kills=participant['kills'],
                deaths=participant['deaths'],
                assists=participant['assists'],
                total_damage_dealt_to_champions=participant.get('totalDamageDealtToChampions', 0),
                gold_earned=participant.get('goldEarned', 0),
                cs_score=participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0),
                vision_score=participant.get('visionScore', 0)
            )
            
            result['success'] = True
            return result
        
        # Player not in DB - need to get Riot ID from API
        account_data = self.api_client.get_account_by_puuid(nexus_puuid, region)
        result['api_calls'] += 1
        
        if not account_data:
            result['error'] = 'Could not get Riot ID from PUUID'
            return result
        
        game_name = account_data.get('gameName')
        tag_line = account_data.get('tagLine')
        
        if not game_name or not tag_line:
            result['error'] = 'Missing gameName or tagLine'
            return result
        
        # Check if player exists by Riot ID (race condition with other key)
        existing_by_riot_id = get_player(region, game_name, tag_line)
        
        if existing_by_riot_id:
            # Race condition: other key just added this player
            # Update our PUUID on existing record
            from database.operations.player_ops import update_nexus_puuid
            update_nexus_puuid(region, game_name, tag_line, nexus_puuid)
            
            # Get updated rank data
            league_data = self.api_client.get_league_by_puuid(nexus_puuid, region)
            result['api_calls'] += 1
            
            if league_data:
                for entry in league_data:
                    if entry.get('queueType') == 'RANKED_SOLO_5x5':
                        update_rank_data(
                            region=region,
                            game_name=game_name,
                            tag_line=tag_line,
                            tier=entry.get('tier', 'UNRANKED'),
                            rank=entry.get('rank'),
                            league_points=entry.get('leaguePoints', 0),
                            wins=entry.get('wins', 0),
                            losses=entry.get('losses', 0),
                            league_id=entry.get('leagueId')
                        )
                        break
        
        else:
            # Truly new player - get rank and insert
            league_data = self.api_client.get_league_by_puuid(nexus_puuid, region)
            result['api_calls'] += 1
            
            tier = 'UNRANKED'
            rank = None
            league_points = 0
            wins = 0
            losses = 0
            league_id = None
            
            if league_data:
                for entry in league_data:
                    if entry.get('queueType') == 'RANKED_SOLO_5x5':
                        tier = entry.get('tier', 'UNRANKED')
                        rank = entry.get('rank')
                        league_points = entry.get('leaguePoints', 0)
                        wins = entry.get('wins', 0)
                        losses = entry.get('losses', 0)
                        league_id = entry.get('leagueId')
                        break
            
            # Insert new player
            insert_player(
                region=region,
                game_name=game_name,
                tag_line=tag_line,
                nexus_puuid=nexus_puuid,
                tier=tier,
                rank=rank,
                league_points=league_points,
                wins=wins,
                losses=losses,
                league_id=league_id,
                discovered_by='nexus',
                is_seed_player=False
            )
            
            result['new_player'] = True
            
            # Add to appropriate queue based on tier
            if tier in ['CHALLENGER', 'GRANDMASTER']:
                # High elo players discovered by NEXUS go to APEX queue
                add_to_queue(region, game_name, tag_line, 'apex', priority=8)
            else:
                # Everyone else continues network expansion in NEXUS queue
                add_to_queue(region, game_name, tag_line, 'nexus', priority=3)
        
        # Insert participant data
        insert_participant(
            match_id=match_id,
            region=region,
            game_name=game_name,
            tag_line=tag_line,
            participant_id=participant['participantId'],
            champion_id=participant['championId'],
            champion_name=participant['championName'],
            team_id=participant['teamId'],
            team_position=participant.get('teamPosition', 'UNKNOWN'),
            won=participant['win'],
            kills=participant['kills'],
            deaths=participant['deaths'],
            assists=participant['assists'],
            total_damage_dealt_to_champions=participant.get('totalDamageDealtToChampions', 0),
            gold_earned=participant.get('goldEarned', 0),
            cs_score=participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0),
            vision_score=participant.get('visionScore', 0)
        )
        
        result['success'] = True
        return result
    
    def get_stats(self) -> Dict:
        """Get processor statistics"""
        return {
            'participants_processed': self.participants_processed,
            'players_discovered': self.players_discovered,
            'api_calls': self.api_calls
        }
    
    def close(self):
        """Close API client"""
        self.api_client.close()


if __name__ == "__main__":
    # Test processor on stored matches
    print("Testing NEXUS Player Processor...")
    print("="*60)
    
    db_pool.initialize()
    
    # Get a few NEXUS matches from database that don't have participants yet
    from database.operations.match_ops import get_match
    from services.shared.storage.json_handler import json_handler
    
    import psycopg2
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/neural_nexus_v3")
    cur = conn.cursor()
    
    # Get 3 NEXUS matches without participants
    cur.execute("""
        SELECT m.match_id, m.region
        FROM matches m
        WHERE m.collected_by = 'nexus'
          AND NOT EXISTS (
            SELECT 1 FROM match_participants mp 
            WHERE mp.match_id = m.match_id
        )
        LIMIT 3
    """)
    
    matches_to_process = cur.fetchall()
    conn.close()
    
    if not matches_to_process:
        print("❌ No NEXUS matches without participants found. Run collector first!")
        db_pool.close()
        exit(1)
    
    print(f"Found {len(matches_to_process)} matches to process\n")
    
    # Create processor
    processor = NexusPlayerProcessor()
    
    for match_id, region in matches_to_process:
        print(f"\nProcessing match {match_id}...")
        
        # Load match data
        match_data = json_handler.load_match(match_id, region, 'nexus')
        
        # Process participants
        stats = processor.process_match_participants(match_data, region)
        
        print(f"  Participants processed: {stats['participants_processed']}")
        print(f"  New players discovered: {stats['players_discovered']}")
        print(f"  API calls: {stats['api_calls']}")
        if stats['errors']:
            print(f"  Errors: {len(stats['errors'])}")
    
    # Overall stats
    overall_stats = processor.get_stats()
    print(f"\n{'='*60}")
    print("Overall Stats:")
    print(f"{'='*60}")
    print(f"  Total participants: {overall_stats['participants_processed']}")
    print(f"  New players: {overall_stats['players_discovered']}")
    print(f"  API calls: {overall_stats['api_calls']}")
    
    # Check database
    from database.operations.player_ops import get_player_count
    from database.operations.queue_ops import get_queue_depth
    
    print(f"\nDatabase stats:")
    print(f"  Total players: {get_player_count()}")
    print(f"  NEXUS queue: {get_queue_depth('nexus')}")
    
    # Cleanup
    processor.close()
    db_pool.close()
    
    print("\n✅ NEXUS Player processor test complete!")