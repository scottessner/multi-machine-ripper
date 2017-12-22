from thespian.actors import ActorSystem
import app
import sys
import platform
import socket

port_number = int(sys.argv[1])
hostname = platform.node()
host_address = socket.gethostname(hostname)
convention_leader = sys.argv[2]

capability_names = (sys.argv + [''])[3].split(',')
capabilities = dict([('Admin Port', port_number),
                     ('Convention Address.IPv4', (convention_leader, 1900)),
                     ('HostName', hostname),
                    ] +
                    list(zip(capability_names, [True] * len(capability_names))))


asys = ActorSystem('multiprocTCPBase', capabilities)

if host_address == convention_leader:
    controller = asys.createActor('app.MasterController',
                                  globalName='MasterController')
    asys.tell(controller, app.HandleRegistrationChanges(True))
    controller.createActor(actorClass='a0',
                           targetActorRequirements={
                               'HostName': hostname},
                           globalName='NodeController'
                           )
