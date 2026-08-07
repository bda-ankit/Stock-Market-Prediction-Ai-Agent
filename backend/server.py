from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import cgi

from analyzer import analyze_uploaded_file


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
HOST = "127.0.0.1"
PORT = 8000


class StockAgentHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._serve_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._serve_file(FRONTEND_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._serve_file(FRONTEND_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        if self.path == "/api/health":
            self._json({"status": "ok", "message": "Stock Market Prediction backend is running."})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self._json({"error": "Use multipart/form-data with fields asset and file."}, HTTPStatus.BAD_REQUEST)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )

        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "filename", ""):
            self._json({"error": "Please attach a CSV or Excel file."}, HTTPStatus.BAD_REQUEST)
            return

        asset = form.getvalue("asset") or ""
        news_text = form.getvalue("newsText") or ""
        file_bytes = file_item.file.read()

        try:
            result = analyze_uploaded_file(file_bytes, file_item.filename, asset, news_text)
            self._json(result)
        except Exception as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), StockAgentHandler)
    print(f"Stock Market Prediction app running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()


# import tensorflow as tf

# print(tf.__version__)
# print(tf.test.is_built_with_cuda())
# print(tf.config.list_physical_devices('GPU'))