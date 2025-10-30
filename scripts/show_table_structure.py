"""
Neural Nexus v3.0 - Show Table Structure
Displays the structure of database tables
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database.connection import db_pool


def show_table_structure(table_name: str):
    """Show structure of a specific table"""
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")
    
    with db_pool.get_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, (table_name,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print(f"Table '{table_name}' not found!")
            return
        
        # Print header
        print(f"{'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<30}")
        print("-" * 80)
        
        # Print columns
        for row in rows:
            col_name = row['column_name']
            
            # Build type string
            data_type = row['data_type']
            if row['character_maximum_length']:
                data_type += f"({row['character_maximum_length']})"
            
            nullable = 'YES' if row['is_nullable'] == 'YES' else 'NO'
            default = row['column_default'] or ''
            if len(default) > 30:
                default = default[:27] + '...'
            
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default:<30}")


if __name__ == "__main__":
    db_pool.initialize()
    
    # Show all important tables
    tables = [
        'players',
        'matches',
        'match_participants',
        'collection_queues',
        'match_locks',
        'system_status'
    ]
    
    for table in tables:
        show_table_structure(table)
    
    db_pool.close()