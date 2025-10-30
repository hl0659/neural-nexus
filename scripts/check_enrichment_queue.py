import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool

def main():
    print("📋 Enrichment Queue Check\n")
    
    db_pool.initialize()
    
    with db_pool.get_cursor() as cursor:
        # Total players needing enrichment
        cursor.execute("SELECT COUNT(*) as count FROM enrichment_queue")
        queue_count = cursor.fetchone()['count']
        print(f"Total in Enrichment Queue: {queue_count}")
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM enrichment_queue
            GROUP BY status
        """)
        print("\nBy Status:")
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")
        
        # Sample entries
        cursor.execute("""
            SELECT eq.puuid, p.region, p.tier, 
                   eq.needs_summoner_id, eq.needs_rank, eq.needs_riot_id
            FROM enrichment_queue eq
            JOIN players p ON eq.puuid = p.puuid
            LIMIT 10
        """)
        print("\nSample Queue Entries:")
        for row in cursor.fetchall():
            print(f"  {row['region'].upper()} - {row['tier']} - needs: "
                  f"summoner_id={row['needs_summoner_id']}, "
                  f"rank={row['needs_rank']}, "
                  f"riot_id={row['needs_riot_id']}")
    
    db_pool.close()
    print("\n✅ Queue check complete")

if __name__ == "__main__":
    main()