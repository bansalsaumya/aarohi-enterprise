import http.server
import socketserver
import os
import posixpath
import urllib.parse
import urllib.request
import sqlite3
import json
import mimetypes
import ssl

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(DIRECTORY), "backend", "database.sqlite")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(DIRECTORY, "backend", "database.sqlite")

REMOTE_BACKEND = "https://backend-one-blond-23.vercel.app"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("video/mp4", ".mp4")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, file_path):
        try:
            mime, _ = mimetypes.guess_type(file_path)
            file_size = os.path.getsize(file_path)
            self.send_response(200)
            self.send_header('Content-Type', mime or 'application/octet-stream')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except (ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                self.send_error(500, f"Error reading file: {e}")
            except Exception:
                pass

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/inquiries':
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_body)
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO inquiries (name, mobile, email, city, requirement, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (data.get('name', ''), data.get('phone', '') or data.get('mobile', ''), data.get('email', ''), data.get('city', ''), data.get('message', '') or data.get('requirement', '')))
                inquiry_id = cursor.lastrowid
                for pid in data.get('product_ids', []):
                    try:
                        cursor.execute("INSERT INTO inquiry_products (inquiry_id, product_id) VALUES (?, ?)", (inquiry_id, pid))
                    except Exception:
                        pass
                conn.commit()
                conn.close()
                return self.send_json({"success": True, "message": "Inquiry recorded successfully", "id": inquiry_id})
            except Exception as e:
                return self.send_json({"error": str(e)}, status=500)

        elif path == '/api/auth/login':
            return self.send_json({"token": "demo_admin_token", "user": {"email": "admin@aarohienterprise.com"}})

        self.send_error(404, f"Endpoint not found: {path}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # --- API Routes ---
        if clean_path == '/api/categories':
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM categories ORDER BY id ASC")
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                return self.send_json(rows)
            except Exception as e:
                return self.send_json({"error": str(e)}, status=500)

        elif clean_path == '/api/products':
            try:
                conn = get_db()
                cursor = conn.cursor()
                cat_filter = query_params.get('category', [None])[0]
                featured_filter = query_params.get('featured', [None])[0]
                search_filter = query_params.get('search', [None])[0]

                sql = """
                    SELECT p.*, c.name AS category_name, c.slug AS category_slug 
                    FROM products p 
                    LEFT JOIN categories c ON p.category_id = c.id 
                    WHERE 1=1
                """
                args = []
                if cat_filter:
                    sql += " AND (c.slug = ? OR c.id = ?)"
                    args.extend([cat_filter, cat_filter])
                if featured_filter == 'true' or featured_filter == '1':
                    sql += " AND p.is_featured = 1"
                if search_filter:
                    sql += " AND (p.name LIKE ? OR p.description LIKE ?)"
                    args.extend([f"%{search_filter}%", f"%{search_filter}%"])

                sql += " ORDER BY p.id DESC"
                cursor.execute(sql, args)
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                return self.send_json(rows)
            except Exception as e:
                return self.send_json({"error": str(e)}, status=500)

        elif clean_path.startswith('/api/products/'):
            slug_or_id = clean_path.replace('/api/products/', '').strip()
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, c.name AS category_name, c.slug AS category_slug 
                    FROM products p 
                    LEFT JOIN categories c ON p.category_id = c.id 
                    WHERE p.slug = ? OR p.id = ?
                """, (slug_or_id, slug_or_id))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return self.send_json(dict(row))
                else:
                    return self.send_json({"error": "Product not found"}, status=404)
            except Exception as e:
                return self.send_json({"error": str(e)}, status=500)

        # --- Static File Serving ---
        if clean_path.startswith('/uploads/'):
            file_name = clean_path.replace('/uploads/', '')
            candidate_paths = [
                os.path.join(DIRECTORY, "uploads", file_name),
                os.path.join(DIRECTORY, "backend", "uploads", file_name),
                os.path.join(os.path.dirname(DIRECTORY), "backend", "uploads", file_name)
            ]
            for cp in candidate_paths:
                if os.path.isfile(cp):
                    return self.serve_file(cp)
            
            # If not found locally, fetch from remote backend and cache it locally
            try:
                remote_url = f"{REMOTE_BACKEND}/uploads/{urllib.parse.quote(file_name)}"
                req = urllib.request.Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=3) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        cache_path = os.path.join(DIRECTORY, "uploads", file_name)
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        with open(cache_path, "wb") as f:
                            f.write(content)
                        return self.serve_file(cache_path)
            except Exception:
                pass

        # Remove leading slashes for local filesystem path
        relative_path = clean_path.lstrip('/\\').replace('/', os.sep)
        full_path = os.path.join(DIRECTORY, relative_path)
        
        # If requested path matches a static file on disk, serve it directly
        if relative_path and os.path.isfile(full_path):
            return self.serve_file(full_path)
            
        # If it has a file extension (e.g. .jpg, .js, .css, .png, .webp) but not found
        _, ext = os.path.splitext(clean_path)
        if ext and ext not in ['.html']:
            self.send_error(404, f"File not found: {clean_path}")
            return

        # Fallback to index.html for Single Page Application routing (e.g., /, /products, /about, /contact)
        index_file = os.path.join(DIRECTORY, "index.html")
        return self.serve_file(index_file)

if __name__ == '__main__':
    try:
        httpd = ThreadedHTTPServer(("", PORT), SPAHandler)
        print(f"Serving Aarohi Enterprise SPA & API at http://localhost:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Server start error: {e}")
