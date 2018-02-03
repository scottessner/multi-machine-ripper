from thespian.actors import *
from . import messages as m
from ..models import TranscodeJob, JobState
import platform
import inotify.adapters
import inotify.constants as ic
import logging
import os

class FolderWatcher(ActorTypeDispatcher):
    def __init__(self):
        super(FolderWatcher, self).__init__()
        self.watched_folder = None
        self.adapter = None
        self.events = None
        self.enabled = False
        self.coordinator = None
        self.dest_host = None
        self.job_queue = None
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
        self.job_queue = message.job_queue
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
                        print(event)
                        self.send(self.job_queue, m.AddTranscodeJob(TranscodeJob(folder=folder,
                                                                                 file_name=file,
                                                                                 base_path=self.watched_folder,
                                                                                 origin_host=self.host,
                                                                                 dest_host=self.dest_host)))

                    if eventinfo.mask == ic.IN_MODIFY:
                        size = os.path.getsize(os.path.join(folder, file))
                        logging.debug('Sending Update %s/%s is now %s bytes', folder, file, size)
                        self.send(self.job_queue, m.UpdateTranscodeJob(folder=folder,
                                                                       file_name=file,
                                                                       state=JobState.RIPPING,
                                                                       size=size))

                    # If the event is a file 'IN_CLOSE_WRITE' (mask=8), mark it as ready to transcode
                    elif eventinfo.mask == ic.IN_CLOSE_WRITE:
                        print('Time to Write')
                        print(event)
                        # event[2] is the full path of the file, event[3] is the file name
                        self.send(self.job_queue, m.StartTranscodeJob(TranscodeJob(folder=folder,
                                                                                   file_name=file,
                                                                                   base_path=self.watched_folder,
                                                                                   origin_host=self.host,
                                                                                   dest_host=self.dest_host,
                                                                                   )))
                        size = os.path.getsize(os.path.join(folder, file))
                        self.send(self.job_queue, m.UpdateTranscodeJob(folder=folder,
                                                                       file_name=file,
                                                                       state=JobState.RIPPED,
                                                                       size=size))
            # Make sure to break out after each event
            break

        if self.enabled:
            self.send(self.myAddress, m.KeepWatching())

    def receiveMsg_StopWatching(self, message, sender):
        self.enabled = False

    def receiveMsg_ActorExitRequest(self, message, sender):
        self.enabled = False
