import os
import platform
import socket
import subprocess
import time
import signal

from thespian.actors import ActorSystem, ActorExitRequest
from mmr.config import Config, LogConfig
from mmr import messages


# Checks to verify that the HandBrake command can be called
def handbrake_exists():
    try:
        subprocess.call(["HandBrakeCLI", "--version"])
    except OSError as e:
        print('Handbrake error: {0}'.format(e.errno))
        return False
    return True


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# Pull configuration information from the config file
port_number = Config['PORT_NUMBER']
hostname = platform.node()
host_address = get_ip()
convention_leader = os.environ['MMR_LEADER']
#convention_leader = Config['CONVENTION_LEADER']
if host_address == convention_leader:
    watch_folders = Config['WATCH_FOLDERS']
else:
    watch_folders = None

# Format config into a dictionary to pass to the Actor System
capabilities = dict([('Admin Port', port_number),
                     ('Convention Address.IPv4', (convention_leader, port_number)),
                     ('WatchFolders', watch_folders),
                     ('HostName', hostname),
                     ('HandBrakeCLI', handbrake_exists())
                    ])

print(capabilities)

# Creates Actor System
asys = ActorSystem('multiprocTCPBase', capabilities, logDefs=LogConfig)

# Set a variable that watches for a stop signal from the system
# stopped = False

# If we are the convention leader, set up the coordinator and have it watch for
# convention updates
if host_address == convention_leader:
    # print("I'm the convention leader, let's create a Master Controller")
    controller = asys.createActor('mmr.Coordinator',
                                  globalName='Coordinator')

    asys.tell(controller, messages.Initialize(capabilities=capabilities))
    # print("Telling the master to watch for convention registration changes")

    # print("Now tell the master controller to create a node controller on my system")
    node_controller = asys.ask(controller, messages.CreateNodeController(hostname))
    # print(node_controller)

# while controller:
#     print(controller)
#     controller = asys.listen(timedelta(seconds=1.0))
# sys.exit(0)

# Kill the coordinator and shut down the actor system
def stop(sig, frame):
    # global stopped
    # stopped = True
    global controller
    asys.tell(controller, ActorExitRequest())
    asys.shutdown()
    print('stopping')

# Register a handler for the stop signal
signal.signal(signal.SIGTERM, stop)

# Loop until we get a stop signal
while True:
    # print('running')
    time.sleep(60)