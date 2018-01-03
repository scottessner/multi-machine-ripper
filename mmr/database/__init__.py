from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from ..config import config

engine = create_engine(config['DATABASE_PATH'])
Base = declarative_base()


from .database import TranscodeJob
