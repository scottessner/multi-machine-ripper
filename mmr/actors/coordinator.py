from thespian.actors import ActorTypeDispatcher
from . import messages as m
from ..config import Config
from ..models import TranscodeJob, TranscodeQueue
import os
import pickle
import logging
import platform


class Coordinator(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(Coordinator, self).__init__(*args, **kwargs)
        # self.nodes = set()
        # self.node_controllers = dict()
        # self.transcoders = dict()
        self.transcode_queue = self.restore_queue()
        # self.watchers = list()

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

    def receiveMsg_Initialize(self, message, sender):
        self.send(self.myAddress, m.HandleRegistrationChanges(True))
        if hasattr(message, 'capabilities'):
            self._create_node_actors(message.capabilities)
        logging.debug('Coordinator initialized.')

    # Exit handler - currently pickles transcode queue
    def receiveMsg_ActorExitRequest(self, message, sender):
        self.save_queue()

    def receiveMsg_HandleRegistrationChanges(self, message, sender):
        self.notifyOnSystemRegistrationChanges(message.value)
        self.send(sender, 'Now handling registration changes')
        logging.debug('Coordinator now handling registration changes.')

    def receiveMsg_ActorSystemConventionUpdate(self, message, sender):
        if message.remoteAdded:
            print(message.remoteAdminAddress)
            #host = message.remoteCapabilities['HostName']

            self._create_node_actors(message.remoteCapabilities)

            # self.nodes.add(host)
            # self.send(self.myAddress, m.CreateNodeController(host))
            # print('Checking for WatchFolder')
            # if message.remoteCapabilities.get('WatchFolders', None):
            #     print('WatchFolder Attribute Found')
            #     for folder in message.remoteCapabilities['WatchFolders']:
            #         self.send(self.myAddress, m.CreateFolderWatcher(host, folder))
    #
    # def receiveMsg_CreateNodeController(self, message, sender):
    #     node_controller = self.createActor('mmr.NodeController',
    #                                        targetActorRequirements={'HostName': message.host})
    #
    #     print('Node Controller Created for {0} at {1}'.format(message.host, node_controller))
    #     self.node_controllers[message.host] = node_controller
    #     self.send(node_controller, m.Initialize(self.myAddress))
    #     self.send(sender, node_controller)
    #     self._collect_transcoders()
    #
    # def receiveMsg_CreateFolderWatcher(self, message, sender):
    #     watcher = self.createActor('mmr.FolderWatcher',
    #                                targetActorRequirements={'HostName': message.host})
    #     self.send(watcher, m.InitWatcher(message.folder))
    #     self.send(watcher, m.StartWatching())
    #
    # def receiveMsg_RequestTranscoders(self, message, sender):
    #     for node in self.node_controllers.keys():
    #         self.transcoders[node] = self.createActor('mmr.Transcoder',
    #                                                   targetActorRequirements={'HostName': message.host})

    def receiveMsg_AddTranscodeJob(self, message, sender):
        self.transcode_queue.add_job(message.job)
        print(self.transcode_queue)

    def receiveMsg_StartTranscodeJob(self, message, sender):
        self.transcode_queue.make_job_ready(message.folder, message.file_name)

    def receiveMsg_UpdateTranscodeJob(self, message, sender):
        self.transcode_queue.update_job(message.job_id, message.state, message.progress)

    def receiveMsg_TranscodeJobRequest(self, message, sender):
        job = self.transcode_queue.start_job(message.host)
        if job:
            logging.info('Transcode of %s started on %s', job.file_name, message.host)
        self.send(sender, m.TranscodeJobResponse(job))

    def receiveMsg_TranscodeJobComplete(self, message, sender):
        if not message.failed:
            self.transcode_queue.complete_job(message.job)
            os.remove(message.job.input_file)
        else:
            self.transcode_queue.fail_job(message.job)

    def receiveMsg_str(self, message, sender):
        print('Coordinator received message {0}'.format(message))

    def _collect_transcoders(self):
        for node in self.nodes:
            if self.transcoders.get(node, None) is None:
                self.transcoders[node] = self.createActor('mmr.Transcoder',
                                                          targetActorRequirements={'HostName': node,
                                                                                   'HandBrakeCLI': True})
                if node in self.node_controllers.keys():
                    self.send(self.transcoders[node], m.Initialize({'coordinator': self.myAddress}))

    # def _createTranscoder(self):

    #
    #     addresses = dict()
    #     addresses['node_controller'] = self.myAddress
    #     addresses['coordinator'] = self.address_book['coordinator']
    #
    #     self.send(self.address_book['transcoder'], m.Initialize(addresses))

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
        self.send(watcher, m.InitWatcher(folder, dest_host=platform.node()))
        self.send(watcher, m.StartWatching())

    def _create_transcoder(self, host):
        transcoder = self.createActor('mmr.Transcoder',
                                      {'HostName': host,
                                      'HandBrakeCLI': True})
        self.send(transcoder, m.Initialize())