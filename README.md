# Email/Phone Hunter (Windows + Linux)

A domain‑restricted **OSINT email & phone finder** for permissioned coursework and assessments.  
It crawls your **start URLs**, optionally follows external links, respects `robots.txt` by default (can be disabled with permission),
parses **HTML + PDFs**, and records **emails that match only the domains you allow**. It can also extract **phone numbers** to increase hit rate.

> ⚠️ Use only within a **clear scope** and with **written permission**. Follow site ToS, respect rate limits, and avoid evading logins/technical protections.

---
## Why information gathering matters in Ethical Hacking
Information Gathering (Recon/OSINT) is the **first, critical phase** of an ethical hacking engagement. With proper permission and scope, you map public-facing assets, discover **points of contact** (emails/phones), and learn where policies, press kits, or technical documents live. Good recon:
- narrows the testing surface (focus on what’s in-scope),
- avoids noisy or intrusive techniques,
- improves reporting with verifiable sources (links, docs, timestamps),
- and reduces risk by staying within public/approved data.

**This tool helps** by automating public discovery from your seed URLs, safely and transparently:
- records **only** emails ending with your allowed domains,
- optionally extracts **phone numbers** (higher hit-rate on contact pages),
- supports **HTML + PDFs**, external-follow (still domain-filtered results), UA rotation, and CSV output,
- lets you keep **robots.txt** on (default) or turn it off **only if permitted**.

---

## ✨ Features

- **Domain‑restricted emails**: collects only addresses that end with your `--domains` (subdomains allowed).
- **HTML + PDF parsing** (`--include-pdfs`, needs `pdfminer.six`).
- **Phone extraction** (`--include-phones`) for better coverage when emails aren’t listed.
- **Robots‑aware** by default; can disable via `--honor-robots false` (use only if permitted).
- **External follow** (`--external-follow`) to visit third‑party pages while still filtering emails to your allowed domains.
- **Real‑browser UA** + retries to reduce 403s.
- Depth/page/rate limits; **CSV output** with useful context columns.
- Works on **Windows + Linux** and friendly with **VS Code (“vibe coding”)** workflows.

---

## 🧰 Requirements

- Python **3.9+**
- Packages: `requests`, `beautifulsoup4`, (optional) `pdfminer.six`

---

## 🚀 Quickstart (company‑agnostic)

### 1) Install dependencies (virtualenv recommended)

**Windows PowerShell**
```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install requests beautifulsoup4 pdfminer.six
```

**Linux/macOS**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip requests beautifulsoup4 pdfminer.six
```

### 2) Run (examples using example.com)

**Conservative (robots respected)**
```bash
python3 email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/contact --output findings.csv --max-pages 40 --depth 1 --rate 2.0 --include-pdfs --include-phones --verbose
```

**Aggressive (robots off + external follow; only with permission)**
```bash
python3 email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/contact --output findings.csv --max-pages 60 --depth 2 --rate 2.5 --include-pdfs --include-phones --external-follow --honor-robots false --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36" --verbose
```

**Single page only (no link-follow)**
```bash
python3 email_hunter.py --domains example.com --start-urls https://www.example.com/contact --output findings.csv --max-pages 5 --depth 0 --rate 2.0 --include-phones --verbose
```

> Tip: You can pass **multiple** allowed domains if needed, e.g. `--domains example.com example.org`.

---
## One‑liner run commands (company‑agnostic, uses example.com) Another Option to Run the Script.

> Replace the domain and URLs with targets you are **authorized** to test.

### Windows (PowerShell) — one line
```powershell
.\venv\Scripts\python.exe .\email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/about https://www.example.com/contact https://www.example.com/press --output findings.csv --max-pages 60 --depth 1 --rate 2.5 --include-pdfs --include-phones --external-follow --honor-robots false --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36" --verbose
```

### macOS/Linux (Terminal) — one line
```bash
python3 email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/about https://www.example.com/contact https://www.example.com/press --output findings.csv --max-pages 60 --depth 1 --rate 2.5 --include-pdfs --include-phones --external-follow --honor-robots false --user-agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15" --verbose
```

### “Create venv + install + run” in one line (optional convenience)

**Windows PowerShell**
```powershell
py -m venv venv; .\venv\Scripts\python.exe -m pip install -U pip requests beautifulsoup4 pdfminer.six; .\venv\Scripts\python.exe .\email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/about https://www.example.com/contact https://www.example.com/press --output findings.csv --max-pages 60 --depth 1 --rate 2.5 --include-pdfs --include-phones --external-follow --honor-robots false --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36" --verbose
```

**macOS/Linux**
```bash
python3 -m venv venv && source venv/bin/activate && pip install -U pip requests beautifulsoup4 pdfminer.six && python3 email_hunter.py --domains example.com --start-urls https://www.example.com https://www.example.com/about https://www.example.com/contact https://www.example.com/press --output findings.csv --max-pages 60 --depth 1 --rate 2.5 --include-pdfs --include-phones --external-follow --honor-robots false --user-agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15" --verbose
```

> Tip: You can pass **multiple** allowed domains if needed, e.g. `--domains example.com example.org`.

---

## ⚙️ CLI Options

- `--domains` **(required)**: Allowed base domains; emails must end with these (subdomains allowed).
- `--start-urls` **(required)**: Seed URLs to fetch first.
- `--output` *(default: findings.csv)*: CSV output path.
- `--max-pages` *(default: 80)*: Max pages to fetch in total.
- `--depth` *(default: 1)*: Link‑follow depth (0 = only the start pages).
- `--rate` *(default: 1.0)*: Seconds between HTTP requests (be polite).
- `--include-pdfs`: Parse PDFs using `pdfminer.six`.
- `--include-phones`: Also extract phone numbers.
- `--honor-robots {true,false}` *(default: true)*: Respect or ignore `robots.txt`.
- `--external-follow`: Allow following links to other sites (emails still filtered to your domains).
- `--user-agent`: Custom UA string. If omitted, a real‑browser UA is chosen automatically.
- `--verbose`: Print progress and skip reasons.

---

## 📤 Output (CSV columns)

`type,value,domain,source_url,source_type,page_title,snippet,first_seen`

- `type`: `email` | `phone` | `info`
- `value`: the email or phone number
- `domain`: for emails (domain part), empty for phones
- `source_url`: page/PDF where found
- `source_type`: `html` or `pdf`
- `page_title`: HTML title or `(PDF)`
- `snippet`: nearby text context
- `first_seen`: UTC ISO timestamp

Example rows:
```csv
type,value,domain,source_url,source_type,page_title,snippet,first_seen
email,contact@example.com,example.com,https://www.example.com/contact,html,Contact,"...reach us at contact@example.com...",2025-01-01T12:00:00Z
phone,+8801XXXXXXXXX,,https://www.example.com/about,html,About,"...call us at +8801XXXXXXXXX...",2025-01-01T12:00:05Z
```

---

## 🔧 Troubleshooting

- **HTTP 403**: Site is blocking bots. Try a real browser UA (`--user-agent`), slower `--rate`, fewer pages, or different seeds. Some sites require JS/cookies—consider a browser mode.
- **0 pages crawled**: Missing/blocked seeds or robots disallowed. Provide reachable `--start-urls`.
- **No results**: Many sites don’t expose emails. Try `--include-pdfs`, `--include-phones`, add targeted seeds (press/investor pages).

---

## 🧑‍💻 “Vibe Coding” (VS Code workflow)

- Open the project folder in **VS Code** (“vibe coding” setup).
- Use the **Terminal** to create a venv and install dependencies.
- Create a **Run & Debug** configuration (or launch via Terminal) to pass CLI flags.
- Add a `.gitignore` with:
  ```
  venv/
  __pycache__/
  *.pyc
  *.log
  ```

---

## Ethics & Scope
- Run only with **written permission** and a defined scope.
- Keep your footprint small (`--rate`, `--max-pages`, `--depth`).
- Do **not** break logins, bypass technical protections, or violate any ToS.

---

## 📚 License

Educational use only. You are responsible for complying with laws and terms of service.
