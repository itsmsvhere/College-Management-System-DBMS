import os

# ─── Database Configuration ───────────────────────────────────────────────────
# Set these values via environment variables or edit directly for local dev.
# NEVER commit real credentials to version control.

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),          # set your password here (local only)
    "database": os.environ.get("DB_NAME",     "collegemanagementsystem"),
}
