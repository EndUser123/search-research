// Detached restart helper: waits 2s for old process to release the port,
// then launches start-proxy.bat. Spawned as detached by the /restart-proxy endpoint.
const { spawn } = require("child_process");
const path = require("path");

setTimeout(() => {
    const bat = path.join(__dirname, "start-proxy.bat");
    const child = spawn("cmd.exe", ["/c", bat], {
        detached: true,
        stdio: "ignore",
        cwd: "P:\\",
    });
    child.unref();
    process.exit(0);
}, 2000);
