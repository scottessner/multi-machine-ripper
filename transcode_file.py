import subprocess

class Receiver(object):

    def __init__(self, path, port):
        self.path = path
        self.port = port
        self.fp = None
        self.sock = None

    def open(self):
        self.fp = open(self.path, 'wb+')
        # self.sock =


class Sender(object):
    def __init__(self, path, port):
        self.path = path
        self.port = port
        self.fp = None
        self.sock = None

    # def


# if __name__ == '__main__':

    # transcode('/data/leader/incoming/The Big Bang Theory Season 10/The_Big_Bang_Theory_Season_10_Disc_1_t00.mkv',
    #           '/data/leader/outgoing/The_Big_Bang_Theory_Season_10_Disc_1_t00.mkv')