export class AsyncCache {
  constructor() {
    this.values = new Map();
  }

  async get(key, loader, { signal } = {}) {
    if (this.values.has(key)) return this.values.get(key);
    const value = await loader({ signal });
    this.values.set(key, value);
    return value;
  }
}
