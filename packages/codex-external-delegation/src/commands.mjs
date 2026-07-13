export function commandName(worker, platform = process.platform) {
  if (platform !== "win32") return worker;
  return `${worker}.cmd`;
}

function quoteCmdArg(value) {
  const text = String(value);
  if (text.length === 0) return '""';
  if (!/[\s"&|<>^%]/.test(text)) return text;
  return `"${text.replace(/(["^])/g, "^$1")}"`;
}

export function spawnSpec(command, args, { platform = process.platform, comspec = process.env.ComSpec || "cmd.exe" } = {}) {
  if (platform !== "win32") return { command, args };
  return {
    command: comspec,
    args: ["/d", "/s", "/c", `call ${[command, ...args].map(quoteCmdArg).join(" ")}`],
  };
}

export function buildCommand(packet, prompt, { platform = process.platform } = {}) {
  const cwd = packet.isolated_cwd || packet.cwd;
  const agent = packet.agent || (packet.mode === "read_only" ? "external-readonly-primary" : "external-writer");
  const args = [];

  if (packet.worker === "pi") {
    args.push("-p", "--no-session", "--mode", "json", "--model", packet.model);
    if (packet.mode === "read_only") {
      args.push("--thinking", "off", "--tools", "read,grep,find,ls");
    } else {
      args.push("--thinking", packet.thinking || "low");
    }
  } else if (packet.worker === "opencode") {
    args.push("run", "--format", "json", "--model", packet.model, "--agent", agent, "--dir", cwd);
    if (packet.variant) args.push("--variant", packet.variant);
  } else {
    throw new Error(`Unsupported worker: ${packet.worker}`);
  }

  return { command: commandName(packet.worker, platform), args, cwd, stdin: prompt };
}
