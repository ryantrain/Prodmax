const { app, BrowserWindow , Menu} = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let pythonProcess = null;

// Menu.setApplicationMenu(null);

const createWindow = () => {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        titleBarOverlay: {
            color: '#3b3b3b',
            symbolColor: '#FFFFFF',
            height: 32,
        },
    });

    //   win.setMenu(null);
   
    win.loadFile('templates/login.html')
};

function StartMainWindow() {
    waitForPythonServer(() => {
        createWindow();
    })
}

app.whenReady().then(() => {
    StartPythonServer();
    StartMainWindow();
});

// async function fetchWithError (url, options, retries = 5) {
//     try {
//         const response = await fetch(url, options);
//         return await response.json();
//     } catch (error) {
//         if (retries > 0) {
//             await new Promise(resolve => setTimeout(resolve, 250));
//             return fetchWithError(url, options, retries - 1);
//         }
//         throw error;
//     }
// }

function StartPythonServer() {
    pythonProcess = spawn('python', ['-m', 'uvicorn', 'server:app', '--port', '8000', '--host', '127.0.0.1']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python: ${data.toString()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`PYTHON CRASHED/LOGGED: ${data.toString()}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process stopped automatically with exit code: ${code}`);
    });

}

function waitForPythonServer(callback, retries = 20) {
    fetch('http://127.0.0.1:8000').then(callback).catch(() => {
        if (retries > 0) setTimeout(() => waitForPythonServer(callback, retries -1), 250);
    })
}

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});