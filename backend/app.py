import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- Google Sheets Setup ----------------
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "nadiaportfolio-de04b6b47335.json")
SPREADSHEET_ID ="1UQct0Zr9Z3XkRfl4RS9Qi-E5jTc9CsyKeOw0SqzezCs"

print("JSON PATH:", SERVICE_ACCOUNT_FILE)
print("EXISTS:", os.path.exists(SERVICE_ACCOUNT_FILE))

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, SCOPE
)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # Use first tab
print("Using tab:", sheet.title)
print("✅ Server ready!")

# ---------------- HELPER ----------------
def get_value(data, key):
    val = data.get(key)
    if isinstance(val, list):
        return val[0].strip()
    elif isinstance(val, str):
        return val.strip()
    return ""

# ---------------- SERVER ----------------
class RequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_POST(self):
        if self.path != "/contacts":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())
            return

        # Read JSON safely
        content_length = int(self.headers.get("Content-Length", 0))
        raw_data = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(raw_data)
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        name = get_value(data, "name")
        email = get_value(data, "email")
        phone = get_value(data, "phone")
        message = get_value(data, "message")

        if not name or not email or not message:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Name, email, and message required"}).encode())
            return

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, email, phone, message, created_at])

        self._set_headers(201)
        
        self.wfile.write(json.dumps({"message": "Contact added","created_at":"created_at"}).encode())

# ---------------- RUN ----------------
def run(port=8080):
    print(f"Running server at http://localhost:{port}")
    server_address = ("", port)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    run()