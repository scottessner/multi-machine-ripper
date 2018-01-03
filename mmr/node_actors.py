from thespian.actors import *
from datetime import timedelta
import platform
from queue import Queue
import subprocess


class NodeControllers(object):
    def __init__(self):
        self.members = 'none'


class HandleRegistrationChanges(object):
    def __init__(self, val):
        self.value = val
        self.nodes = dict()


class CreateNodeController(object):
    def __init__(self, hostname):
        self.host = hostname


class Initialize(object):
    def __init__(self, addresses=None):
        self.addresses = addresses


class ActorHostRequest(object):
    def __init__(self):
        pass


class ActorHostResponse(object):
    def __init__(self, host):
        self.host = host


class CheckNodeHosts(object):
    def __init__(self):
        pass


class ForwardToCoordinator(object):
    def __init__(self, text):
        self.text = text


class TranscoderStatusRequest(object):
    pass


class TranscoderStatus(object):
    def __init__(self, state, task):
        self.state = None
        self.task = None




class CreateNodeAcceptor(object):
    def __init__(self):
        pass


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
        self.send(sender, ActorHostResponse(platform.node()))

    def receiveMsg_ForwardToCoordinator(self, message, sender):
        print('NodeController received message to forward.')
        self.send(self.coordinator, message.text)

    def receiveMsg_str(self, message, sender):
        self.send(sender, message)

    def _createNodeAcceptor(self):
        self.address_book['acceptor'] = self.createActor('mmr.node_actors.NodeAcceptor',
                                                         globalName='NodeAcceptor',
                                                         targetActorRequirements={'HostName': platform.node()})
        self.send(self.address_book['acceptor'], Initialize({'node_controller': self.myAddress}))

    def _createTranscoder(self):
        self.address_book['transcoder'] = self.createActor('mmr.node_actors.Transcoder',
                                                           {'HostName': platform.node(),
                                                            'HandBrakeCLI': True})

        addresses = dict()
        addresses['node_controller'] = self.myAddress
        addresses['coordinator'] = self.address_book['coordinator']

        self.send(self.address_book['transcoder'], Initialize(addresses))


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


class Transcoder(ActorTypeDispatcher):
    def __init__(self):
        self.state = 'init'
        self.task = None
        self.address_book = dict()

    @staticmethod
    def actorSystemCapabilityCheck(capabilities, requirements):
        res = True
        res = res and capabilities['HostName'] == requirements['HostName']
        res = res and capabilities['HandBrakeCLI']
        return res

    def receiveMsg_Initialize(self, message, sender):
        for addr in message.addresses.keys():
            self.address_book[addr] = message.addresses[addr]
        self.state = 'available'

    def receiveMsg_TranscodeTask(self, message, sender):
        self.state = 'busy'
        process = subprocess.Popen(message.command, stdout=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        self.send(self.address_book['coordinator'], 'Transcode_Complete')
