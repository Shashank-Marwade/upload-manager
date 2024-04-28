import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging, pysqlite3

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, '/data')
    DATABASE_PATH = os.path.join(DATABASE_DIR, os.environ.get('DATABASE'))
    logging.info(f"Database path: {DATABASE_PATH}")

    # Ensure the database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)
    engine = create_engine(f"sqlite+pysqlite:///{DATABASE_PATH}", echo=True, module=pysqlite3)
    logging.info(f"Database engine: {engine}")

    Session = sessionmaker(bind=engine)
    session = Session()
except Exception as e:
    logging.exception(f"Error occurred while connecing to db {e}")
