from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from mmr.node_actors import *



class Coordinator(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(Coordinator, self).__init__(*args, **kwargs)
        self.node_controllers = dict()
        self.transcoders = dict()
        self.transcode_queue = Queue()
        self.engine = create_engine('sqlite:///mmr.db')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def receiveMsg_HandleRegistrationChanges(self, message, sender):
        self.notifyOnSystemRegistrationChanges(message.value)
        self.send(sender, 'Now handling registration changes')


    def receiveMsg_ActorSystemConventionUpdate(self, message, sender):
        if message.remoteAdded:
            print(message.remoteAdminAddress)
            host = message.remoteCapabilities['HostName']
            self.send(self.myAddress, CreateNodeController(host))

    def receiveMsg_NodeControllers(self, message, sender):
        # print('Received request for convention members')
        self.send(sender, self.node_controllers)

    def receiveMsg_CreateNodeController(self, message, sender):
        node_controller = self.createActor('mmr.node_actors.NodeController',
                                           targetActorRequirements={'HostName': message.host})

        print('Node Controller Created for {0} at {1}'.format(message.host, node_controller))
        self.node_controllers[message.host] = node_controller
        self.send(node_controller, Initialize(self.myAddress))
        self.send(sender, node_controller)
        self._collect_transcoders()

    def receiveMsg_CheckNodeHosts(self, message, sender):
        for node in self.node_controllers:
            self.send(self.node_controllers[node], ActorHostRequest())

    def receiveMsg_RequestTranscoders(self, message, sender):
        for node in self.node_controllers.keys():
            self.transcoders[node] = self.createActor('mmr.node_actors.Transcoder',
                             targetActorRequirements={'HostName': message.host})


    def receiveMsg_ActorHostResponse(self, message, sender):
        print('Actor at {0} is on host {1}'.format(sender, message.host))

    def receiveMsg_AddTranscodeJob(self, message, sender):
        self.session.add(message.job)
        self.session.commit()

    def receiveMsg_str(self, message, sender):
        print('Coordinator received message {0}'.format(message))

    def _collect_transcoders(self):
        for node in self.node_controllers.keys():
            if self.transcoders.get(node, None) is None:
                self.transcoders[node] = self.createActor('mmr.node_actors.Transcoder',
                                                          targetActorRequirements={'HostName': node,
                                                                                   'HandBrakeCLI': True})
                if node in self.node_controllers.keys():
                    self.send(self.transcoders[node], Initialize({'coordinator': self.myAddress}))


class AddTranscodeJob(object):
    def __init__(self, job):
        self.job = job