from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
# Using PostgreSQL (Supabase or Local)
# Ensure your DATABASE_URL is set in the .env file
# Example: postgresql+psycopg2://user:password@host:port/dbname
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise ValueError("No DATABASE_URL found in environment variables. Please check your .env file.")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
