export function createRequest(path, options = {}) {
  return {
    path: String(path),
    timeoutMs: Number(options.timeoutMs || 5000),
  };
}
