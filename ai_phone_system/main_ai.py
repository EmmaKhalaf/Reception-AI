from fastapi import FastAPI
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Database Setup
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------------
# User Table
# -------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# -------------------------
# FastAPI App
# -------------------------

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}