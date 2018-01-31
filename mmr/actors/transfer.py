from thespian.actors import ActorTypeDispatcher, ActorExitRequest
from . import messages as m
import logging
import platform
import os
import time


class FileSender(ActorTypeDispatcher):
    def __init__(self):
        self.receiver = None
        self.manager = None
        self.job_queue = None
        self.job_id = None
        self.job_state = None
        self.path = None
        self.length = None
        self.host = platform.node()
        self.fp = None

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        return res

    def receiveMsg_InitFileSender(self, message, sender):
        self.manager = sender
        self.job_queue = message.job_queue
        self.job_id = message.job_id
        self.job_state = message.job_state
        self.path = message.file
        self.length = os.path.getsize(self.path)
        self.fp = open(self.path, 'rb')
        logging.info('Preparing to send %s from %s.',
                     self.path,
                     self.host)

    def receiveMsg_SendChunk(self, message, sender):
        # self.send()
        if message.offset == self.fp.tell():
            self.fp.seek(message.offset, 0)
        data = self.fp.read(4194000)
        eof = True if len(data) < 4194000 else False
        self.send(sender, m.Chunk(data, self.length, message.offset, eof))
        #logging.debug('Chunk %s sent', str(offset/4194000))

    def receiveMsg_ActorExitRequest(self, message, sender):
        self.fp.close()
        # os.remove(self.path)
        self.enabled = False


class FileReceiver(ActorTypeDispatcher):
    def __init__(self):
        self.manager = None
        self.file_sender = None
        self.job_queue = None
        self.job_id = None
        self.job_state = None
        self.path = None
        self.host = platform.node()
        self.fp = None
        self.length = None
        self.progress = None

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        return res

    def receiveMsg_InitFileReceiver(self, message, sender):
        self.manager = sender
        self.file_sender = message.source_address
        self.job_queue = message.job_queue
        self.job_id = message.job_id
        self.job_state = message.job_state
        self.path = message.file
        folder = os.path.split(self.path)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.fp = open(self.path, 'wb')
        logging.info('Preparing to receive %s on %s.',
                     self.path,
                     self.host)
        time.sleep(5)
        self.send(self.file_sender, m.SendChunk(0))

    def receiveMsg_Chunk(self, message, sender):
        self.length = message.length
        if message.offset == self.fp.tell():
            self.fp.write(message.data)
            if not message.eof:
                progress = self.fp.tell()*100//self.length
                if progress != self.progress:
                    self.send(self.job_queue, m.UpdateTranscodeJob(self.job_id, self.job_state, progress))
                    self.progress = progress
                self.send(self.file_sender, m.SendChunk(self.fp.tell()))
            else:
                logging.debug('Entire file received.')
                self.fp.close()
                self.send(self.manager, m.FileTransferComplete())
                self.send(self.file_sender, ActorExitRequest())
                self.send(self.myAddress, ActorExitRequest())


    def receiveMsg_ActorExitRequest(self, message, sender):
        self.enabled = False