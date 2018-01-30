from thespian.actors import ActorTypeDispatcher
from . import messages as m
from datetime import timedelta
from ..models import TranscodeJob, TranscodeQueue, JobState
import os
import pickle
import logging


class JobQueue(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(JobQueue, self).__init__(*args, **kwargs)
        self.transcode_queue = self.restore_queue()
        self.exiting = False

    # Load from pickle of transcode queue to restore on boot
    def restore_queue(self):
        queue_save_path = os.path.join('/app', 'transcode_queue')
        if os.path.exists(queue_save_path):
            with open(queue_save_path, 'rb') as f:
                transcode_queue = pickle.load(f)
        else:
            transcode_queue = TranscodeQueue()
        return transcode_queue

    # Save a queue to pickle to preserve state
    def save_queue(self):
        queue_save_path = os.path.join('/app', 'transcode_queue')
        with open(queue_save_path, 'wb') as f:
            pickle.dump(self.transcode_queue, f)

    def write_queue_file(self):
        logging.debug('Attempting to save queue status to file')
        with open('/log/queue.txt', 'w+') as fp:
            fp.write(self.transcode_queue.status())
        logging.debug('Save complete')

    def receiveMsg_WakeupMessage(self, message, sender):
        logging.debug('Writing Queue File.')
        self.write_queue_file()
        if not self.exiting:
            self.wakeupAfter(timedelta(seconds=3))

    def receiveMsg_InitJobQueue(self, message, sender):
        self.restore_queue()
        logging.info('Job Queue Initialized.')
        self.wakeupAfter(timedelta(seconds=3))

    def receiveMsg_AddTranscodeJob(self, message, sender):
        self.transcode_queue.add_job(message.job)
        print(self.transcode_queue)

    def receiveMsg_StartTranscodeJob(self, message, sender):
        self.transcode_queue.make_job_ready(message.job)
        print(self.transcode_queue)

    def receiveMsg_UpdateTranscodeJob(self, message, sender):
        # if isinstance(message.job_id, tuple):
        #     logging.debug('Update job: Converting folder from tuple to string.')
        #     message.job_id = message.job_id[0]
        self.transcode_queue.update_job(message.job_id, message.state, message.progress)

    def receiveMsg_TranscodeJobRequest(self, message, sender):
        job = self.transcode_queue.start_job(message.host)
        if job:
            logging.info('Transcode of %s started on %s', job.file_name, message.host)
        self.send(sender, m.TranscodeJobResponse(job))

    def receiveMsg_TranscodeJobComplete(self, message, sender):
        if not message.failed:
            print('Completing {0}'.format(message.job.id))
            self.transcode_queue.complete_job(message.job.id)
        else:
            self.transcode_queue.fail_job(message.job)

    def receiveMsg_ActorExitRequest(self, message, sender):
        self.exiting = True
        self.save_queue()
