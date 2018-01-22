from thespian.actors import *
from . import messages as m
from ..models import TranscodeJob
import platform
import inotify.adapters
import inotify.constants as ic
import logging


class NodeController(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(NodeController, self).__init__(*args, **kwargs)
        self.address_book = dict()

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        return capabilities['HostName'] == requirements['HostName']

    def receiveMsg_Initialize(self, message, sender):
        self.address_book['coordinator'] = sender
        self._createNodeAcceptor()

    def receiveMsg_ActorHostRequest(self, message, sender):
        self.send(sender, m.ActorHostResponse(platform.node()))

    def receiveMsg_ForwardToCoordinator(self, message, sender):
        print('NodeController received message to forward.')
        self.send(self.coordinator, message.text)

    def receiveMsg_str(self, message, sender):
        self.send(sender, message)

    def _createNodeAcceptor(self):
        self.address_book['acceptor'] = self.createActor('mmr.NodeAcceptor',
                                                         globalName='NodeAcceptor',
                                                         targetActorRequirements={'HostName': platform.node()})
        self.send(self.address_book['acceptor'], m.Initialize({'node_controller': self.myAddress}))


class NodeAcceptor(ActorTypeDispatcher):
    def __init__(self):
        super(NodeAcceptor, self).__init__()
        self.address_book = dict()

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        return capabilities['HostName'] == requirements['HostName']

    def receiveMsg_Initialize(self, message, sender):
        for addr in message.addresses.keys():
            self.address_book[addr] = message.addresses[addr]

    def receiveMsg_ParentAddress(self, message, sender):
        self.node_controller = message.address

    def receiveMsg_ForwardToCoordinator(self, message, sender):
        print('NodeAcceptor received message to forward.')
        self.send(self.node_controller, message)


class FolderWatcher(ActorTypeDispatcher):
    def __init__(self):
        super(FolderWatcher, self).__init__()
        self.watched_folder = None
        self.adapter = None
        self.events = None
        self.enabled = False
        self.coordinator = None
        self.dest_host = None
        self.host = platform.node()

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        return res

    def receiveMsg_InitWatcher(self, message, sender):
        self.coordinator = sender
        self.watched_folder = message.path
        self.dest_host = message.dest_host
        self.adapter = inotify.adapters.InotifyTree(self.watched_folder)
        logging.info('Started watching %s on %s. Completed transcodes will be sent to %s',
                     self.watched_folder,
                     self.host,
                     self.dest_host)

    def receiveMsg_StartWatching(self, message, sender):
        self.events = self.adapter.event_gen()
        self.enabled = True
        self.send(self.myAddress, m.KeepWatching())

    def receiveMsg_KeepWatching(self, message, sender):
        # Pull the next event from the inotify generator
        for event in self.events:
            if event is not None:
                (eventinfo, typenames, folder, file) = event
                # print(eventinfo)
                # print(typenames)
                # print(folder)
                # print(file)
                if hasattr(eventinfo, 'mask'):
                    # Create the transcode job when the file is created, can be used to track ripping time
                    # Also will help with awareness of pending additional files to transcode
                    if eventinfo.mask == ic.IN_CREATE:
                        self.send(self.coordinator, m.AddTranscodeJob(TranscodeJob(folder=folder,
                                                                                   file_name=file,
                                                                                   base_path=self.watched_folder,
                                                                                   origin_host=self.host,
                                                                                   dest_host=self.dest_host)))
                    # If the event is a file 'IN_CLOSE_WRITE' (mask=8), mark it as ready to transcode
                    elif eventinfo.mask == ic.IN_CLOSE_WRITE:
                        print('Time to Write')
                        # event[2] is the full path of the file, event[3] is the file name
                        self.send(self.coordinator, m.StartTranscodeJob(folder=folder,
                                                                        file_name=file))
            # Make sure to break out after each event
            break

        if self.enabled:
            self.send(self.myAddress, m.KeepWatching())

    def receiveMsg_StopWatching(self, message, sender):
        self.enabled = False

    def receiveMsg_ActorExitRequest(self, message, sender):
        self.enabled = False
