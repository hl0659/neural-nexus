"""
Neural Nexus v3.0 - Project Structure Generator
Creates the complete directory structure and initial files for the v3.0 rebuild
"""

import os
from pathlib import Path

def create_structure():
    """Create complete v3.0 directory structure"""
    
    base = Path(".")
    
    # Directory structure
    dirs = [
        # Services - APEX
        "services/apex",
        
        # Services - NEXUS  
        "services/nexus",
        
        # Services - Shared
        "services/shared/api",
        "services/shared/storage",
        "services/shared/models",
        
        # Database
        "database/migrations",
        "database/operations",
        
        # Shared (root level)
        "shared/config",
        "shared/database",
        
        # Scripts
        "scripts",
        
        # Tests
        "tests/apex",
        "tests/nexus",
        "tests/shared",
    ]
    
    print("Creating directory structure...")
    for dir_path in dirs:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py for Python packages
        if not dir_path.startswith("scripts") and not dir_path.startswith("tests") and not dir_path.startswith("database"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Package initialization"""\n')
        
        print(f"  ✓ {dir_path}")
    
    print("\nDirectory structure created!")
    print("\nNext steps:")
    print("1. Create .env file with your API keys")
    print("2. Create database schema (schema_v3.sql)")
    print("3. Create requirements.txt")
    print("4. Initialize database")
    print("5. Build APEX service")
    print("6. Build NEXUS service")

if __name__ == "__main__":
    create_structure()
