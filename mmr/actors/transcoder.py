from thespian.actors import ActorTypeDispatcher
import platform
import subprocess
from datetime import timedelta
from . import messages as m
from ..models import JobState
import logging
import enum
import os

class TCState(enum.Enum):
    DISABLED = 1
    AVAILABLE = 2
    PROCESSING = 3
    RETRIEVING = 4
    TRANSCODING = 5
    SENDING = 6


class Transcoder(ActorTypeDispatcher):
    def __init__(self):
        super(Transcoder, self).__init__()
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

    def receiveMsg_Initialize(self, message, sender):
        # for addr in message.addresses.keys():
        #     self.address_book[addr] = message.addresses[addr]
        self.state = TCState.AVAILABLE
        self.queue = sender
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
            self._transcode_job()
        elif self.state == TCState.SENDING:
            os.remove(self.job.input_file)
            for folder in os.listdir('/data/incoming'):
                os.remove(folder)
            os.remove(self.job.output_file)
            for folder in os.listdir('/data/outgoing'):
                os.remove(folder)
            self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.RECEIVED, 100))
            self._complete_job()

    def receiveMsg_WakeupMessage(self, message, sender):
        self._request_job()

    def _request_job(self):
        self.send(self.queue, m.TranscodeJobRequest(self.host))

    def _retrieve_job(self):
        self.state = TCState.RETRIEVING
        self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.SENDING, 0))
        if self.job.origin_host != self.host:
            logging.debug('File not on current host. Initiating transfer.')
            self._transfer_file(self.job.origin_host, self.job.input_file, self.host, self.job.input_file)
        else:
            logging.debug('File on current host.  Initiating transcode.')
            self._transcode_job()

    def _send_job(self):
        self.state = TCState.SENDING
        self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.RECEIVING, 0))
        if self.host != self.job.dest_host:
            logging.debug('File not on current host. Initiating transfer.')
            self._transfer_file(self.host, self.job.output_file, self.job.dest_host, self.job.output_file)

        else:
            logging.debug('File on current host.  Completing job.')
            self._complete_job()

    def _complete_job(self):
        self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.RECEIVED, 100))
        logging.info('Job completed successfully.')
        self.send(self.queue, m.TranscodeJobComplete(self.job, failed=False))
        self.job = None
        self.state = TCState.AVAILABLE
        self._request_job()

    def _transcode_job(self):
        self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.SENT, 100))
        self.state = TCState.TRANSCODING

        folder = os.path.split(self.job.output_file)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)

        command = ['HandBrakeCLI',
                   '-i',
                   self.job.input_file,
                   '-o',
                   self.job.output_file,
                   '--preset=High Profile',
                   '--subtitle',
                   'scan',
                   '-F']
        logging.debug('Transcode process starting.')
        self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.TRANSCODING, 0))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            err_line = process.stderr.readline()
            if err_line == b'' and process.poll() is not None:
                break
            # logging.debug(err_line)
        rc = process.poll()
        if rc:
            logging.warning('Transcode job failed')
            # Process failed jobs here (remove local copy and send failure message
            pass
        else:
            logging.info('Transcode completed successfully.')
            self.send(self.queue, m.UpdateTranscodeJob(self.job.id, JobState.TRANSCODED, 100))
            self._send_job()

    def _transfer_file(self, source_host, source_file, dest_host, dest_file, remove_source=False):

        file_sender = self.createActor('mmr.FileSender',
                                       targetActorRequirements={'HostName': source_host})
        self.send(file_sender, m.InitFileSender(source_file))
        file_receiver = self.createActor('mmr.FileReceiver',
                                         targetActorRequirements={'HostName': dest_host})
        self.send(file_receiver, m.InitFileReceiver(dest_file, file_sender))



