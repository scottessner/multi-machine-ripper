from thespian.actors import ActorSystem
import app
import sys
import platform
import socket
import time

port_number = int(sys.argv[1])
hostname = platform.node()
host_address = socket.gethostbyname(hostname)
convention_leader = sys.argv[2]

capability_names = (sys.argv + [''])[3].split(',')
capabilities = dict([('Admin Port', port_number),
                     ('Convention Address.IPv4', (convention_leader, 1900)),
                     ('HostName', hostname),
                    ] +
                    list(zip(capability_names, [True] * len(capability_names))))


asys = ActorSystem('multiprocTCPBase', capabilities)

if host_address == convention_leader:
    print("I'm the convention leader, let's create a Master Controller")
    controller = asys.createActor('app.MasterController',
                                  globalName='MasterController')

    print("Telling the master to watch for convention registration changes")
    asys.tell(controller, app.HandleRegistrationChanges(True))

    print("Now tell the master controller to create a node controller on my system")
    controller.createActor(actorClass='app.NodeController',
                           targetActorRequirements={
                               'HostName': hostname},
                           globalName='NodeController'
                           )

while True:
    print("sleeping")
    time.sleep(100)
