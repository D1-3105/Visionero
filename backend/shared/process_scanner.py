import datetime
import os
import pathlib

import win32com
import win32evtlog
from win32com.client import Dispatch
import pythoncom

DESKTOP_PATH = pathlib.Path(r'C:\Users\User\Desktop')
last_scanned_pids = {}  # pid: executable


def get_process_list():
    links = os.listdir(DESKTOP_PATH)
    process_list_executables = []
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("WScript.Shell")
    for link in links:
        if (DESKTOP_PATH / link).is_file():
            if link.endswith('lnk'):
                shortcut = shell.CreateShortcut(str(DESKTOP_PATH / link))
                lnk_exe = pathlib.Path(shortcut.TargetPath).name
                process_list_executables.append(lnk_exe)
            else:
                process_list_executables.append(link)
    return process_list_executables


def make_accum_offset(eq_signs: list[int], word_num, row):
    if word_num > 0:
        return row[sum(eq_signs[:word_num - 1]):sum(eq_signs[:word_num])]
    else:
        return row[0:eq_signs[0]]


def map_output(row: str, eq_signs: list[int]):
    output = (
        make_accum_offset(eq_signs, 1, row),
        make_accum_offset(eq_signs, 2, row),
        make_accum_offset(eq_signs, 8, row)
    )
    for s in output:
        yield s.strip()


def cls_or_zero(obj, cls):
    try:
        return cls(obj)
    except ValueError:
        return 0


def process_generator():
    process_output = os.popen('tasklist /v').read().split('\n')
    proc_list = get_process_list()
    header_separator_index = next(i for i, line in enumerate(process_output) if '=' in line)
    out_processes_rows = process_output[header_separator_index + 1:]
    col_cnt = list(map(lambda eq: eq.count('=') + 1, process_output[header_separator_index].split()))
    for process_row in out_processes_rows:
        process_exe, pid, time_cpu = list(map_output(process_row, col_cnt))
        if process_exe not in proc_list:
            continue
        time_cpu = time_cpu.split(':')
        h_cpu = cls_or_zero(time_cpu[0], int) * 3600
        m_cpu = cls_or_zero(time_cpu[1], int) * 60
        s_cpu = cls_or_zero(time_cpu[2], int)
        start_time = datetime.datetime.now() - datetime.timedelta(
            seconds=h_cpu + m_cpu + s_cpu
        )
        yield process_exe, cls_or_zero(pid, int), start_time


def scan_processes():
    all_processes = []
    for process_exe, pid, start_time in process_generator():
        all_processes.append({'pid': pid, 'executable': process_exe, 'time': start_time})
    return all_processes


class ActiveProcessStream:
    last_scanned_pids: dict[int, str]

    def __init__(self, generator):
        self.generator = generator
        self.last_scanned_pids = {}

    def get_active_processes(self):
        active_pids = {}
        active_process_list = []
        for process_exe, pid, start_time in self.generator():
            active_pids[pid] = process_exe
            if self.last_scanned_pids.get(pid) != process_exe:
                active_process_list.append({'pid': pid, 'executable': process_exe, 'time': start_time})

        self.last_scanned_pids = active_pids
        return active_process_list

    def __call__(self, *args, **kwargs):
        return self.get_active_processes()


class TerminatedProcessStream:
    last_scanned_pids: dict[int, dict]

    def __init__(self, generator):
        self.last_scanned_pids = {}
        self.generator = generator

    def get_terminated_processes(self):
        active_pids = {}
        terminated_processes = []
        for process_exe, pid, start_time in self.generator():
            active_pids[pid] = {'executable': process_exe, 'time': start_time}
        for pid, process in self.last_scanned_pids.items():
            if active_pids.get(pid, {}).get('executable') != process.get('executable'):
                terminated_processes.append({'pid': pid, **process})
        self.last_scanned_pids = active_pids
        return terminated_processes

    def __call__(self, *args, **kwargs):
        return self.get_terminated_processes()


active_process_stream = ActiveProcessStream(process_generator)
terminated_process_stream = TerminatedProcessStream(process_generator)


def offset_to_end(log_desc):
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(log_desc, flags, 0)
    if not events:
        return 0
    return events[-1].RecordNumber


def scan_terminated_processes(log_desc):
    """
    Window's based solution, but it's not working properly because it's Windows :))
    Requires gpedit.msc setup
    """
    terminated_processes = []
    flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(log_desc, flags, 9999)

    for event in events:
        if event.EventID == 4689:
            event_info = event.StringInserts
            executable = pathlib.Path(event.StringInserts[6]).name

            if executable in get_process_list():
                print(executable, event.TimeGenerated, executable in get_process_list())
                terminated_processes.append(
                    {'executable': executable, 'pid': int(event_info[5], 16), 'time': event.TimeGenerated}
                )
    return {'processes': terminated_processes}


LOG_DESC = win32evtlog.OpenEventLog('localhost', 'Security')  # should be setup with gpedit.msc
offset_to_end(LOG_DESC)
