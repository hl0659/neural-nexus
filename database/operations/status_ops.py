"""
Neural Nexus v3.0 - System Status Database Operations
Manages system_status table for service monitoring and coordination
"""

from typing import Optional, Dict, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database.connection import db_pool


def update_service_status(
    service_name: str,
    current_phase: Optional[str] = None,
    is_active: Optional[bool] = None,
    players_processed: Optional[int] = None,
    matches_collected: Optional[int] = None,
    api_calls_made: Optional[int] = None,
    errors_encountered: Optional[int] = None,
    matches_per_hour: Optional[float] = None,
    average_response_time_ms: Optional[float] = None
) -> bool:
    """
    Update service status
    
    Args:
        service_name: 'apex' or 'nexus'
        current_phase: Current operation phase
        is_active: Whether service is running
        players_processed: Increment to player count
        matches_collected: Increment to match count
        api_calls_made: Increment to API call count
        errors_encountered: Increment to error count
        matches_per_hour: Current throughput rate
        average_response_time_ms: Average API response time
    
    Returns:
        True if updated successfully
    """
    try:
        with db_pool.get_cursor() as cursor:
            # Build dynamic UPDATE query
            updates = ["last_update = CURRENT_TIMESTAMP"]
            params = []
            
            if current_phase is not None:
                updates.append("current_phase = %s")
                params.append(current_phase)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
                if is_active and "started_at IS NULL":
                    updates.append("started_at = CURRENT_TIMESTAMP")
            
            if players_processed is not None:
                updates.append("players_processed = players_processed + %s")
                params.append(players_processed)
            
            if matches_collected is not None:
                updates.append("matches_collected = matches_collected + %s")
                updates.append("last_match_collected_at = CURRENT_TIMESTAMP")
                params.append(matches_collected)
            
            if api_calls_made is not None:
                updates.append("api_calls_made = api_calls_made + %s")
                params.append(api_calls_made)
            
            if errors_encountered is not None:
                updates.append("errors_encountered = errors_encountered + %s")
                params.append(errors_encountered)
            
            if matches_per_hour is not None:
                updates.append("matches_per_hour = %s")
                params.append(matches_per_hour)
            
            if average_response_time_ms is not None:
                updates.append("average_response_time_ms = %s")
                params.append(average_response_time_ms)
            
            params.append(service_name)
            
            query = f"""
                UPDATE system_status
                SET {', '.join(updates)}
                WHERE service_name = %s
            """
            
            cursor.execute(query, params)
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to update {service_name} status: {e}")
        return False


def get_service_status(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get status for a specific service
    
    Args:
        service_name: 'apex' or 'nexus'
    
    Returns:
        Status dict or None
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM system_status
                WHERE service_name = %s
            """, (service_name,))
            
            return cursor.fetchone()
    
    except Exception as e:
        print(f"❌ Failed to get {service_name} status: {e}")
        return None


def get_all_service_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status for all services
    
    Returns:
        Dict with 'apex' and 'nexus' status
    """
    try:
        with db_pool.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM system_status")
            
            statuses = {}
            for row in cursor.fetchall():
                statuses[row['service_name']] = dict(row)
            
            return statuses
    
    except Exception as e:
        print(f"❌ Failed to get all service status: {e}")
        return {}


def reset_service_status(service_name: str) -> bool:
    """
    Reset service status to initial state
    
    Args:
        service_name: 'apex' or 'nexus'
    
    Returns:
        True if reset successfully
    """
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE system_status
                SET current_phase = 'idle',
                    is_active = FALSE,
                    players_processed = 0,
                    matches_collected = 0,
                    api_calls_made = 0,
                    errors_encountered = 0,
                    matches_per_hour = NULL,
                    average_response_time_ms = NULL,
                    started_at = NULL,
                    last_update = CURRENT_TIMESTAMP,
                    last_match_collected_at = NULL
                WHERE service_name = %s
            """, (service_name,))
            
            return cursor.rowcount > 0
    
    except Exception as e:
        print(f"❌ Failed to reset {service_name} status: {e}")
        return False


def mark_service_active(service_name: str, phase: str = 'running') -> bool:
    """Mark service as active"""
    return update_service_status(
        service_name=service_name,
        is_active=True,
        current_phase=phase
    )


def mark_service_inactive(service_name: str) -> bool:
    """Mark service as inactive"""
    return update_service_status(
        service_name=service_name,
        is_active=False,
        current_phase='idle'
    )


def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health metrics
    
    Returns:
        Dict with combined metrics from both services
    """
    try:
        statuses = get_all_service_status()
        
        total_players = sum(s.get('players_processed', 0) for s in statuses.values())
        total_matches = sum(s.get('matches_collected', 0) for s in statuses.values())
        total_api_calls = sum(s.get('api_calls_made', 0) for s in statuses.values())
        total_errors = sum(s.get('errors_encountered', 0) for s in statuses.values())
        
        apex_active = statuses.get('apex', {}).get('is_active', False)
        nexus_active = statuses.get('nexus', {}).get('is_active', False)
        
        return {
            'apex_status': statuses.get('apex', {}),
            'nexus_status': statuses.get('nexus', {}),
            'total_players_processed': total_players,
            'total_matches_collected': total_matches,
            'total_api_calls': total_api_calls,
            'total_errors': total_errors,
            'services_active': apex_active or nexus_active,
            'both_services_active': apex_active and nexus_active
        }
    
    except Exception as e:
        print(f"❌ Failed to get system health: {e}")
        return {}


if __name__ == "__main__":
    # Test status operations
    print("Testing Status Operations...")
    print("="*60)
    
    db_pool.initialize()
    
    # Test 1: Get initial status
    print("\nTest 1: Getting APEX status...")
    status = get_service_status('apex')
    if status:
        print(f"✅ APEX Status:")
        print(f"   Phase: {status['current_phase']}")
        print(f"   Active: {status['is_active']}")
        print(f"   Players: {status['players_processed']}")
        print(f"   Matches: {status['matches_collected']}")
    
    # Test 2: Mark service active
    print("\nTest 2: Marking APEX as active...")
    success = mark_service_active('apex', 'testing')
    print(f"{'✅' if success else '❌'} Mark active: {success}")
    
    # Test 3: Update metrics
    print("\nTest 3: Updating APEX metrics...")
    success = update_service_status(
        service_name='apex',
        players_processed=10,
        matches_collected=50,
        api_calls_made=100,
        matches_per_hour=1500.5
    )
    print(f"{'✅' if success else '❌'} Update metrics: {success}")
    
    # Test 4: Get updated status
    print("\nTest 4: Getting updated APEX status...")
    status = get_service_status('apex')
    if status:
        print(f"✅ Updated APEX Status:")
        print(f"   Phase: {status['current_phase']}")
        print(f"   Active: {status['is_active']}")
        print(f"   Players: {status['players_processed']}")
        print(f"   Matches: {status['matches_collected']}")
        print(f"   API Calls: {status['api_calls_made']}")
        print(f"   Rate: {status['matches_per_hour']} matches/hour")
    
    # Test 5: Get all service status
    print("\nTest 5: Getting all service status...")
    statuses = get_all_service_status()
    print(f"✅ Found {len(statuses)} services")
    for name, status in statuses.items():
        print(f"   {name.upper()}: {status['current_phase']} ({'Active' if status['is_active'] else 'Inactive'})")
    
    # Test 6: Get system health
    print("\nTest 6: Getting system health...")
    health = get_system_health()
    print(f"✅ System Health:")
    print(f"   Total Players: {health['total_players_processed']}")
    print(f"   Total Matches: {health['total_matches_collected']}")
    print(f"   Total API Calls: {health['total_api_calls']}")
    print(f"   Services Active: {health['services_active']}")
    
    # Test 7: Mark service inactive
    print("\nTest 7: Marking APEX as inactive...")
    success = mark_service_inactive('apex')
    print(f"{'✅' if success else '❌'} Mark inactive: {success}")
    
    # Test 8: Reset service
    print("\nTest 8: Resetting APEX status...")
    success = reset_service_status('apex')
    print(f"{'✅' if success else '❌'} Reset status: {success}")
    
    # Verify reset
    status = get_service_status('apex')
    if status:
        print(f"   Verified - Players: {status['players_processed']}, Matches: {status['matches_collected']}")
    
    db_pool.close()
    
    print("\n✅ Status operations tests complete!")