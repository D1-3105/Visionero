import './App.css';
import {ProcessListDTO} from './ProcessDTO.js'
import {Component, useEffect, useState} from "react";


const socketDead = new WebSocket('ws://127.0.0.1:8005/dead_processes/stream');
const socketActive = new WebSocket('ws://127.0.0.1:8005/live_processes/stream');


/** @param process {ProcessDTO} */
function ProcessEventComponent(idx, process) {
    return (
        <tr key={idx}>
            <td>
                {process.pid}
            </td>
            <td>
                {process.executable}
            </td>
            <td>
                {process.time}
            </td>
        </tr>
    );
}


class ProcessTable extends Component {
    constructor(props) {
        super(props);
        this.state = {processList: this.props.processList};
    }

    tableBody() {
        const processList = this.state.processList;
        let rows = [];
        for (const [idx, entry] of Object.entries(processList.processes)) {
            rows.push(ProcessEventComponent(idx, entry));
        }
        return (
            <tbody>
            {rows}
            </tbody>
        );
    }

    render() {
        return (
            <table id={this.props.id} className={'process-grid'}>
                <thead>
                <tr>
                    <td>PID</td>
                    <td>Executable</td>
                    <td>Time</td>
                </tr>
                </thead>
                {this.tableBody()}
            </table>
        );
    }
}


function setProcessState(event, oldProcessList, setStreamProcessList) {
    console.log(event.data);
    let validatedEventData = new ProcessListDTO(JSON.parse(event.data));
    if (validatedEventData.processes.length > 0) {
        let updatedList = new ProcessListDTO(oldProcessList); // Create a new instance or clone
        updatedList.reapply(validatedEventData);
        updatedList.sort();
        setStreamProcessList(updatedList); // Update state with the new instance
        console.log(updatedList);
    }

}


function App() {

    const [StreamDeadProcessList, setStreamDeadProcessList] = useState(new ProcessListDTO({processes: []}));
    const [StreamLiveProcessList, setStreamLiveProcessList] = useState(new ProcessListDTO({processes: []}));
    useEffect(() => {
        socketDead.onopen = () => console.log("Successfully opened Dead Stream!");
        socketActive.onopen = () => console.log("Successfully opened Active Stream!");

        const onDeadMessage = (event) => {
            setProcessState(event, StreamDeadProcessList, setStreamDeadProcessList);
        };

        const onActiveMessage = (event) => {
           setProcessState(event, StreamLiveProcessList, setStreamLiveProcessList);
        };

        socketDead.onmessage = onDeadMessage;
        socketActive.onmessage = onActiveMessage;

        return () => {
            //socketActive.onopen = null;
            //socketActive.onmessage = null;
            socketDead.onopen = null;
            socketDead.onmessage = null;
        };
    }, []);


    return (
        <div>
            <div>
                <h1>Завершённые процессы</h1>
                <ProcessTable processList={StreamDeadProcessList} id={'eventTable-Dead'}/>
            </div>
            <div>
                <h1>Активные процессы</h1>
                <ProcessTable processList={StreamLiveProcessList} id={'eventTable-Dead'}/>
            </div>

        </div>
    );
}


export default App;
