export class ProcessDTO {
    /** @type {BigInteger} */
    pid;
    /** @type {String} */
    executable;
    /** @type {string | null} */
    time = null;

    constructor(data = null) {
        this.executable = data?.executable;
        this.pid = data?.pid;
        this.time = data?.time;
    }
}


export class ProcessListDTO {
    /** @type {Array<ProcessDTO>} */
    processes;

    constructor(data) {
        this.processes = [];
        if (data) {
            for (let process of data.processes) {
                this.pushEvent(new ProcessDTO(process));
            }
            this.processes = data.processes;
        }
    }

    /** @param processList {ProcessListDTO} */
    reapply(processList) {
        let newProcesses = [];
        processList.processes.forEach((entry) => {
            let newProcess = this.pushEvent(entry);
        });
        for (const [idx, entry] of Object.entries(this.processes)) {
            if (!newProcesses.includes(entry)) {
                this.processes.splice(idx, 1);
            }
        }
        this.sort();
        return newProcesses;
    }

    sort() {
        this.processes.sort((a, b) => {
            return a.pid - b.pid;
        });
    }

    /** @param event {ProcessDTO} */
    pushEvent(event) {
        if (this.processes.length === 0) {
            this.processes.push(event);
            return event;
        }
        let mutated = false;
        for (const [idx, selfProcess] of Object.entries(this.processes)) {
            if (event.pid === selfProcess.pid) {
                this.processes[idx].executable = event.executable;
                mutated = true;
            }
        }
        if (!mutated) {
            this.processes.push(event);
            return event;
        }
    }
}