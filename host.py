#!/usr/bin/env python3
"""
Lightweight zero-dependency local static HTTP server.
Hosts the web dashboard on http://localhost:8000 and automatically opens it in your default browser.
"""

import http.server
import socketserver
import sys
import webbrowser

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler


class TCPServer(socketserver.TCPServer):
    """Custom TCP Server that allows immediate address reuse."""
    allow_reuse_address = True


def main():
    print(f"Starting local static web server on http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server.")

    try:
        with TCPServer(("", PORT), Handler) as httpd:
            # Automatically open the browser to our dashboard
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
