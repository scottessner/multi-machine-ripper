from thespian.actors import ActorTypeDispatcher, ActorExitRequest
from . import messages as m
import logging
import platform
import os
import time


class FileSender(ActorTypeDispatcher):
    def __init__(self):
        self.coordinator = None
        self.receiver = None
        self.transcoder = None
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
        self.transcoder = sender
        self.path = message.file
        self.length = os.path.getsize(self.path)
        self.fp = open(self.path, 'rb')
        logging.info('Preparing to send %s from %s.',
                     self.path,
                     self.host)

    def receiveMsg_SendNextChunk(self, message, sender):
        self.send()
        data = self.fp.read(4194000)
        eof = True if len(data) < 4194000 else False
        self.send(sender, m.Chunk(data, eof))
        #logging.debug('Chunk %s sent', str(offset/4194000))

    def receiveMsg_ActorExitRequest(self, message, sender):
        self.fp.close()
        os.remove(self.path)
        self.enabled = False


class FileReceiver(ActorTypeDispatcher):
    def __init__(self):
        self.transcoder = None
        self.file_sender = None
        self.path = None
        self.host = platform.node()
        self.fp = None

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        return res

    def receiveMsg_InitFileReceiver(self, message, sender):
        self.transcoder = sender
        self.file_sender = message.source_address
        self.path = message.file
        folder = os.path.split(self.path)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.fp = open(self.path, 'wb')
        logging.info('Preparing to receive %s on %s.',
                     self.path,
                     self.host)
        time.sleep(5)
        self.send(self.file_sender, m.SendNextChunk())

    # def receiveMsg_InitFileReceiver(self, message, sender):
    #     self.transcoder = sender
    #     self.file_sender = message.source_address
    #     self.path = message.file
    #     folder = os.path.split(self.path)[0]
    #     if not os.path.exists(folder):
    #         os.makedirs(folder)
    #     self.fp = open(self.path, 'wb')
    #     logging.info('Preparing to receive %s on %s.',
    #                  self.path,
    #                  self.host)
    #     self.send(self.file_sender, m.SendNextChunk())

    def receiveMsg_Chunk(self, message, sender):
        self.fp.write(message.data)
        # logging.debug('Chunk received.')
        if not message.eof:
            self.send(self.file_sender, m.SendNextChunk())
        else:
            logging.debug('Entire file received.')
            self.fp.close()
            self.send(self.transcoder, m.FileTransferComplete())
            self.send(self.file_sender, ActorExitRequest())
            self.send(self.myAddress, ActorExitRequest())


    def receiveMsg_ActorExitRequest(self, message, sender):
        self.enabled = False