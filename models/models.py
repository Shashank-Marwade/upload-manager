from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AWSCred(Base):
    __tablename__ = 'aws_secreats'
    
    id = Column(Integer, primary_key=True)
    access_key = Column(String)
    secret_key = Column(String)

class UploadMon(Base):
    __tablename__ = 'upload_monitor'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    path = Column(String)
    update_date_time = Column(String)

