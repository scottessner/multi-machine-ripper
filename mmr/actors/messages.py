

class InitJobQueue(object):
    def __init__(self):
        pass


class AddTranscodeJob(object):
    def __init__(self, job):
        self.job = job


class AddTranscodeProject(object):
    def __init__(self, project):
        self.project = project


class StartTranscodeJob(object):
    def __init__(self, job):
        self.job = job


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
    def __init__(self, path, dest_host, job_queue):
        self.path = path
        self.dest_host = dest_host
        self.job_queue = job_queue


class InitFileSender(object):
    def __init__(self, job_id, job_state, file, job_queue):
        self.job_id = job_id
        self.job_state = job_state
        self.file = file
        self.job_queue = job_queue


class InitFileReceiver(object):
    def __init__(self, job_id, job_state, file, source_address, job_queue):
        self.job_id = job_id
        self.job_state = job_state
        self.file = file
        self.source_address = source_address
        self.job_queue = job_queue


class SendChunk(object):
    def __init__(self, offset):
        self.offset = offset


class Chunk(object):
    def __init__(self, data, length, offset, eof):
        self.data = data
        self.length = length
        self.offset = offset
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


class InitTranscodeManager(object):
    def __init__(self, job_queue):
        self.job_queue = job_queue


class TranscodeJobRequest(object):
    def __init__(self, host):
        self.host = host


class TranscodeJobResponse(object):
    def __init__(self, job):
        self.job = job


class UpdateTranscodeJob(object):
    def __init__(self, job_id=None, folder=None, file_name=None, state=None, progress=None, report=None, size=None):
        self.job_id = job_id
        self.folder = folder
        self.file_name = file_name
        self.state = state
        self.progress = progress
        self.report = report
        self.size = size


class InitTranscoder(object):
    def __init__(self, job, job_queue):
        self.job = job
        self.job_queue = job_queue


class FileTranscodeComplete(object):
    def __init__(self, return_code):
        self.return_code = return_code


class TranscodeJobComplete(object):
    def __init__(self, job, failed):
        self.job = job
        self.failed = failed

