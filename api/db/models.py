from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    cam_id = Column(String(50), index=True)
    event_type = Column(String(100), index=True)
    path = Column(String(255))
    timestamp = Column(DateTime, default=datetime.datetime.now)

class ScreenshotForTrain(Base):
    __tablename__ = "screenshots_for_train"

    id = Column(Integer, primary_key=True, index=True)
    cam_id = Column(String(50), index=True)
    event_type = Column(String(100), index=True)
    path = Column(String(255))
    timestamp = Column(DateTime, default=datetime.datetime.now)