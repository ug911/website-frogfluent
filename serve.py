#!/usr/bin/env python3
"""Local dev server.

Two important things this does:
  1. Rewrites /payment_status/<id> → payment_status.html so that Stripe's
     redirect back to our origin lands on a real file.
  2. Optionally serves over HTTPS with a self-signed cert. Stripe forces the
     returnURL to https:// (and Chrome will cache localhost in HSTS once you
     hit a Stripe checkout once), so this is required for the payment-callback
     loop to work end-to-end.

Usage:
  python3 serve.py 8099            # http
  python3 serve.py 8099 --ssl      # https with auto-generated self-signed cert
"""
import os
import ssl
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CERT_DIR = Path(__file__).parent / ".certs"
CERT_FILE = CERT_DIR / "localhost.pem"
KEY_FILE = CERT_DIR / "localhost-key.pem"


def ensure_self_signed_cert():
    if CERT_FILE.exists() and KEY_FILE.exists():
        return
    CERT_DIR.mkdir(exist_ok=True)
    print("Generating a self-signed certificate for localhost…")
    subprocess.check_call(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(KEY_FILE), "-out", str(CERT_FILE),
            "-days", "365", "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ]
    )


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/payment_status/"):
            self.path = "/payment_status.html" + (
                "?" + self.path.split("?", 1)[1] if "?" in self.path else ""
            )
        return super().do_GET()


def main():
    args = [a for a in sys.argv[1:]]
    use_ssl = "--ssl" in args
    args = [a for a in args if a != "--ssl"]
    port = int(args[0]) if args else 8099

    httpd = ThreadingHTTPServer(("", port), Handler)
    scheme = "http"
    if use_ssl:
        ensure_self_signed_cert()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"

    print(f"Serving frogfluent on {scheme}://localhost:{port}/")
    if use_ssl:
        print("First visit will warn about the self-signed cert — click 'Advanced → Proceed'.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
