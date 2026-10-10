# `secrets/` — local-only credentials

This folder is intentionally kept out of version control.

**Rule of thumb: anything you put in here must NEVER be committed.**

## What lives here

- `auth.json` — Playwright `storage_state` export for the job-board scraper (session cookies, local storage entries). Anyone with this file can impersonate your logged-in session.
- Any future per-user credential files (API tokens, private keys, etc.).

## Why it is gitignored

The contents of this folder are listed in the root `.gitignore` (`/secrets/*` with allow-rules for `.gitkeep` and `README.md`). This protects you from accidentally pushing a session cookie to a public repository.

## What to do if you suspect a leak

1. **Rotate your password immediately** on the affected service (e.g. Glints).
2. **Invalidate active sessions** in your account's security settings.
3. Delete the leaked file from your machine.
4. Re-run the login helper to regenerate a fresh `auth.json` locally.
5. Search your shell / editor history for accidental copies and clean them up.

## Best practices

- Do **not** symlink files from cloud-synced folders (OneDrive, Dropbox, iCloud, Google Drive) into this directory.
- Do **not** copy `auth.json` to another machine, a USB stick, or a chat message — even temporarily.
- Do **not** run the scraper against a real account from a CI runner or shared server. Use a dedicated test account instead.
- Review your repository history (`git log --all -- secrets/auth.json`) before publishing a fork.

When in doubt: assume anything in `secrets/` is as sensitive as a plaintext password and handle accordingly.
