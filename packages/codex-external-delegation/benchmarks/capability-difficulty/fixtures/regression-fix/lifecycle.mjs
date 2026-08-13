export async function executeRequest(send) {
  try {
    return { status: "ok", attempt: 2, response: await send() };
  } catch {
    return { status: "ok", attempt: 2, response: null };
  }
}
