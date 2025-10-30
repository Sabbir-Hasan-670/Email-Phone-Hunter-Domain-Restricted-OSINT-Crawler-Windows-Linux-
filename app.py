# src/email_hunter/app.py
# Email/Phone Hunter – domain-restricted OSINT crawler (Windows + Linux)
# Features: domain-filtered emails, optional phones, HTML+PDF parsing, robots toggle, external follow, UA rotation, CSV output.

import argparse, csv, re, sys, time, datetime, collections, io, random
from typing import Set, Dict, Tuple
from urllib.parse import urljoin, urlparse
import urllib.robotparser as robotparser

import requests
from bs4 import BeautifulSoup

# Optional PDF parsing
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDF_OK = True
except Exception:
    PDF_OK = False

EMAIL_RE = re.compile(r'(?i)\b[A-Z0-9._%+\-]+@([A-Z0-9.\-]+\.[A-Z]{2,})\b')
PHONE_RE = re.compile(r'(?:(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{2,4}\)?[\s\-\.]?)?\d{3,4}[\s\-\.]?\d{3,4})')

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]

SNIP_LEN = 160

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def normalize_email(e: str) -> str:
    return e.strip().strip('.,;:!?"\'()[]{}<>').lower()

def domain_allowed(host: str, allowed_suffixes: Set[str]) -> bool:
    host = (host or "").lower()
    return any(host == d or host.endswith("." + d) for d in allowed_suffixes)

def email_matches_allowed(email: str, allowed_suffixes: Set[str]) -> bool:
    if "@" not in email: return False
    dom = email.split("@", 1)[1].lower()
    return any(dom == d or dom.endswith("." + d) for d in allowed_suffixes)

def load_robots(origin: str, ua: str, robots_cache: Dict[str, robotparser.RobotFileParser], verbose=False):
    rp = robots_cache.get(origin)
    if rp is None:
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(origin + "/robots.txt"); rp.read()
            if verbose: print(f"[robots] loaded {origin}/robots.txt")
        except Exception:
            if verbose: print(f"[robots] failed {origin}/robots.txt (default allow)")
        robots_cache[origin] = rp
    return rp

def can_fetch(robots_cache, url, ua, honor_robots=True, verbose=False):
    if not honor_robots:
        return True
    p = urlparse(url)
    if p.scheme not in ("http","https") or not p.netloc: return False
    rp = load_robots(f"{p.scheme}://{p.netloc}", ua, robots_cache, verbose)
    try:
        ok = rp.can_fetch(ua, url)
        if verbose and not ok: print(f"[skip] robots disallow: {url}")
        return ok
    except Exception:
        return True

def make_client(user_agent: str | None = None):
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent or random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    })
    try:
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        retries = Retry(total=3, connect=2, read=2, backoff_factor=0.6,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=False)
        s.mount("http://", HTTPAdapter(max_retries=retries))
        s.mount("https://", HTTPAdapter(max_retries=retries))
    except Exception:
        pass
    return s

def is_content_html(ct: str) -> bool:
    ct = (ct or "").lower()
    return "text/html" in ct or "application/xhtml" in ct

def is_content_pdf(ct: str) -> bool:
    ct = (ct or "").lower()
    return "application/pdf" in ct or ct.endswith("/pdf")

def title_of(soup: BeautifulSoup) -> str:
    t = soup.find("title")
    return (t.get_text(strip=True) if t else "")[:140]

def snippet_around(text: str, needle: str) -> str:
    if not text: return ""
    i = text.lower().find(needle.lower())
    if i == -1: return ""
    start = max(0, i - SNIP_LEN//2); end = min(len(text), i + len(needle) + SNIP_LEN//2)
    return " ".join(text[start:end].split())

def extract_emails(text: str, allowed: Set[str]) -> Set[str]:
    hits = set()
    if not text: return hits
    for m in EMAIL_RE.finditer(text):
        email = normalize_email(m.group(0))
        if email_matches_allowed(email, allowed):
            hits.add(email)
    return hits

def extract_phones(text: str) -> Set[str]:
    if not text: return set()
    raw = set(x.strip() for x in PHONE_RE.findall(text))
    cleaned = set()
    for p in raw:
        p2 = re.sub(r"[^\d+]", "", p)
        digits = re.sub(r"\D", "", p2)
        if len(digits) >= 8:
            cleaned.add(p)
    return cleaned

def handle_html(resp_text: str, base_url: str, depth: int, max_depth: int) -> tuple[str,str,list[str]]:
    soup = BeautifulSoup(resp_text, "html.parser")
    page_title = title_of(soup)
    page_text = soup.get_text(separator=" ", strip=True)
    for a in soup.select('a[href^="mailto:"]'):
        href = a.get("href", "")
        email = href.replace("mailto:", "").split("?", 1)[0]
        page_text += " " + email
    out_links = []
    if depth < max_depth:
        for a in soup.find_all("a", href=True):
            nxt = urljoin(base_url, a["href"])
            out_links.append(nxt)
    return page_title, page_text, out_links

def handle_pdf(content: bytes) -> str:
    if not PDF_OK: return ""
    try:
        return pdf_extract_text(io.BytesIO(content)) or ""
    except Exception:
        return ""

def main(argv=None):
    ap = argparse.ArgumentParser(description="Email/Phone Hunter (domain-restricted)")
    ap.add_argument("--domains", nargs="+", required=True, help="Allowed base domains; only emails ending with these are recorded (subdomains allowed).")
    ap.add_argument("--start-urls", nargs="+", required=True, help="Seed URLs to fetch first.")
    ap.add_argument("--output", default="findings.csv", help="CSV output (default: findings.csv)")
    ap.add_argument("--max-pages", type=int, default=80, help="Max total pages to fetch")
    ap.add_argument("--depth", type=int, default=1, help="Link-follow depth")
    ap.add_argument("--rate", type=float, default=1.0, help="Seconds between requests (be polite)")
    ap.add_argument("--include-pdfs", action="store_true", help="Parse PDFs (requires pdfminer.six)")
    ap.add_argument("--include-phones", action="store_true", help="Also extract phone numbers")
    ap.add_argument("--honor-robots", choices=["true","false"], default="true", help="Respect robots.txt (default true)")
    ap.add_argument("--external-follow", action="store_true", help="Allow following links to other sites (emails still filtered to allowed domains)")
    ap.add_argument("--user-agent", default=None, help="Custom UA string; rotates real browser UAs if omitted")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = ap.parse_args(argv)

    allowed: Set[str] = set(d.lower() for d in args.domains if d.strip())
    honor = (args.honor_robots.lower() == "true")

    if args.include_pdfs and not PDF_OK:
        print("[WARN] --include-pdfs requested but pdfminer.six not installed. Run: pip install -U pdfminer.six", file=sys.stderr)

    s = make_client(args.user_agent)
    robots_cache: Dict[str, robotparser.RobotFileParser] = {}

    queue: collections.deque[Tuple[str,int]] = collections.deque()
    seen_urls: Set[str] = set()
    results = []
    emails_best: Dict[str, dict] = {}

    for u in args.start_urls:
        try:
            pu = urlparse(u)
        except Exception:
            continue
        if pu.scheme in ("http","https"):
            queue.append((u, 0))

    pages = 0
    while queue and pages < args.max_pages:
        url0, depth = queue.popleft()
        if url0 in seen_urls: continue
        seen_urls.add(url0)

        if honor and not can_fetch(robots_cache, url0, s.headers.get("User-Agent","Mozilla"), honor_robots=True, verbose=args.verbose):
            continue

        try:
            resp = s.get(url0, timeout=15, allow_redirects=True)
        except Exception as e:
            if args.verbose: print(f"[skip] fetch error {url0}: {e}")
            continue

        time.sleep(args.rate)

        if resp.status_code != 200:
            if args.verbose: print(f"[skip] HTTP {resp.status_code}: {url0}")
            continue

        final = urlparse(resp.url)
        ct = resp.headers.get("Content-Type","").lower()
        page_title, page_text = "", ""
        out_links = []

        if is_content_html(ct):
            page_title, page_text, out_links = handle_html(resp.text, resp.url, depth, args.depth)
        elif args.include_pdfs and is_content_pdf(ct):
            page_title = "(PDF)"
            page_text = handle_pdf(resp.content)
        else:
            if args.verbose: print(f"[skip] unsupported content-type {ct}: {resp.url}")
            continue

        pages += 1
        if args.verbose: print(f"[ok ] {pages:4d} {resp.url}")

        filtered_links = []
        if depth < args.depth:
            for nxt in out_links:
                if nxt in seen_urls: continue
                p = urlparse(nxt)
                if p.scheme not in ("http","https"): continue
                if args.external_follow or domain_allowed(p.netloc, allowed):
                    filtered_links.append(nxt)
        for nxt in filtered_links:
            queue.append((nxt, depth + 1))

        for email in extract_emails(page_text, allowed):
            rec = {
                "type": "email",
                "value": email,
                "domain": email.split("@",1)[1],
                "source_url": resp.url,
                "source_type": "pdf" if page_title == "(PDF)" else "html",
                "page_title": page_title,
                "snippet": snippet_around(page_text, email),
                "first_seen": now_iso(),
            }
            if email not in emails_best:
                emails_best[email] = rec

        if args.include_phones:
            for ph in extract_phones(page_text):
                results.append({
                    "type": "phone",
                    "value": ph,
                    "domain": "",
                    "source_url": resp.url,
                    "source_type": "pdf" if page_title == "(PDF)" else "html",
                    "page_title": page_title,
                    "snippet": snippet_around(page_text, ph),
                    "first_seen": now_iso(),
                })

    for rec in emails_best.values():
        results.append(rec)

    if not results:
        results.append({
            "type": "info",
            "value": "no_hits",
            "domain": "",
            "source_url": "",
            "source_type": "",
            "page_title": "",
            "snippet": "No emails/phones matched. Try --external-follow, --include-pdfs, --include-phones, a real browser UA, smaller depth, different seeds.",
            "first_seen": now_iso(),
        })

    try:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "type","value","domain","source_url","source_type","page_title","snippet","first_seen"
            ])
            w.writeheader()
            for rec in sorted(results, key=lambda r: ({"email":0,"phone":1,"info":2}.get(r["type"],9), r["value"])):
                w.writerow(rec)
    except Exception as e:
        print(f"[ERROR] Could not write CSV: {e}", file=sys.stderr); return 2

    print(f"[OK] Found: {len(results)} items (emails+phones+info) | Pages fetched: {pages} | Output: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
