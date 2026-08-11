/**
 * Links panel — extracts and displays URLs from the video description.
 */

interface LinkEntry {
  url: string;
  label: string;
}

function extractLinks(description: string): LinkEntry[] {
  const links: LinkEntry[] = [];
  const seen = new Set<string>();

  const urlRegex = /(https?:\/\/[^\s<>"']+)/g;
  let m: RegExpExecArray | null;
  while ((m = urlRegex.exec(description)) !== null) {
    const url = (m[1] ?? "").replace(/[),.;]+$/, "");
    if (seen.has(url)) continue;
    seen.add(url);

    let label = url;
    try {
      const u = new URL(url);
      const host = u.hostname.replace(/^www\./, "");
      const path = u.pathname === "/" ? "" : u.pathname.slice(0, 30);
      label = host + path;
      if (u.searchParams.has("q")) {
        label += ` (search: ${u.searchParams.get("q")})`;
      }
    } catch {
      // keep raw url as label
    }

    links.push({ url, label });
  }

  return links;
}

export function renderLinks(
  container: HTMLElement,
  description: string | null,
): void {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  if (!description) {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "No description available";
    container.appendChild(empty);
    return;
  }

  const links = extractLinks(description);
  if (links.length === 0) {
    const empty = document.createElement("div");
    empty.className = "ytws-empty";
    empty.textContent = "No links found in description";
    container.appendChild(empty);
    return;
  }

  const header = document.createElement("div");
  header.className = "ytws-links-header";
  header.textContent = `${links.length} link${links.length > 1 ? "s" : ""} found`;
  container.appendChild(header);

  for (const link of links) {
    const anchor = document.createElement("a");
    anchor.href = link.url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    anchor.className = "ytws-link";
    anchor.textContent = link.label;
    container.appendChild(anchor);
  }
}
