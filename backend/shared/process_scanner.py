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


def scan_processes():
    delta_pids = []
    cur_pids = []
    process_output = os.popen('tasklist /v').read().split('\n')
    proc_list = get_process_list()
    out_processes_rows = process_output[3:]
    col_cnt = list(map(lambda eq: eq.count('=') + 1, process_output[2].split()))
    for process_row in out_processes_rows:
        process_exe, pid, time_cpu = list(map_output(process_row, col_cnt))
        if process_exe not in proc_list:
            continue
        if last_scanned_pids.get(pid) != process_exe:
            h_cpu = int(time_cpu.split(':')[0]) * 3600
            m_cpu = int(time_cpu.split(':')[1]) * 60
            s_cpu = int(time_cpu.split(':')[2])
            start_time = datetime.datetime.now() - datetime.timedelta(
                seconds=h_cpu + m_cpu + s_cpu
            )
            delta_pids.append({'pid': pid, 'executable': process_exe, 'time': start_time})
        cur_pids.append({'executable': process_exe, 'process_state': {'state': 'running', 'pid': int(pid)}})
    for proc in get_process_list():
        if proc not in map(lambda p: p['executable'], cur_pids):
            cur_pids.append({'executable': proc, 'process_state': {'state': 'idle', 'pid': None}})
    return {'delta': delta_pids, 'all': cur_pids}


def offset_to_end(log_desc):
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(log_desc, flags, 0)
    if not events:
        return 0
    return events[-1].RecordNumber


def scan_terminated_processes(log_desc):
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
