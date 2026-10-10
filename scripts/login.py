"""Login helper using real Google Chrome to bypass Google/Cloudflare bot detection.

How it works:
1. Spawns your installed real Google Chrome with a dedicated session & debugging port.
2. You log in to Glints normally with Google (no 'browser not secure' error).
3. Playwright connects to the real Chrome session and saves cookies to secrets/auth.json.
"""
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

SECRETS_DIR = Path("secrets")
AUTH_PATH = SECRETS_DIR / "auth.json"
DEV_DIR = Path(".chrome_login_session")


def find_browser() -> Path:
    for p in CHROME_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError("Google Chrome or Microsoft Edge not found.")


def main() -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    DEV_DIR.mkdir(parents=True, exist_ok=True)

    browser_exe = find_browser()
    print(f"[*] Menggunakan browser asli: {browser_exe.name}")

    cmd = [
        str(browser_exe),
        "--remote-debugging-port=9222",
        f"--user-data-dir={DEV_DIR.resolve()}",
        "https://glints.com/id/login",
    ]

    print("[*] Membuka Google Chrome asli...")
    proc = subprocess.Popen(cmd)

    # Wait for Chrome to open port
    time.sleep(2)

    print("\n" + "=" * 65)
    print("Browser Chrome asli sudah terbuka.")
    print("Silakan login dengan akun Google atau email kamu.")
    print("Setelah berhasil masuk ke Glints, kembali ke terminal ini dan")
    print("tekan [ENTER] untuk menyimpan session.")
    print("=" * 65 + "\n")

    input("Tekan [ENTER] setelah selesai login di Chrome...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            if not browser.contexts:
                print("[-] Tidak ada konteks browser yang ditemukan.")
                return
            context = browser.contexts[0]
            context.storage_state(path=str(AUTH_PATH))
            print(f"\n[+] BERHASIL! Session berhasil disimpan ke: {AUTH_PATH}")
    except Exception as e:
        print(f"[-] Gagal mengekspor session: {e}")
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
