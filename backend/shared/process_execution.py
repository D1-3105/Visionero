import subprocess


def run_process(exe: str):
    proc = subprocess.Popen(exe, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
    pid = proc.pid
    return pid
