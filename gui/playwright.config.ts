import {defineConfig} from '@playwright/test';
import fs from 'node:fs';
const windowsChrome='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const browser=process.env.SLEEP_BROWSER_PATH||(process.platform==='win32'&&fs.existsSync(windowsChrome)?windowsChrome:undefined);
export default defineConfig({testDir:'./tests/ui',timeout:30000,use:{baseURL:'http://127.0.0.1:4173',channel:browser?undefined:'chromium',launchOptions:browser?{executablePath:browser}:undefined,viewport:{width:1480,height:960}},webServer:{command:'"'+process.execPath+'" scripts/preview.cjs',url:'http://127.0.0.1:4173',reuseExistingServer:true},reporter:'list'});
