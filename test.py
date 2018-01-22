from os import environ
import platform
from thespian.actors import ActorSystem
from mmr import TranscodeJob
from mmr import messages as m


class ActorSystemInterface(object):

    def __init__(self):
        self.asys = None
        self.master = None
        self.acceptor = None

    def connect_to_system(self):
        port_number = 1900
        hostname = platform.node()
        convention_leader = environ['MMR-LEADER']

        capabilities = dict([('Admin Port', port_number),
                             ('Convention Address.IPv4', (convention_leader, 1900)),
                             ('HostName', hostname),
                             ])

        self.asys = ActorSystem('multiprocTCPBase', capabilities)

    def get_coordinator(self):
        self.coordinator = self.asys.createActor('mmr.Coordinator',
                                                 globalName='Coordinator')

    def get_acceptor(self):
        self.acceptor = self.asys.createActor('mmr.NodeAcceptor',
                                              globalName='NodeAcceptor',
                                              targetActorRequirements={'HostName': platform.node()})

    def check_node_hosts(self):
        self.asys.tell(self.master, m.CheckNodeHosts())

    def run_test_message(self, text):
        self.connect_to_system()
        self.get_acceptor()
        self.asys.tell(self.acceptor, m.ForwardToCoordinator(text))

    def test_add_job(self):
        self.connect_to_system()
        self.get_coordinator()
        job = TranscodeJob(path='/app/test')
        self.asys.tell(self.coordinator, m.AddTranscodeJob(job))

    def start_watcher(self):
        self.connect_to_system()
        watcher = self.asys.createActor('mmr.FolderWatcher',
                                        targetActorRequirements={'HostName': platform.node()})
        self.asys.tell(watcher, m.StartWatching())
        return watcher


if __name__ == '__main__':
    asi = ActorSystemInterface()
    asi.start_watcher()