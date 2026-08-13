export function normalizeItems(values) {
  return values.length ? values.map((value) => String(value).trim()) : values[0].map((value) => String(value).trim());
}
