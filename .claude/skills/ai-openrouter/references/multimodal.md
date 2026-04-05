# Multimodal Support

## Image Understanding

```typescript
const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
    "Content-Type": "application/json",
    "HTTP-Referer": process.env.OPENROUTER_SITE_URL || "http://localhost:3000",
    "X-OpenRouter-Title": process.env.OPENROUTER_APP_NAME || "My App",
  },
  body: JSON.stringify({
    model: "google/gemini-2.5-flash",
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: "Extract all visible text from this image." },
          {
            type: "image_url",
            image_url: { url: imageDataUrl }, // base64:data:image/jpeg;base64,...
          },
        ],
      },
    ],
    temperature: 0,
  }),
})

const content = (await res.json())?.choices?.[0]?.message?.content
```

## Image Generation

```typescript
const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "google/gemini-3.1-flash-image-preview",
    messages: [
      {
        role: "user",
        content: "Generate a clean product-style illustration of a glass teacup on a plain background.",
      },
    ],
    modalities: ["image", "text"],
    image_config: { size: "1024x1024" },
  }),
})

const json = await res.json()
const imageUrl = json?.choices?.[0]?.message?.images?.[0]?.image_url?.url
```

## PDF Processing

```typescript
const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "google/gemini-2.5-flash",
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: "Extract the invoice totals as JSON." },
          {
            type: "file",
            file: {
              filename: "invoice.pdf",
              file_data: pdfDataUrl, // base64:data:application/pdf;base64,...
            },
          },
        ],
      },
    ],
    plugins: [
      {
        id: "file-parser",
        pdf: { engine: "pdf-text" }, // or "mistral-ocr" for scanned PDFs
      },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
  }),
})

const data = await res.json()
const totals = JSON.parse(data.choices[0].message.content)
```

**PDF Engine Options**:
- `pdf-text`: Clean text PDFs
- `mistral-ocr`: Scanned or image-heavy PDFs
- `native`: When model supports file input natively
