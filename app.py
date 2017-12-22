from thespian.actors import *
from datetime import timedelta


class ConventionMembers(object):
    def __init__(self):
        self.members = 'none'


class HandleRegistrationChanges(object):
    def __init__(self, val):
        self.value = val
        self.nodes = dict()


class MasterController(ActorTypeDispatcher):
    def __init__(self, *args, **kwargs):
        super(MasterController, self).__init__(*args, **kwargs)
        self.node_controllers = dict()

    def receiveMsg_HandleRegistrationChanges(self, message, sender):
        self.notifyOnSystemRegistrationChanges(message.value)
        self.send(sender, 'Hi there')

    def receiveMsg_ActorSystemConventionUpdate(self, message, sender):
        self.convention_members.append(message)

    def receiveMsg_ConventionMembers(self, message, sender):
        # print('Received request for convention members')
        self.send(sender, self.convention_members)

    def receiveMsg_str(self, message, sender):
        # print('Received request for convention members as string')
        # self.send(sender, self.convention_members)
        self.send(sender, 'Hi there')


class NodeController(ActorTypeDispatcher):
    def receiveMessage_str(self, message, sender):
        self.send(sender, message)