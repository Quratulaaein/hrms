from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = "postgresql://postgres.eiejdgqjxpvshrpfjjju:%40biVMj2z%40t6Wszy@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
