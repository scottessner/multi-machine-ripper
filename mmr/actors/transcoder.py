from thespian.actors import ActorTypeDispatcher
import os
import subprocess
from datetime import timedelta
import re
from ..models import JobState, TranscodeJob
from . import messages as m
import logging


class Transcoder(ActorTypeDispatcher):
    def __init__(self):
        super(Transcoder, self).__init__()
        self.manager = None
        self.job_queue = None
        self.job = None
        self.command = 'HandBrakeCLI -i {0} -o {1} --preset = "High Profile" --subtitle scan -F'
        self.process = None
        self.progress_regex = re.compile('Encoding:.* (?P<progress>\d{0,2})(.\d{2} %)')
        self.progress = 0

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        return res

    def receiveMsg_InitTranscoder(self, message, sender):
        logging.info('Starting Transcode of {0}'.format(message.job.relative_file))
        self.job = message.job
        self.manager = sender
        self.job_queue = message.job_queue

        folder = os.path.split(self.job.output_file)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
            folder = os.path.split(self.job.output_file)[0]

        command = ['HandBrakeCLI',
                   '-i',
                   self.job.input_file,
                   '-o',
                   self.job.output_file,
                   '--preset=High Profile',
                   '--subtitle',
                   'scan',
                   '-F']

        self.process = subprocess.Popen(command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        self.wakeupAfter(timedelta(seconds=0.1))

    def receiveMsg_WakeupMessage(self, message, sender):
        # Pull a line off stdout searching for carriage return
        # HandBrakeCLI overwrites the same line repeatedly
        # logging.debug('Reading next line from Handbrake.')
        line = ''
        while line[-1:] != '\r' and self.process.poll() is None:
            line = line + bytes.decode(self.process.stdout.read(1))

        progress = self._find_transcode_progress(line)
        if progress != self.progress:
            self.progress = progress
            self.send(self.job_queue, m.UpdateTranscodeJob(self.job.id, JobState.TRANSCODING, progress=progress))

        if self.process.poll() is not None:
            logging.debug('Transcoder completed with return code %s', self.process.poll())
            self.send(self.manager, m.FileTranscodeComplete(self.process.poll()))
        else:
            self.wakeupAfter(timedelta(seconds=0.1))

    def _find_transcode_progress(self, line):
        result = self.progress_regex.match(line)
        progress = None
        if result is not None:
            progress = result.groupdict().get('progress', None)
        return progress
