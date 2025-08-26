import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import { spawn } from 'child_process';
import kill from 'tree-kill';
import fetch from 'node-fetch';

// --- Helper to get __dirname in ESM ---
import { fileURLToPath } from 'url';
import { dirname } from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// --- Global variables ---
let mainWindow;
let loadingWindow;
let pyProc = null;
const pyPort = 8000;


// --- Creates the loading window shown during initialization ---
const createLoadingWindow = () => {
  loadingWindow = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    show: false
  });
  loadingWindow.loadFile(path.join(__dirname, 'loading.html'));
  loadingWindow.once('ready-to-show', () => {
    loadingWindow.show();
  });
};

// --- Creates the main application window ---
const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    show: false 
  });
  
  // --- Load the UI from the FastAPI server, explicitly using IPv4 ---
  mainWindow.loadURL(`http://127.0.0.1:${pyPort}`);

  // --- Show window only when it's ready to avoid a blank screen ---
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // --- Clean up when the window is closed ---
  mainWindow.on('closed', function() {
    mainWindow = null;
    // --- Ensure the Python process is terminated ---
    if (pyProc != null) {
      kill(pyProc.pid, 'SIGKILL'); 
      pyProc = null;
    }
  });
};

// --- Installs Python packages from requirements.txt ---
const installRequirements = () => {
  return new Promise((resolve, reject) => {
    // --- Determine Python executable path for packaged vs. dev environment ---
    const pythonPath = app.isPackaged
      ? path.join(process.resourcesPath, 'venv', 'Scripts', 'python.exe')
      : path.join(app.getAppPath(), 'venv', 'Scripts', 'python.exe');
    const reqPath = path.join(app.getAppPath(), 'App', 'requirements.txt');

    // --- Send initial progress to the loading window ---
    if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('progress', {
          percent: 0,
          status: 'Installing required packages...'
        });
    }

    const pip = spawn(pythonPath, ['-m', 'pip', 'install', '-r', reqPath]);
    
    // --- Simulate installation progress for better UX ---
    let progress = 0;
    const updateProgress = () => {
      progress = Math.min(progress + 5, 80); 
      if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('progress', {
          percent: progress,
          status: 'Installing packages...'
        });
      }
    };
    const progressInterval = setInterval(updateProgress, 500);

    // --- Relay stdout and stderr to the loading window and console ---
    pip.stdout.on('data', (data) => {
      const message = data.toString();
      console.log(message);
      if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('log', message);
      }
    });

    pip.stderr.on('data', (data) => {
      const message = data.toString();
      console.error(message);
      if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('log', message);
      }
    });

    // --- Resolve or reject the promise when pip process finishes ---
    pip.on('close', (code) => {
      clearInterval(progressInterval);
      if (code === 0) {
        if (loadingWindow && !loadingWindow.isDestroyed()) {
            loadingWindow.webContents.send('progress', {
              percent: 100,
              status: 'Installation completed!'
            });
        }
        console.log('Requirements installed successfully');
        resolve();
      } else {
        console.error(`pip process exited with code ${code}`);
        reject(new Error(`pip process exited with code ${code}`));
      }
    });
  });
};

// --- Starts the FastAPI server and waits for it to be fully ready ---
const startPythonServer = async () => {
  try {
    await installRequirements();

    // --- Define paths for the Python script ---
    const script = path.join(app.getAppPath(), 'App', 'main.py');
    const pythonPath = app.isPackaged
      ? path.join(process.resourcesPath, 'venv', 'Scripts', 'python.exe')
      : path.join(app.getAppPath(), 'venv', 'Scripts', 'python.exe');

    // --- Spawn the Python backend process ---
    pyProc = spawn(pythonPath, [script]);

    if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('progress', {
          percent: 90,
          status: 'Starting FastAPI server & loading models...'
        });
    }

    pyProc.stdout.on('data', (data) => {
      console.log(`Python stdout: ${data}`);
      if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('log', data.toString());
      }
    });

    // --- Wait until the server is fully initialized (including model loading) ---
    const serverReady = await new Promise((resolve) => {
      const onData = (data) => {
        const message = data.toString();
        console.error(`Python stderr: ${message}`);
        if (loadingWindow && !loadingWindow.isDestroyed()) {
          loadingWindow.webContents.send('log', message);
        }

        // --- Start polling the /status endpoint only after Uvicorn confirms it's running ---
        if (message.includes('Uvicorn running on')) {
          console.log('Uvicorn server is running. Starting status checks...');
          pyProc.stderr.removeListener('data', onData); // Prevent multiple listeners

          const checkStatus = setInterval(async () => {
            try {
              // --- Poll the /status endpoint using the IPv4 address ---
              const response = await fetch(`http://127.0.0.1:${pyPort}/status`);
              if (response.ok) {
                const data = await response.json();
                // --- Resolve only when the backend confirms models are loaded ---
                if (data.status === 'ready') {
                  console.log('Server and models are ready!');
                  clearInterval(checkStatus);
                  resolve(true);
                } else {
                  console.log('Server is running, but models are still loading...');
                }
              }
            } catch (error) {
              console.log('Waiting for server to respond...', error.message);
            }
          }, 2000); // Check every 2 seconds
        }
      };

      pyProc.stderr.on('data', onData);

      // --- Set a timeout for the entire readiness check ---
      setTimeout(() => {
        pyProc.stderr.removeListener('data', onData);
        console.error('Server readiness check timed out.');
        resolve(false);
      }, 300000); // 5-minute timeout
    });

    return serverReady;

  } catch (error) {
    console.error('Error during startup:', error);
    if (loadingWindow && !loadingWindow.isDestroyed()) {
        loadingWindow.webContents.send('log', `Error: ${error.message}`);
    }
    return false;
  }
};

// --- App's main entry point ---
app.on('ready', async () => {
      createLoadingWindow();
      
      const serverStarted = await startPythonServer();

      // --- If server starts successfully, close loading window and open main window ---
      if (serverStarted) {
        console.log("Server started successfully. Creating main window.");
        if (loadingWindow) {
          loadingWindow.close();
          loadingWindow = null;
        }
        createWindow();
      } else {
        // --- If server fails to start, show an error and quit ---
        console.error('Failed to start server.');
        dialog.showErrorBox('Server Error', 'Failed to start the backend server. The application will now close.');
        if (loadingWindow) {
          loadingWindow.close();
          loadingWindow = null;
        }
        app.quit();
      }
    });

// --- Quit the app when all windows are closed (except on macOS) ---
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (pyProc != null) {
      kill(pyProc.pid, 'SIGKILL');
      pyProc = null;
    }
    app.quit();
  }
});

// --- Re-create the window if the app is activated (macOS) ---
app.on('activate', () => {
  if (mainWindow === null) {  
    createWindow();
  }
});
