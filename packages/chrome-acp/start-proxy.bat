@echo off
cd /d "P:\"
"C:\Program Files\nodejs\node.exe" "C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\cli\bin.js" --no-auth --port 9315 grok agent -- --always-approve stdio
