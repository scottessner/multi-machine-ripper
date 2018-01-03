import os
import platform
import socket
import subprocess
import time

from thespian.actors import ActorSystem

from mmr import node_actors


# from mmr.actors.actors import *

def handbrake_exists():
    try:
        subprocess.call(["HandBrakeCLI", "--version"])
    except OSError as e:
        print('Handbrake error: {0}'.format(e.errno))
        return False
    return True

port_number = 1900
hostname = platform.node()
host_address = socket.gethostbyname(hostname)
convention_leader = os.environ['MMR-LEADER']

capabilities = dict([('Admin Port', port_number),
                     ('Convention Address.IPv4', (convention_leader, 1900)),
                     ('HostName', hostname),
                    ])

if handbrake_exists():
    capabilities['HandBrakeCLI'] = True

asys = ActorSystem('multiprocTCPBase', capabilities)

print(asys.capabilities)

if host_address == convention_leader:
    print("I'm the convention leader, let's create a Master Controller")
    controller = asys.createActor('mmr.coordinator.Coordinator',
                                  globalName='Coordinator')

    print("Telling the master to watch for convention registration changes")
    asys.tell(controller, node_actors.HandleRegistrationChanges(True))

    print("Now tell the master controller to create a node controller on my system")
    node_controller = asys.ask(controller, node_actors.CreateNodeController(hostname))
    print(node_controller)

# while controller:
#     print(controller)
#     controller = asys.listen(timedelta(seconds=1.0))
# sys.exit(0)

while True:
    print('sleeping')
    time.sleep(60)