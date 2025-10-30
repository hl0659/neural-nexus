"""
Neural Nexus v3.0 - Queue Database Operations
Manages collection queues for APEX and NEXUS services
"""

from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool
from services.shared.models.player import Player


def add_to_queue(
    region: str,
    game_name: str,
    tag_line: str,
    queue_type: str,
    priority: int = 5
) -> bool:
    """
    Add a player to a collection queue
    
    Args:
        region: Player region
        game_name: Player game name
        tag_line: Player tag line
        queue_type: 'apex' or 'nexus'
        priority: Priority level (1-10, higher = more important)
    
    Returns:
        True if added, False if already in queue
    """
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO collection_queues (
                    region, game_name, tag_line, queue_type, priority
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (region, game_name, tag_line, queue_type) DO NOTHING
                RETURNING region
            """, (region, game_name, tag_line, queue_type, priority))
            
            return cursor.fetchone() is not None
    
    except Exception as e:
        print(f"❌ Failed to add to {queue_type} queue: {e}")
        return False


def get_next_from_queue(queue_type: str, limit: int = 1) -> List[Player]:
    """
    Get next players to process from queue
    
    Args:
        queue_type: 'apex' or 'nexus'
        limit: Number of players to retrieve
    
    Returns:
        List of Player objects ready for processing
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT p.* 
                FROM collection_queues q
                JOIN players p ON (
                    q.region = p.region AND 
                    q.game_name = p.game_name AND 
                    q.tag_line = p.tag_line
                )
                WHERE q.queue_type = %s
                  AND q.next_check <= CURRENT_TIMESTAMP
                  AND q.status = 'pending'
                ORDER BY q.priority DESC, q.next_check ASC
                LIMIT %s
            """, (queue_type, limit))
            
            return [Player(**row) for row in cursor.fetchall()]
    
    except Exception as e:
        print(f"❌ Failed to get from {queue_type} queue: {e}")
        return []


def mark_queue_processing(region: str, game_name: str, tag_line: str, queue_type: str) -> bool:
    """Mark a queue entry as being processed"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE collection_queues
                SET status = 'processing',
                    last_attempt = CURRENT_TIMESTAMP
                WHERE region = %s AND game_name = %s AND tag_line = %s
                  AND queue_type = %s
            """, (region, game_name, tag_line, queue_type))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to mark processing: {e}")
        return False


def mark_queue_complete(region: str, game_name: str, tag_line: str, queue_type: str) -> bool:
    """Mark a queue entry as completed and schedule next check"""
    try:
        with db_pool.get_cursor() as cursor:
            # Schedule next check in 24 hours
            cursor.execute("""
                UPDATE collection_queues
                SET status = 'pending',
                    next_check = CURRENT_TIMESTAMP + INTERVAL '24 hours',
                    attempts = 0,
                    last_error = NULL
                WHERE region = %s AND game_name = %s AND tag_line = %s
                  AND queue_type = %s
            """, (region, game_name, tag_line, queue_type))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to mark complete: {e}")
        return False


def mark_queue_error(
    region: str,
    game_name: str,
    tag_line: str,
    queue_type: str,
    error_message: str
) -> bool:
    """Mark a queue entry as failed with error"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE collection_queues
                SET status = 'pending',
                    attempts = attempts + 1,
                    next_check = CURRENT_TIMESTAMP + INTERVAL '1 hour',
                    last_error = %s
                WHERE region = %s AND game_name = %s AND tag_line = %s
                  AND queue_type = %s
            """, (error_message, region, game_name, tag_line, queue_type))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to mark error: {e}")
        return False


def remove_from_queue(region: str, game_name: str, tag_line: str, queue_type: str) -> bool:
    """Remove a player from queue"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM collection_queues
                WHERE region = %s AND game_name = %s AND tag_line = %s
                  AND queue_type = %s
            """, (region, game_name, tag_line, queue_type))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to remove from queue: {e}")
        return False


def get_queue_depth(queue_type: str) -> int:
    """Get number of pending items in queue"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM collection_queues
                WHERE queue_type = %s AND status = 'pending'
            """, (queue_type,))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    except Exception as e:
        print(f"❌ Failed to get queue depth: {e}")
        return 0


def get_queue_stats(queue_type: str) -> dict:
    """Get comprehensive queue statistics"""
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            # Total items
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE attempts > 3) as failed
                FROM collection_queues
                WHERE queue_type = %s
            """, (queue_type,))
            
            result = cursor.fetchone()
            
            return {
                'queue_type': queue_type,
                'total': result['total'] if result else 0,
                'pending': result['pending'] if result else 0,
                'processing': result['processing'] if result else 0,
                'failed': result['failed'] if result else 0
            }
    
    except Exception as e:
        print(f"❌ Failed to get queue stats: {e}")
        return {'queue_type': queue_type, 'total': 0, 'pending': 0, 'processing': 0, 'failed': 0}


def cleanup_stuck_processing(queue_type: str, timeout_minutes: int = 30) -> int:
    """
    Reset stuck 'processing' entries back to 'pending'
    
    Args:
        queue_type: 'apex' or 'nexus'
        timeout_minutes: How long before considering stuck
    
    Returns:
        Number of entries reset
    """
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE collection_queues
                SET status = 'pending',
                    next_check = CURRENT_TIMESTAMP
                WHERE queue_type = %s
                  AND status = 'processing'
                  AND last_attempt < CURRENT_TIMESTAMP - INTERVAL '%s minutes'
            """, (queue_type, timeout_minutes))
            
            return cursor.rowcount
    
    except Exception as e:
        print(f"❌ Failed to cleanup stuck entries: {e}")
        return 0


if __name__ == "__main__":
    # Test queue operations
    print("Testing Queue Operations...")
    print("="*60)
    
    db_pool.initialize()
    
    # First, create a test player
    from database.operations.player_ops import insert_player
    
    insert_player(
        region='na1',
        game_name='QueueTest',
        tag_line='TEST',
        apex_puuid='test-puuid',
        tier='DIAMOND'
    )
    
    # Test 1: Add to APEX queue
    print("\nTest 1: Adding to APEX queue...")
    success = add_to_queue('na1', 'QueueTest', 'TEST', 'apex', priority=8)
    print(f"{'✅' if success else '❌'} Add to queue: {success}")
    
    # Test 2: Get queue depth
    print("\nTest 2: Getting queue depth...")
    depth = get_queue_depth('apex')
    print(f"✅ APEX queue depth: {depth}")
    
    # Test 3: Get next from queue
    print("\nTest 3: Getting next from queue...")
    players = get_next_from_queue('apex', limit=1)
    print(f"✅ Retrieved {len(players)} player(s)")
    if players:
        print(f"   Player: {players[0]}")
    
    # Test 4: Mark as processing
    print("\nTest 4: Marking as processing...")
    success = mark_queue_processing('na1', 'QueueTest', 'TEST', 'apex')
    print(f"{'✅' if success else '❌'} Mark processing: {success}")
    
    # Test 5: Get queue stats
    print("\nTest 5: Getting queue stats...")
    stats = get_queue_stats('apex')
    print(f"✅ Queue stats:")
    print(f"   Total: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Processing: {stats['processing']}")
    print(f"   Failed: {stats['failed']}")
    
    # Test 6: Mark as complete
    print("\nTest 6: Marking as complete...")
    success = mark_queue_complete('na1', 'QueueTest', 'TEST', 'apex')
    print(f"{'✅' if success else '❌'} Mark complete: {success}")
    
    # Test 7: Mark as error
    print("\nTest 7: Marking as error...")
    success = mark_queue_error('na1', 'QueueTest', 'TEST', 'apex', 'Test error message')
    print(f"{'✅' if success else '❌'} Mark error: {success}")
    
    # Test 8: Remove from queue
    print("\nTest 8: Removing from queue...")
    success = remove_from_queue('na1', 'QueueTest', 'TEST', 'apex')
    print(f"{'✅' if success else '❌'} Remove from queue: {success}")
    
    # Cleanup
    print("\nCleaning up test data...")
    with db_pool.get_cursor() as cursor:
        cursor.execute("DELETE FROM collection_queues WHERE game_name = 'QueueTest'")
        cursor.execute("DELETE FROM players WHERE game_name = 'QueueTest'")
    
    db_pool.close()
    
    print("\n✅ Queue operations tests complete!")