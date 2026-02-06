from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json

# #region agent log
try:
    os.makedirs('/app/.cursor', exist_ok=True)
    with open('/app/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"db.py:5","message":"Reading environment variables","data":{"POSTGRES_USER":os.getenv("POSTGRES_USER"),"POSTGRES_DB":os.getenv("POSTGRES_DB"),"POSTGRES_HOST":os.getenv("POSTGRES_HOST"),"POSTGRES_PORT":os.getenv("POSTGRES_PORT")},"timestamp":int(__import__('time').time()*1000)})+'\n')
except: pass
# #endregion

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

# #region agent log
try:
    with open('/app/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"db.py:15","message":"Environment variables after reading","data":{"DB_USER":DB_USER,"DB_NAME":DB_NAME,"DB_HOST":DB_HOST,"DB_PORT":DB_PORT,"DB_PASS":"***" if DB_PASS else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
except: pass
# #endregion

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# #region agent log
try:
    with open('/app/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"db.py:18","message":"DATABASE_URL constructed","data":{"DATABASE_URL":DATABASE_URL.replace(DB_PASS or "","***") if DB_PASS else DATABASE_URL},"timestamp":int(__import__('time').time()*1000)})+'\n')
except: pass
# #endregion

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
