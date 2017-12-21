from thespian.actors import ActorSystem
import app
import sys
import platform

portnum = int(sys.argv[1])
hostname = platform.node()

capability_names = (sys.argv + [''])[2].split(',')
capabilities = dict([('Admin Port', portnum),
                     ('Convention Address.IPv4', ('', 1900)),
                     ('HostName', hostname),
                    ] +
                    list(zip(capability_names, [True] * len(capability_names))))


asys = ActorSystem('multiprocTCPBase', capabilities)
controller = asys.createActor('app.MasterController',
                           globalName='MasterController')
asys.tell(controller, app.HandleRegistrationChanges(True))