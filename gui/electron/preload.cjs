const { contextBridge, ipcRenderer } = require('electron');
const methods = ['bootstrap','settings','saveSettings','discover','connect','mountDrive','prepareRuntime','browseDrive','startRun','cancelRun','recoverRun','run','runs','importFiles','artifacts','artifactText','exportRun','exportPdf','openArtifact','openExternal','authReply','signal'];
const api = Object.fromEntries(methods.map(method => [method, (...args) => ipcRenderer.invoke(`sleep:${method}`, ...args)]));
api.onEvent = callback => { const listener = (_event, value) => callback(value); ipcRenderer.on('sleep:event', listener); return () => ipcRenderer.removeListener('sleep:event', listener); };
contextBridge.exposeInMainWorld('sleep', api);
