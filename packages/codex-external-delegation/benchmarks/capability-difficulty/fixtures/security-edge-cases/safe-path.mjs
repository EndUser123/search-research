import { resolve } from "node:path";

export async function resolveSafePath(root, requested) {
  return { path: resolve(root, requested), reason: null };
}
