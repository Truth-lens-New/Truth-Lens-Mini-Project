
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from sqlalchemy import text
from app.core.database import engine

async def migrate():
    print("Starting migration...")
    async with engine.begin() as conn:
        # Check if columns exist
        print("Checking columns...")
        
        # Add full_name
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
            print("Added full_name column")
        except Exception as e:
            if "duplicate column" in str(e):
                print("full_name column already exists")
            else:
                print(f"Error adding full_name: {e}")

        # Add avatar_url
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))
            print("Added avatar_url column")
        except Exception as e:
            if "duplicate column" in str(e):
                print("avatar_url column already exists")
            else:
                print(f"Error adding avatar_url: {e}")

        # Add preferences
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN preferences JSON DEFAULT '{}'"))
            print("Added preferences column")
        except Exception as e:
            if "duplicate column" in str(e):
                print("preferences column already exists")
            else:
                print(f"Error adding preferences: {e}")
                
    print("Migration complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate())
