import asyncio
from sqlalchemy.future import select
from app.core.database import async_session
from app.models.user import User
from app.core.security import hash_password

async def reset_password():
    async with async_session() as db:
        result = await db.execute(select(User).filter(User.email == 'gegira5351@daikoa.com'))
        user = result.scalars().first()
        if user:
            user.hashed_password = hash_password('truthlens123')
            await db.commit()
            print("SUCCESS")
        else:
            print("USER_NOT_FOUND")

if __name__ == "__main__":
    asyncio.run(reset_password())
