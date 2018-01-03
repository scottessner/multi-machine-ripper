from sqlalchemy import Column, Integer, String


from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..database import

class TranscodeJob(Base):
    __tablename__ = 'transcode_jobs'

    id = Column(Integer, primary_key=True)
    path = Column(String)
    worker_node = Column(String)

Base.metadata.create_all(bind=engine)
Session = sessionmaker()
Session.configure(bind=engine)



        #          path=None,
        #          args=None,
        #          worker=None,
        #          time_created=None,
        #          time_started=None,
        #          time_finished=None,
        #          status='NEW'):
        # self.path = path
        # self.args = args
        # self.worker = worker
        # self.time_created = time_created
        # self.time_started = time_started
        # self.time_finished = time_finished
        # self.status = status




