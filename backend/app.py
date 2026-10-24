import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCAL = os.environ.get('STREAMVAULT_LOCAL') == '1'
ASSETS = {}
CATALOG = json.loads((ROOT / 'backend/catalog.json').read_text(encoding='utf-8')) if (ROOT / 'backend/catalog.json').exists() else []
IDS = {t['id'] for t in CATALOG}
_store = None

class Conflict(Exception):
    pass

class Store:
    def __init__(self):
        if LOCAL:
            self.path = os.environ.get('STREAMVAULT_DB', str(ROOT / 'data/streamvault.db'))
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path) as c:
                c.execute('CREATE TABLE IF NOT EXISTS records (pk TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        else:
            import boto3
            from botocore.config import Config
            self.table = boto3.resource('dynamodb').Table(os.environ['TABLE'])
            self.s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION'), config=Config(signature_version='s3v4'))

    def get(self, key):
        if LOCAL:
            with sqlite3.connect(self.path) as c:
                row = c.execute('SELECT payload FROM records WHERE pk=?', (key,)).fetchone()
            return json.loads(row[0]) if row else None
        return self.table.get_item(Key={'pk': key}, ConsistentRead=True).get('Item')

    def put(self, item, unique=False):
        if LOCAL:
            try:
                with sqlite3.connect(self.path) as c:
                    sql = 'INSERT INTO' if unique else 'INSERT OR REPLACE INTO'
                    c.execute(sql + ' records VALUES (?,?)', (item['pk'], json.dumps(item)))
            except sqlite3.IntegrityError:
                raise Conflict()
        else:
            from botocore.exceptions import ClientError
            try:
                args = {'Item': item}
                if unique:
                    args['ConditionExpression'] = 'attribute_not_exists(pk)'
                self.table.put_item(**args)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    raise Conflict()
                raise

    def delete(self, key):
        if LOCAL:
            with sqlite3.connect(self.path) as c:
                c.execute('DELETE FROM records WHERE pk=?', (key,))
        else:
            self.table.delete_item(Key={'pk': key})

    def video(self, title):
        if LOCAL:
            if not (ROOT / 'media' / (title + '.mp4')).is_file():
                return None
            return '/media/' + title + '.mp4'
        from botocore.exceptions import ClientError
        key = 'videos/' + title + '.mp4'
        try:
            self.s3.head_object(Bucket=os.environ['BUCKET'], Key=key)
        except ClientError as e:
            if e.response['Error']['Code'] in ('404', 'NoSuchKey', 'NotFound'):
                return None
            raise
        return self.s3.generate_presigned_url('get_object', Params={'Bucket': os.environ['BUCKET'], 'Key': key}, ExpiresIn=3600)

def store():
    global _store
    if _store is None:
        _store = Store()
    return _store

def response(code, data, content='application/json; charset=utf-8', cookies=None):
    headers = {'content-type': content, 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'referrer-policy': 'same-origin', 'x-frame-options': 'DENY'}
    result = {'statusCode': code, 'headers': headers, 'body': json.dumps(data) if content.startswith('application/json') else data}
    if cookies:
        result['cookies'] = cookies
    return result

def token_from(event):
    jar = SimpleCookie()
    try:
        jar.load('; '.join(event.get('cookies', [])) or event.get('headers', {}).get('cookie', ''))
        return jar['svsession'].value if 'svsession' in jar else None
    except Exception:
        return None

def session(event):
    token = token_from(event)
    if not token:
        return None
    item = store().get('session#' + hashlib.sha256(token.encode()).hexdigest())
    return item if item and int(item['expires']) > int(time.time()) else None

def cookie(token, age=604800):
    return 'svsession=' + token + '; HttpOnly; SameSite=Lax; Path=/; Max-Age=' + str(age) + ('' if LOCAL else '; Secure')

def asset(path):
    if path in ASSETS:
        item = ASSETS[path]
        return response(200, item[1], item[0])
    allowed = {'/': ('index.html', 'text/html; charset=utf-8'), '/styles.css': ('styles.css', 'text/css; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
    if path in allowed:
        name, mime = allowed[path]
        return response(200, (ROOT / 'frontend' / name).read_text(encoding='utf-8'), mime)
    if re.fullmatch(r'/assets/[a-z]+\.svg', path):
        p = ROOT / 'frontend' / path.lstrip('/')
        if p.is_file():
            return response(200, p.read_text(encoding='utf-8'), 'image/svg+xml')
    return None

def handler(event, context=None):
    try:
        return route(event)
    except Exception as e:
        print('StreamVault error:', type(e).__name__)
        return response(500, {'error': 'Server error. Please try again.'})

def route(event):
    path = event.get('rawPath', '/')
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    if method == 'GET' and not path.startswith('/api/'):
        result = asset(path)
        return result or response(404, {'error': 'Page not found'})
    if path == '/api/health' and method == 'GET':
        return response(200, {'status': 'ok', 'service': 'StreamVault', 'storage': 'SQLite' if LOCAL else 'DynamoDB'})
    body = {}
    if method == 'POST':
        if headers.get('content-type', '').split(';')[0].strip() != 'application/json':
            return response(415, {'error': 'Expected application/json'})
        origin = headers.get('origin')
        host = headers.get('host') or event.get('requestContext', {}).get('domainName', '')
        if origin and (urlsplit(origin).netloc != host or urlsplit(origin).scheme not in ('http', 'https')):
            return response(403, {'error': 'Cross origin request rejected'})
        raw = event.get('body') or '{}'
        if len(raw) > 16000:
            return response(413, {'error': 'Request too large'})
        try:
            if event.get('isBase64Encoded'):
                raw = base64.b64decode(raw, validate=True).decode()
            body = json.loads(raw)
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            return response(400, {'error': 'Invalid JSON object'})
    if path == '/api/catalog' and method == 'GET':
        return response(200, {'titles': CATALOG})
    if path == '/api/me' and method == 'GET':
        s = session(event)
        return response(200, {'user': s['user'] if s else None})
    if path in ('/api/register', '/api/login') and method == 'POST':
        user, password = body.get('username'), body.get('password')
        if not isinstance(user, str) or not isinstance(password, str):
            return response(400, {'error': 'Enter a username and password'})
        user = user.strip().lower()
        if not re.fullmatch(r'[a-z0-9_]{3,32}', user) or not 8 <= len(password) <= 128:
            return response(400, {'error': 'Use 3 to 32 letters, numbers or underscores; password must have 8 to 128 characters'})
        if path == '/api/register':
            salt = secrets.token_hex(16)
            digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
            try:
                store().put({'pk': 'user#' + user, 'salt': salt, 'digest': digest}, unique=True)
            except Conflict:
                return response(409, {'error': 'That username is already taken'})
            return response(201, {'ok': True})
        item = store().get('user#' + user)
        salt = item['salt'] if item else '0' * 32
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
        if not item or not hmac.compare_digest(digest, item['digest']):
            return response(401, {'error': 'Incorrect username or password'})
        token = secrets.token_urlsafe(32)
        store().put({'pk': 'session#' + hashlib.sha256(token.encode()).hexdigest(), 'user': user, 'expires': int(time.time()) + 604800})
        return response(200, {'user': user}, cookies=[cookie(token)])
    if path == '/api/logout' and method == 'POST':
        token = token_from(event)
        if token:
            store().delete('session#' + hashlib.sha256(token.encode()).hexdigest())
        return response(200, {'ok': True}, cookies=[cookie('', 0)])
    if path not in ('/api/library', '/api/progress') and not path.startswith('/api/play/'):
        return response(404, {'error': 'Not found'})
    s = session(event)
    if not s:
        return response(401, {'error': 'Sign in to continue'})
    user = s['user']
    if path == '/api/library' and method == 'GET':
        library, progress = {}, {}
        for title in IDS:
            item = store().get('state#' + user + '#' + title + '#saved')
            if item:
                library[title] = bool(item['value'])
            item = store().get('state#' + user + '#' + title + '#progress')
            if item:
                progress[title] = int(item['value'])
        return response(200, {'library': library, 'progress': progress})
    if path in ('/api/library', '/api/progress') and method == 'POST':
        title = body.get('id')
        if not isinstance(title, str) or title not in IDS:
            return response(400, {'error': 'Unknown title'})
        kind = 'saved' if path == '/api/library' else 'progress'
        value = body.get('saved') if kind == 'saved' else body.get('seconds')
        if kind == 'saved' and type(value) is not bool:
            return response(400, {'error': 'saved must be true or false'})
        if kind == 'progress':
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100000:
                return response(400, {'error': 'seconds must be between 0 and 100000'})
            value = int(value)
        store().put({'pk': 'state#' + user + '#' + title + '#' + kind, 'value': value})
        return response(200, {'ok': True})
    if path.startswith('/api/play/') and method == 'GET':
        title = path.removeprefix('/api/play/')
        if title not in IDS:
            return response(404, {'error': 'Unknown title'})
        url = store().video(title)
        if not url:
            return response(404, {'error': 'This film has not been uploaded yet. Add its MP4 using the deployment guide.'})
        return response(200, {'url': url, 'expiresIn': 3600})
    return response(405, {'error': 'Method not allowed'})
