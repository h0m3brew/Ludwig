from datetime import datetime
import threading
import time
from subprocess import CalledProcessError
import subprocess
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from queue import Queue
import sys

from ludwigcluster import config


CMD = 'python3 {}/{}'.format(config.Dirs.watched, config.SFTP.watched_fname)


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.thread = None
        self.q = Queue()

    def start(self):
        self.thread = threading.Thread(target=self._process_q)
        self.thread.daemon = True
        self.thread.start()

    def on_any_event(self, event):
        is_trigger_event = Path(config.Dirs.watched) / config.SFTP.watched_fname == Path(event.src_path)

        if is_trigger_event:
            ts = datetime.now()
            self.q.put((event, ts))

    def delete_params_dirs(self):  # TODO use below
        delta = datetime.timedelta(hours=self.delete_delta)
        time_of_init_cutoff = datetime.datetime.now() - delta
        for params_p in (config.Dirs.lab / self.project_name / 'runs').glob('param_*'):
            if not (config.Dirs.lab / self.project_name / 'backup' / params_p.parent.name / params_p.name).exists():
                result = re.search('_(.*)_', params_p.name)
                time_of_init = result.group(1)
                dt = datetime.datetime.strptime(time_of_init, config.Time.format)
                if dt < time_of_init_cutoff:
                    print('Found dir more than {} hours old that is not backed-up.'.format(self.delete_delta))
                    self.delete_params_dir(params_p)

    def trigger(self):

        # TODO delete old job_dirs on worker


        try:
            subprocess.check_call([CMD], shell=True)  # stdout is already redirected, cannot do it here
        except CalledProcessError as e:  # this is required to continue to the next item in queue if current item fails
            print(e)

            # TODO delete job_dir here?

    def _process_q(self):
        last_ts = datetime.now()

        while True:
            event, time_stamp = self.q.get()
            time_delta = time_stamp - last_ts
            if time_delta.total_seconds() < 1:  # sftp produces 2 events within 1 sec - ignore 2nd event
                print('Ignoring 2nd event.')
                continue
            else:
                print('Detected event {} at {}'.format(event.src_path, datetime.now()))

            print('Executing "{}"'.format(CMD))
            sys.stdout.flush()
            self.trigger()
            last_ts = time_stamp
            print()
            sys.stdout.flush()


def watcher():
    print('Started file-watcher. If {} is modified (e.g. via SFTP), {}  will be executed.'.format(
        config.SFTP.watched_fname, config.SFTP.watched_fname))
    observer = Observer()
    handler = Handler()
    handler.start()

    observer.schedule(handler, config.Dirs.watched, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == '__main__':
    p = Path(config.Dirs.stdout)
    if not p.exists():
        p.mkdir(parents=True)
    watcher()