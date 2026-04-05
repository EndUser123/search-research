import asyncio
import httpx

async def check_headers():
    client = httpx.AsyncClient()
    r = await client.get('https://example.com', follow_redirects=True)
    print('Headers:', dict(r.headers))
    print('Content-Length:', r.headers.get('content-length'))
    print('Content length of text:', len(r.text))
    await client.aclose()

asyncio.run(check_headers())
