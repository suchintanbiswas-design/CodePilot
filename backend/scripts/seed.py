import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import async_session_maker
from app.config.settings import settings
from app.models.language import Language
from app.models.settings import UserSettings
from app.models.user import User
from app.utils.security import hash_password


async def seed_admin(db: AsyncSession):
    stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        print(f"Creating admin user {settings.ADMIN_EMAIL}...")
        admin = User(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            full_name="System Admin",
        )
        db.add(admin)
        await db.flush()

        settings_record = UserSettings(user_id=admin.id)
        db.add(settings_record)
        await db.commit()
    else:
        print("Admin user already exists.")


async def seed_languages(db: AsyncSession):
    langs = [
        {"name": "Python", "extension": ".py", "icon": "python-icon"},
        {"name": "Java", "extension": ".java", "icon": "java-icon"},
        {"name": "C", "extension": ".c", "icon": "c-icon"},
        {"name": "C++", "extension": ".cpp", "icon": "cpp-icon"},
        {"name": "JavaScript", "extension": ".js", "icon": "js-icon"},
        {"name": "TypeScript", "extension": ".ts", "icon": "ts-icon"},
    ]

    for lang_data in langs:
        stmt = select(Language).where(Language.name == lang_data["name"])
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            print(f"Adding language {lang_data['name']}...")
            lang = Language(**lang_data)
            db.add(lang)

    await db.commit()


async def run_seed():
    async with async_session_maker() as session:
        await seed_admin(session)
        await seed_languages(session)
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(run_seed())
