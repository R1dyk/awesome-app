const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const net = require('net');

let mainWindow;
let socket = null;
let connected = false;
let username = 'Anonymous';
let otherClients = [];
let targetClientId = null;
let sentCount = 0;
let receivedCount = 0;
let devMode = false;
let dataBuffer = '';

const SERVER_HOST = '10.32.73.31';
const SERVER_PORT = 12345;

const alerts = {
  'STOP': {
    message: "Stop Scrolling! 😊",
    bg: "#ff4500",
    gif_url: 'https://media1.tenor.com/m/DafLbvYgt50AAAAC/trump-donald-trump.gif'
  },
  'COLD': {
    message: "Turning off the AC, it's freezing! ❄️🥶❄️",
    bg: "#1e90ff",
    gif_url: 'https://media1.tenor.com/m/ShXWuFDDZ8wAAAAd/vtactor007-rwmartin.gif'
  },
  'ALERT1': {
    message: "Working hard!",
    bg: "#00ff00",
    gif_url: 'https://media1.tenor.com/m/yHhqdtTladoAAAAC/cat-typing-typing.gif'
  },
  'ALERT2': {
    message: "Hardly working!",
    bg: "#ffff00",
    gif_url: 'https://media1.tenor.com/m/3pwRCgEnqN8AAAAC/sleeping-at-work-fail.gif'
  },
  'ALERT3': {
    message: "Ansys!",
    bg: "#ff00ff",
    gif_url: 'https://media1.tenor.com/m/7zrtEDHtArcAAAAC/ronswanson-parksandrec.gif'
  },
};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  mainWindow.loadFile('index.html');
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (socket) socket.destroy();
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// Helper to extract first complete JSON object from a buffer string
function extractFirstJSONObject(buffer) {
  let i = 0;
  // Skip leading whitespace
  while (i < buffer.length && /\s/.test(buffer[i])) i++;
  if (i >= buffer.length || buffer[i] !== '{') return [null, buffer];

  let depth = 0;
  let inString = false;
  let escape = false;
  for (let j = i; j < buffer.length; j++) {
    const ch = buffer[j];
    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === '\\') {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }
    if (ch === '"') {
      inString = true;
    } else if (ch === '{') {
      depth++;
    } else if (ch === '}') {
      depth--;
      if (depth === 0) {
        const jsonText = buffer.slice(i, j + 1);
        try {
          const obj = JSON.parse(jsonText);
          const rest = buffer.slice(j + 1);
          return [obj, rest];
        } catch {
          return [null, buffer];
        }
      }
    }
  }
  return [null, buffer];
}

// IPC handlers for UI-python like logic
ipcMain.handle('connect-to-server', async (event, { host, isDev }) => {
  devMode = !!isDev;
  if (devMode) {
    // Offline dev mode; don't mark connected
    if (socket) {
      try { socket.destroy(); } catch {}
    }
    socket = null;
    connected = false;
    mainWindow?.webContents.send('update-status', 'Developer Mode - Offline');
    return { success: true, message: 'Developer Mode - Offline' };
  }
  try {
    socket = new net.Socket();
    dataBuffer = '';
    await new Promise((resolve, reject) => {
      socket.connect(SERVER_PORT, SERVER_HOST, () => {
        connected = true;
        mainWindow?.webContents.send('update-status', `Connected to server ${SERVER_HOST}:${SERVER_PORT}`);
        resolve();
      });
      socket.on('error', reject);
    });
    socket.on('data', (chunk) => {
      dataBuffer += chunk.toString();
      while (true) {
        const [obj, rest] = extractFirstJSONObject(dataBuffer);
        if (!obj) break;
        dataBuffer = rest;
        try {
          processReceivedMessage(obj);
        } catch (e) {
          console.error('Processing error:', e);
        }
      }
    });
    socket.on('close', () => {
      connected = false;
      mainWindow?.webContents.send('update-status', 'Disconnected');
    });
    requestClientList();
    return { success: true, message: 'Connected to server' };
  } catch (e) {
    connected = false;
    return { success: false, message: `Failed to connect: ${e.message}` };
  }
});

ipcMain.handle('set-username', (event, newUsername) => {
  username = newUsername || 'Anonymous';
  if (connected) {
    sendMessage({ type: 'SET_USERNAME', username });
  }
  return username;
});

ipcMain.handle('send-alert', (event, alertType) => {
  sentCount++;
  if (devMode || !connected) {
    showPopup(alerts[alertType]);
  } else {
    // Send legacy raw string so Python server treats it as legacy alert
    try {
      socket.write(String(alertType));
    } catch (e) {
      console.error('Failed to send alert:', e);
    }
  }
  mainWindow?.webContents.send('update-counters', { sent: sentCount, received: receivedCount });
});

ipcMain.handle('send-custom', (event, { msg, gif }) => {
  if (!msg || msg === 'Enter custom message') return;
  sentCount++;
  const colors = ['#ff4500', '#1e90ff', '#00ff00', '#ffff00', '#ff00ff'];
  const bg = colors[Math.floor(Math.random() * colors.length)];
  const gifUrl = gif && gif !== 'GIF URL (optional)' ? gif : null;
  if (devMode || !connected) {
    showPopup({ message: msg, bg, gif_url: gifUrl });
  } else {
    sendMessage({
      type: 'CUSTOM',
      message: msg,
      bg,
      gif_url: gifUrl,
      target_id: targetClientId
    });
  }
  mainWindow?.webContents.send('update-counters', { sent: sentCount, received: receivedCount });
});

ipcMain.handle('set-target', (event, id) => {
  targetClientId = id ? Number(id) : null;
});

ipcMain.handle('request-client-list', () => {
  if (connected) requestClientList();
});

function sendMessage(data) {
  if (socket && connected) {
    try {
      socket.write(JSON.stringify(data));
    } catch (e) {
      console.error('Failed to send message:', e);
    }
  }
}

function requestClientList() {
  sendMessage({ type: 'CLIENT_LIST_REQUEST' });
}

function processReceivedMessage(messageData) {
  const type = messageData.type;
  if (type === 'CUSTOM' || type === 'LEGACY_ALERT') {
    receivedCount++;
    const sender = messageData.sender_username || 'Unknown';
    let alertInfo;
    if (type === 'CUSTOM') {
      alertInfo = {
        message: `From ${sender}:\n${messageData.message}`,
        bg: messageData.bg,
        gif_url: messageData.gif_url
      };
    } else {
      const base = alerts[messageData.alert_type] || { message: messageData.alert_type, bg: '#333', gif_url: null };
      alertInfo = {
        message: `From ${sender}:\n${base.message}`,
        bg: base.bg,
        gif_url: base.gif_url
      };
    }
    showPopup(alertInfo);
    mainWindow?.webContents.send('update-counters', { sent: sentCount, received: receivedCount });
  } else if (type === 'CLIENT_LIST_RESPONSE') {
    otherClients = messageData.clients || [];
    mainWindow?.webContents.send('update-client-list', otherClients);
  }
}

function showPopup(info) {
  const popup = new BrowserWindow({
    width: 800,
    height: 600,
    alwaysOnTop: true,
    frame: false,
    transparent: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  });
  popup.loadFile('popup.html');
  popup.webContents.on('did-finish-load', () => {
    popup.webContents.send('show-alert', info);
  });
}