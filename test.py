from thespian.actors import *
import app

if __name__ == "__main__":
    import sys
    asys = ActorSystem('multiprocTCPBase')

    # Note: the following doesn't work because actor is created by
    # admin, started by the start.py, and the Acceptor class is not
    # part of start.py
    #     app = asys.createActor(Acceptor)

    # c = app.ConventionMembers()

    ctrl = asys.createActor('app.MasterController',
                           globalName='MasterController')
    r = asys.ask(ctrl, app.ConventionMembers()) #, timedelta(seconds=1))
    # while r:
    #     for x in r:
    #         for y in x.keys():
    #             print('{0}: {1}'.format(y, x[y]))
    #     r = asys.listen(timedelta(seconds=1.0))
    sys.exit(0)