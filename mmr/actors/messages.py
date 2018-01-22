class AddTranscodeJob(object):
    def __init__(self, job):
        self.job = job


class AddTranscodeProject(object):
    def __init__(self, project):
        self.project = project


class StartTranscodeJob(object):
    def __init__(self, folder, file_name):
        self.folder = folder,
        self.file_name = file_name


class UpdateTranscodeJob(object):
    def __init__(self, job_id, state, progress, report=None):
        self.job_id = job_id,
        self.state = state,
        self.progress = progress
        self.report = report


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


class InitWatcher(object):
    def __init__(self, path, dest_host):
        self.path = path
        self.dest_host = dest_host


class InitFileSender(object):
    def __init__(self, file):
        self.file = file


class InitFileReceiver(object):
    def __init__(self, file, source_address):
        self.file = file
        self.source_address = source_address


class SendNextChunk(object):
    def __init__(self):
        pass


class Chunk(object):
    def __init__(self, data, eof):
        self.data = data
        self.eof = eof


class FileTransferComplete(object):
    def __init__(self):
        pass


class Initialize(object):
    def __init__(self, addresses=None, capabilities=None):
        self.addresses = addresses
        self.capabilities = capabilities


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


class StartWatching(object):
    def __init__(self):
        pass


class KeepWatching(object):
    def __init__(self):
        pass


class StopWatching(object):
    def __init__(self):
        pass


class CreateNodeAcceptor(object):
    def __init__(self):
        pass


class CreateNodeActors(object):
    def __init__(self, host=None, capabilities=None):
        self.host = host
        self.capabilities = capabilities


class CreateFolderWatcher(object):
    def __init__(self, host, folder):
        self.host = host
        self.folder = folder


class TranscodeJobRequest(object):
    def __init__(self, host):
        self.host = host


class TranscodeJobResponse(object):
    def __init__(self, job):
        self.job = job


class TranscodeJobComplete(object):
    def __init__(self, job, failed):
        self.job = job
        self.failed = failed