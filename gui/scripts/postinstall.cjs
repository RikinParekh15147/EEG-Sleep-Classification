const fs=require('node:fs');const path=require('node:path');
fs.writeFileSync(path.resolve(__dirname,'../node_modules/.sleep-platform'),process.platform+'-'+process.arch);
