export function parseList(value) {
  return String(value).split(",").map((part) => part.trim());
}
