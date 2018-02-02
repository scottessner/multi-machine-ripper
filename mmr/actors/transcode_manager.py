from thespian.actors import ActorTypeDispatcher
import platform
import subprocess
from datetime import timedelta
from . import messages as m
from ..models import JobState, TranscodeJob
import logging
import enum
import os
import time
import re
import shutil

class TCState(enum.Enum):
    DISABLED = 1
    AVAILABLE = 2
    PROCESSING = 3
    RETRIEVING = 4
    TRANSCODING = 5
    SENDING = 6


class TranscodeManager(ActorTypeDispatcher):
    def __init__(self):
        super(TranscodeManager, self).__init__()
        self.state = TCState.DISABLED
        self.job = None
        self.host = platform.node()
        self.address_book = dict()
        self.queue = None
        self.command = 'HandBrakeCLI -i {0} -o {1} --preset = "High Profile" --subtitle scan -F'

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        res = res and capabilities['HandBrakeCLI']
        return res

    def receiveMsg_InitTranscodeManager(self, message, sender):
        self.state = TCState.AVAILABLE
        self.queue = message.job_queue
        self._request_job()

    def receiveMsg_TranscodeJobResponse(self, message, sender):
        if message.job:
            self.job = message.job
            self.state = TCState.PROCESSING
            logging.info('New job received. Beginning to process')
            self._retrieve_job()
        else:
            self.wakeupAfter(timedelta(seconds=5))

    def receiveMsg_FileTransferComplete(self, message, sender):
        if self.state == TCState.RETRIEVING:
            self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id, state=JobState.SENT, progress=100))
            self._transcode_job()
        elif self.state == TCState.SENDING:
            print('Removing from {0}: {1}'.format(self.host, self.job.input_file))
            for folder in os.listdir('/data/incoming'):
                shutil.rmtree(os.path.join('/data/incoming/', folder))
            print('Removing from {0}: {1}'.format(self.host, self.job.output_file))
            for folder in os.listdir('/data/outgoing'):
                shutil.rmtree(os.path.join('/data/outgoing/', folder))
            self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id, state=JobState.RECEIVED, progress=100))
            self._complete_job()

    def receiveMsg_FileTranscodeComplete(self, message, sender):
        if message.return_code != 0:
            logging.warning('Transcode job failed')
            # Process failed jobs here (remove local copy and send failure message
            pass
        else:
            logging.info('Transcode completed successfully.')
            size = os.path.getsize(self.job.output_file)
            self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id,
                                                       state=JobState.TRANSCODED,
                                                       progress=100,
                                                       size=size))
            self._send_job()

    def receiveMsg_WakeupMessage(self, message, sender):
        self._request_job()

    def _request_job(self):
        self.send(self.queue, m.TranscodeJobRequest(self.host))

    def _retrieve_job(self):
        self.state = TCState.RETRIEVING
        if self.job.origin_host != self.host:
            logging.debug('File not on current host. Initiating transfer.')
            self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id, state=JobState.SENDING, progress=0))
            self._transfer_file(JobState.SENDING, self.job.origin_host, self.job.input_file, self.host, self.job.input_file)
        else:
            logging.debug('File on current host.  Initiating transcode.')
            self._transcode_job()

    def _send_job(self):
        self.state = TCState.SENDING
        if self.host != self.job.dest_host:
            logging.debug('File not on current host. Initiating transfer.')
            self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id, state=JobState.RECEIVING, progress=0))
            self._transfer_file(JobState.RECEIVING, self.host, self.job.output_file, self.job.dest_host, self.job.output_file)

        else:
            logging.debug('File on current host.  Completing job.')
            self._complete_job()

    def _complete_job(self):
        self.send(self.queue, m.UpdateTranscodeJob(job_id=self.job.id, state=JobState.RECEIVED, progress=100))
        logging.info('Job completed successfully.')
        self.send(self.queue, m.TranscodeJobComplete(self.job, failed=False))
        self.job = None
        self.state = TCState.AVAILABLE
        self._request_job()

    def _transcode_job(self):
        logging.debug('Ready to start transcoding.')
        self.state = TCState.TRANSCODING
        transcoder = self.createActor('mmr.Transcoder',
                                      targetActorRequirements={'HostName': self.host})
        self.send(transcoder, m.InitTranscoder(self.job, self.queue))

    def _transfer_file(self, job_state, source_host, source_file, dest_host, dest_file, remove_source=False):

        file_sender = self.createActor('mmr.FileSender',
                                       targetActorRequirements={'HostName': source_host})
        self.send(file_sender, m.InitFileSender(self.job.id, job_state, source_file, self.queue))
        file_receiver = self.createActor('mmr.FileReceiver',
                                         targetActorRequirements={'HostName': dest_host})
        self.send(file_receiver, m.InitFileReceiver(self.job.id, job_state, dest_file, file_sender, self.queue))


