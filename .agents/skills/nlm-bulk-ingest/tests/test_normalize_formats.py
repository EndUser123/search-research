"""Smoke-test nlm-bulk-ingest's normalize.py on non-YT input shapes.

Tests: csv, jsonl, json-array, url-list, rss
Does NOT test: actual clustering or ingestion (those require API quota).
Goal: surface parser bugs in normalize.py for each supported format.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path("P:/.agents/skills/nlm-bulk-ingest/scripts/normalize.py")
PASS = 0
FAIL = 0


def run_normalize(input_path: Path, fmt: str = "auto", drop_dead=False, extra_args=None):
    out = input_path.with_suffix(".canonical.jsonl")
    cmd = ["python", str(SCRIPT), str(input_path), "--format", fmt, "-o", str(out)]
    if drop_dead:
        cmd.append("--drop-dead")
    if extra_args:
        cmd.extend(extra_args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8")
    return r, out


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} — {detail}")


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- CSV ---
def test_csv():
    print("\n=== CSV format ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        csv_path = td / "test.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["title", "url", "author"])
            w.writerow(["First Post", "https://example.com/1", "Alice"])
            w.writerow(["Second Post", "https://example.com/2", "Bob"])
            w.writerow(["Duplicate URL", "https://example.com/1", "Charlie"])  # dup URL
        r, out = run_normalize(csv_path, "csv")
        check("csv parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("csv produces 3 items (1 dup URL)", len(items) == 3, f"got {len(items)}")
        check("csv extracts title", items[0].get("title") == "First Post", str(items[0]))
        check("csv extracts url", items[0].get("url") == "https://example.com/1")
        check("csv extracts source from author col", items[0].get("source") == "Alice",
              f"got source={items[0].get('source')!r}")


# --- JSONL ---
def test_jsonl():
    print("\n=== JSONL format ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "test.jsonl"
        p.write_text(
            '{"link": "https://x.com/1", "name": "Item One", "author": "X"}\n'
            '{"link": "https://x.com/2", "name": "Item Two", "author": "Y"}\n',
            encoding="utf-8")
        r, out = run_normalize(p, "jsonl",
                                extra_args=["--url-field", "link", "--title-field", "name", "--source-field", "author"])
        check("jsonl parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("jsonl produces 2 items", len(items) == 2, f"got {len(items)}")
        check("jsonl field mapping works", items[0].get("title") == "Item One",
              str(items[0]))


# --- JSON-array ---
def test_json_array():
    print("\n=== JSON-array format ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "test.json"
        p.write_text(json.dumps([
            {"url": "https://a.com/1", "title": "A1"},
            {"url": "https://a.com/2", "title": "A2"},
        ]), encoding="utf-8")
        r, out = run_normalize(p, "json-array")
        check("json-array parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("json-array produces 2 items", len(items) == 2, f"got {len(items)}")
        check("json-array extracts fields", items[0].get("title") == "A1")


# --- URL list ---
def test_url_list():
    print("\n=== URL-list format ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "urls.txt"
        p.write_text(
            "https://example.com/page1\n"
            "# this is a comment, should be skipped\n"
            "\n"
            "https://example.com/page2\n"
            "https://other.com/foo\n",
            encoding="utf-8")
        r, out = run_normalize(p, "url-list")
        check("url-list parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("url-list produces 3 items (1 comment skipped)", len(items) == 3,
              f"got {len(items)}")
        check("url-list derives title from path", "page1" in items[0].get("title", ""),
              str(items[0]))
        check("url-list derives source from domain", items[0].get("source") == "example.com",
              str(items[0]))


# --- RSS ---
def test_rss():
    print("\n=== RSS format ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "feed.xml"
        p.write_text("""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>First Article</title>
      <link>https://feed.example.com/1</link>
      <guid>guid-1</guid>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://feed.example.com/2</link>
      <guid>guid-2</guid>
    </item>
  </channel>
</rss>""", encoding="utf-8")
        r, out = run_normalize(p, "rss")
        check("rss parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("rss produces 2 items", len(items) == 2, f"got {len(items)}")
        check("rss extracts title", items[0].get("title") == "First Article", str(items[0]))
        check("rss extracts url", items[0].get("url") == "https://feed.example.com/1")


# --- drop-dead flag ---
def test_drop_dead():
    print("\n=== --drop-dead flag ===")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "mixed.json"
        p.write_text(json.dumps([
            {"url": "https://x.com/1", "title": "Live one", "channel": "real_channel"},
            {"url": "https://x.com/2", "title": "[Deleted video]", "channel": "[unknown]"},
            {"url": "", "title": "No URL", "channel": "x"},
        ]), encoding="utf-8")
        r, out = run_normalize(p, "json-array", drop_dead=True)
        check("drop-dead parses rc=0", r.returncode == 0, r.stderr[:200])
        items = load_jsonl(out)
        check("drop-dead keeps only 1 (others filtered)", len(items) == 1,
              f"got {len(items)}: {items}")


# --- auto-detect ---
def test_auto_detect():
    print("\n=== auto-detect ===")
    # .csv → csv
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        csv_p = td / "x.csv"
        with csv_p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["url"])
            w.writerow(["https://auto.csv"])
        r1, _ = run_normalize(csv_p, "auto")
        check("auto-detects .csv as csv", r1.returncode == 0, r1.stderr[:200])

        # .json array → json-array
        json_p = td / "x.json"
        json_p.write_text('[{"url":"https://auto.json","title":"x"}]', encoding="utf-8")
        r2, _ = run_normalize(json_p, "auto")
        check("auto-detects .json array", r2.returncode == 0, r2.stderr[:200])

        # .txt with URLs → url-list
        txt_p = td / "x.txt"
        txt_p.write_text("https://auto.txt\n", encoding="utf-8")
        r3, _ = run_normalize(txt_p, "auto")
        check("auto-detects .txt as url-list", r3.returncode == 0, r3.stderr[:200])


if __name__ == "__main__":
    test_csv()
    test_jsonl()
    test_json_array()
    test_url_list()
    test_rss()
    test_drop_dead()
    test_auto_detect()
    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
