import psycopg # type: ignore
from shared.config.settings import settings

try:
    # Connect to database
    conn = psycopg.connect(settings.DATABASE_URL)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    
    print("✅ Database connection successful!")
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")