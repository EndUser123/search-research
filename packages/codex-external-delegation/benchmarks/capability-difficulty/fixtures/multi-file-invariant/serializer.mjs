export function serializeRecord(record) {
  return JSON.stringify({
    version: 1,
    id: record.id,
    name: record.name,
  });
}
