from thespian.actors import ActorTypeDispatcher
from . import messages as m
import logging
import platform
import time


class Coordinator(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(Coordinator, self).__init__(*args, **kwargs)
        self.job_queue = None

    def receiveMsg_Initialize(self, message, sender):
        self.send(self.myAddress, m.HandleRegistrationChanges(True))
        self.job_queue = self.createActor('mmr.JobQueue')
        self.send(self.job_queue, m.InitJobQueue())
        if hasattr(message, 'capabilities'):
            self._create_node_actors(message.capabilities)
        logging.debug('Coordinator initialized.')

    def receiveMsg_HandleRegistrationChanges(self, message, sender):
        self.notifyOnSystemRegistrationChanges(message.value)
        self.send(sender, 'Now handling registration changes')
        logging.debug('Coordinator now handling registration changes.')

    def receiveMsg_ActorSystemConventionUpdate(self, message, sender):
        if message.remoteAdded:
            print(message.remoteAdminAddress)
            self._create_node_actors(message.remoteCapabilities)

    def _create_node_actors(self, capabilities):
        # Create Folder Watchers for any watched folder on this system
        host = capabilities['HostName']
        if capabilities.get('WatchFolders', None):
            for folder in capabilities['WatchFolders']:
                self._create_folder_watcher(host, folder)

        # Create a transcoder if Handbrake is installed
        if capabilities.get('HandBrakeCLI', None):
            self._create_transcoder(capabilities['HostName'])

    def _create_folder_watcher(self, host, folder):
        watcher = self.createActor('mmr.FolderWatcher',
                                   targetActorRequirements={'HostName': host})
        self.send(watcher, m.InitWatcher(folder, dest_host=platform.node(), job_queue=self.job_queue))
        self.send(watcher, m.StartWatching())

    def _create_transcoder(self, host):
        transcoder = self.createActor('mmr.TranscodeManager',
                                      {'HostName': host,
                                      'HandBrakeCLI': True})
        self.send(transcoder, m.InitTranscodeManager(self.job_queue))
