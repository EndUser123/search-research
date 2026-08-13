export function deserializeRecord(serialized) {
  const record = JSON.parse(serialized);
  return {
    id: record.id,
    name: record.name,
  };
}
