"""Run against an already running local server: python tests/http_smoke.py."""
import http.cookiejar
import json
import secrets
import urllib.error
import urllib.request

base='http://127.0.0.1:8000'
jar=http.cookiejar.CookieJar()
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(path,body=None,headers=None):
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
    return client.open(req,timeout=10)

assert request('/').status==200
assert request('/styles.css').status==200
assert request('/assets/sintel.svg').status==200
user='test_'+secrets.token_hex(4)
data={'username':user,'password':secrets.token_urlsafe(16)}
assert request('/api/register',data).status==201
assert request('/api/login',data).status==200
assert json.load(request('/api/me'))['user']==user
assert request('/api/library',{'id':'sintel','saved':True}).status==200
assert request('/api/progress',{'id':'sintel','seconds':11}).status==200
library=json.load(request('/api/library'))
assert library['library']['sintel'] and library['progress']['sintel']==11
assert json.load(request('/api/play/sintel'))['url']=='/media/sintel.mp4'
with request('/media/sintel.mp4',headers={'Range':'bytes=0-99'}) as r:
    assert r.status==206 and len(r.read())==100
    assert r.headers['Content-Range'].startswith('bytes 0-99/')
with request('/media/sintel.mp4',headers={'Range':'bytes=-64'}) as r:
    assert r.status==206 and len(r.read())==64
assert request('/api/logout',{}).status==200
assert json.load(request('/api/me'))['user'] is None
try:
    request('/media/sintel.mp4')
    raise AssertionError('Anonymous media access succeeded')
except urllib.error.HTTPError as e:
    assert e.code==401
print('HTTP smoke passed: static assets, account, persistence, playback URL, byte ranges, logout and media authorization.')
