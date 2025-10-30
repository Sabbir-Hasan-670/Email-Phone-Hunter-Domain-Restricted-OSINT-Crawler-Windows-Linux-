# src/email_hunter/cli.py
# Thin CLI wrapper that reuses your existing main() function.
# Move your existing email_hunter.py code into src/email_hunter/app.py (keep def main()).

from .app import main

if __name__ == "__main__":
    raise SystemExit(main())
