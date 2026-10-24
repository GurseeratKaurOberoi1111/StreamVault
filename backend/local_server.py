import argparse
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

os.environ['STREAMVAULT_LOCAL'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith('/media/'):
            return self.media(path)
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

    def dispatch(self, method):
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400)
            return
        if size < 0 or size > 16000:
            self.send_error(413)
            return
        event = {'version': '2.0', 'rawPath': urlsplit(self.path).path, 'requestContext': {'http': {'method': method}}, 'headers': {k.lower(): v for k, v in self.headers.items()}, 'cookies': [self.headers.get('Cookie', '')], 'body': self.rfile.read(size).decode('utf-8', errors='replace') if size else None}
        result = app.handler(event)
        data = result['body'].encode()
        self.send_response(result['statusCode'])
        for k, v in result['headers'].items():
            self.send_header(k, v)
        for value in result.get('cookies', []):
            self.send_header('Set-Cookie', value)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def media(self, path):
        if not app.session({'cookies': [self.headers.get('Cookie', '')]}):
            self.send_error(401)
            return
        title = path.removeprefix('/media/').removesuffix('.mp4')
        if title not in app.IDS or path != '/media/' + title + '.mp4':
            self.send_error(404)
            return
        file = app.ROOT / 'media' / (title + '.mp4')
        if not file.is_file():
            self.send_error(404)
            return
        size = file.stat().st_size
        start, end = 0, size - 1
        partial = self.headers.get('Range')
        if partial:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', partial)
            if not match or not any(match.groups()):
                self.send_error(416)
                return
            left, right = match.groups()
            if left:
                start = int(left)
                end = min(int(right), size-1) if right else size-1
            else:
                start = max(0, size-int(right))
            if start > end or start >= size:
                self.send_response(416)
                self.send_header('Content-Range', 'bytes */' + str(size))
                self.end_headers()
                return
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type', 'video/mp4')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('Content-Length', str(end-start+1))
        if partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with file.open('rb') as f:
                f.seek(start)
                remaining = end-start+1
                while remaining:
                    chunk = f.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'StreamVault: http://localhost:{args.port}', flush=True)
    print('Press Ctrl+C to stop. Local data is stored in data/streamvault.db.', flush=True)
    try:
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
