# scheduler.py
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import settings

sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")

jobstores = {"default": SQLAlchemyJobStore(url=sync_db_url, tablename="apscheduler_jobs")}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")

# Запуск планировщика в main.py
