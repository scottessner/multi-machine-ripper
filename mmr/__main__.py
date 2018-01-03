from mmr import database


engine = create_engine('sqlite:///mmr.db')
Base = declarative_base()

job = TranscodeJob(path='/dev/d')

session = Session()

session.add(job)
session.commit()