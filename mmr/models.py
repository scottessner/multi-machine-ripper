import os
from os import path
import uuid
import logging
import time
import enum
from csv import DictReader, DictWriter


class TranscodeJob(object):
    def __init__(self,
                 folder=None,
                 file_name=None,
                 base_path=None,
                 origin_host=None,
                 dest_host=None,
                 # args=None,
                 # worker=None,
                 # time_created=None,
                 # time_started=None,
                 # time_finished=None,
                 # status='NEW',
                 ):
        self.state = JobState.RIPPING
        self.file_name = file_name
        self.folder = folder
        self.base_path = base_path
        self.origin_host = origin_host
        self.dest_host = dest_host
        self.relative_folder = self.get_relative_folder(folder)
        self.relative_file = path.join(self.relative_folder, file_name)
        self.input_file = path.join(folder, file_name)
        self.output_file = str.replace(self.input_file, 'incoming', 'outgoing')
        self.id = uuid.uuid4()
        self.transcode_host = ''
        self.rip_started = time.time()
        self.rip_completed = None
        self.to_transcoder_started = None
        self.to_transcoder_completed = None
        self.transcode_started = None
        self.transcode_completed = None
        self.transcode_report = None
        self.from_transcoder_started = None
        self.from_transcoder_completed = None
        self.initial_file_size = 0
        self.final_file_size = 0
        self.progress = 0

    def update(self, state, progress, report=None, size=None):
        print('Job Update! State: {0}, Progress: {1}, Report: {2}'.format(state, progress, report))
        if state != self.state:
            if state == JobState.RIPPING:
                if size is not None:
                    self.initial_file_size = size
            if state == JobState.RIPPED:
                self.rip_completed = time.time()
                if size is not None:
                    self.initial_file_size = size
                self.state = JobState.RIPPED
            if state == JobState.SENDING:
                self.to_transcoder_started = time.time()
                self.state = JobState.SENDING
            elif state == JobState.SENT:
                self.to_transcoder_completed = time.time()
                self.state = JobState.SENT
            elif state == JobState.TRANSCODING:
                self.transcode_started = time.time()
                self.state = JobState.TRANSCODING
            elif state == JobState.TRANSCODED:
                self.transcode_completed = time.time()
                if size is not None:
                    self.final_file_size = size
                if report is not None:
                    self.transcode_report = report
                self.state = JobState.TRANSCODED
            elif state == JobState.RECEIVING:
                self.from_transcoder_started = time.time()
                self.state = JobState.RECEIVING
            elif state == JobState.RECEIVED:
                self.from_transcoder_completed = time.time()
                self.state = JobState.RECEIVED
            elif state == JobState.COMPLETED:
                self.final_file_size = path.getsize(self.output_file)
        if progress is not None:
            self.progress = progress

    def get_relative_folder(self, abs_folder):
        base_folder, rel_folder = path.split(abs_folder)
        while base_folder != self.base_path:
            base_folder, rel_part = path.split(base_folder)
            rel_folder = path.join(rel_part, rel_folder)
        return rel_folder

    def __repr__(self):
        output = list()
        output.append(self.state.name.ljust(12))
        output.append(str(self.progress).rjust(3))
        output.append(self.transcode_host.ljust(12))
        output.append(str(round(self.initial_file_size/1024/1024, 1)).rjust(9))
        output.append(self.relative_file)
        return ' | '.join(output)


class JobState(enum.IntEnum):
    RIPPING = 1
    RIPPED = 2
    SENDING = 3
    SENT = 4
    TRANSCODING = 5
    TRANSCODED = 6
    RECEIVING = 7
    RECEIVED = 8
    COMPLETED = 9
    FAILED = 10


class TranscodeQueue(object):
    def __init__(self):
        self.jobs = list()
        logging.info('Queue created.')

    def add_job(self, job):
        print('Adding job: {0}, {1}'.format(job.folder, job.file_name))
        self.jobs.append(job)

    def make_job_ready(self, updated_job):
        for job in self.jobs:
            print('Job info Folder: {0}, File: {1}'.format(job.folder, job.file_name))
        jobs = [job for job in self.jobs if job.folder == updated_job.folder and job.file_name == updated_job.file_name]
        if len(jobs) == 0:
            self.add_job(updated_job)
            jobs.append(updated_job)
        self.update_job(jobs[0].id, JobState.RIPPED, 100)
        print(self.status())

    def start_job(self, host):
        try:
            # Return jobs ready to start transcoding (rip completed and no host assigned)
            jobs = [job for job in self.jobs if job.state == JobState.RIPPED]
            next_job = sorted(jobs, key=lambda job: job.rip_completed)[0]

            # Sort jobs by order of rip completion
            next_job.transcode_host = host
            next_job.state = JobState.SENDING
            return next_job
        except IndexError:
            return None

    def get_job(self, job_id=None, folder=None, file_name=None):
        job = None
        if job_id is not None:
            job = [job for job in self.jobs if job.id == job_id][0]
        elif folder is not None and file_name is not None:
            job = [job for job in self.jobs if
                   job.folder == folder and job.file_name == file_name][0]
        return job

    def update_job(self, job_id=None, folder=None, file_name=None, state=None, progress=None, report=None, size=None):
        logging.debug('Updating job with id %s to state %s', job_id, state)
        job = self.get_job(job_id, folder, file_name)
        # print('Job: {0}, State: {1}, Progress: {2}, Report: {3}'.format(job, state, progress, report))
        job.update(state, progress, report, size)

    def complete_job(self, job_id):
        completed_job = [job for job in self.jobs if job.id == job_id][0]
        completed_job.update(JobState.COMPLETED, 100)
        self.update_history(completed_job)
        if path.exists(completed_job.input_file):
            os.remove(completed_job.input_file)
        self.jobs.remove(completed_job)
        jobs_in_project = [job for job in self.jobs if job.relative_folder == completed_job.relative_folder]
        if len(jobs_in_project) == 0:
            os.rmdir(completed_job.folder)

    def fail_job(self, job_id):
        failed_job = [job for job in self.jobs if job.id == job_id][0]
        failed_job.state = JobState.RIPPED
        failed_job.transcode_host = ''
        logging.info(self.status())

    def status(self):

        output = list()
        header = list()
        header.append('STATE'.ljust(12))
        header.append('PRG'.rjust(3))
        header.append('HOST'.ljust(12))
        header.append('SIZE (MB)'.rjust(9))
        header.append('FILE')
        output.append(' | '.join(header))
        output.append('-' * 80)

        self.jobs.sort(key=lambda x: x.state)
        for job in self.jobs:
            output.append(repr(job))
        return '\n'.join(output)

    def update_history(self, job):
        history = list()
        keys = list(job.__dict__.keys())

        try:
            with open('/log/job_history.csv', 'r+') as in_file:
                reader = DictReader(in_file)
                keys.extend(reader.fieldnames)
                for row in reader:
                    history.append(row)
        except FileNotFoundError:
            logging.info('History file not found.  Creating now.')

        final_keys = set(keys)

        with open('/log/job_history.csv', 'w+') as out_file:
            writer = DictWriter(out_file, fieldnames=final_keys)
            writer.writeheader()
            writer.writerows(history)
            writer.writerow(job.__dict__)

    def __repr__(self):
        return self.status()
