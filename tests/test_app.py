import base64
import copy
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ['STREAMVAULT_LOCAL'] = '1'
sys.path.insert(0, str(ROOT / 'backend'))
import app

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ['STREAMVAULT_DB'] = str(Path(self.temp.name) / 'test.db')
        app._store = None
        self.cookie = None

    def tearDown(self):
        self.temp.cleanup()

    def call(self, path, method='GET', body=None, cookie=None, headers=None, raw=None):
        event = {'rawPath':path,'requestContext':{'http':{'method':method}},'headers':{'content-type':'application/json','host':'localhost:8000',**(headers or {})},'cookies':[cookie or self.cookie] if cookie or self.cookie else [],'body':raw if raw is not None else json.dumps(body or {})}
        result = app.handler(event)
        data = json.loads(result['body']) if result['headers']['content-type'].startswith('application/json') else result['body']
        return result, data

    def register(self, user='alice', password='valid_password'):
        return self.call('/api/register','POST',{'username':user,'password':password})

    def login(self, user='alice', password='valid_password'):
        result, data = self.call('/api/login','POST',{'username':user,'password':password})
        if result['statusCode']==200:
            self.cookie=result['cookies'][0].split(';')[0]
        return result, data

    def account(self):
        self.register();self.login()

    def test_catalog_public(self):
        r,d=self.call('/api/catalog');self.assertEqual(r['statusCode'],200);self.assertEqual(len(d['titles']),6)

    def test_assets(self):
        for path in ['/','/styles.css','/app.js','/assets/sintel.svg']:
            self.assertEqual(self.call(path)[0]['statusCode'],200)

    def test_assets_with_windows_default_encoding(self):
        from unittest.mock import patch
        original = Path.read_text
        def windows_read(path, encoding=None, errors=None):
            return original(path, encoding=encoding or 'cp1252', errors=errors)
        with patch.object(Path, 'read_text', windows_read):
            html = self.call('/')[1]
            js = self.call('/app.js')[1]
        self.assertIn('▶', html)
        self.assertIn('↗', html)
        self.assertIn('✓', js)
        self.assertNotIn('â', html)

    def test_traversal_blocked(self):
        self.assertEqual(self.call('/assets/../app.py')[0]['statusCode'],404)

    def test_duplicate_account(self):
        self.assertEqual(self.register()[0]['statusCode'],201)
        self.assertEqual(self.register()[0]['statusCode'],409)

    def test_password_hash(self):
        self.register();item=app.store().get('user#alice')
        self.assertNotIn('valid_password',json.dumps(item));self.assertIn('salt',item)

    def test_bad_credentials(self):
        self.register();self.assertEqual(self.login(password='wrong_password')[0]['statusCode'],401)
        self.assertEqual(self.login(user='nobody')[0]['statusCode'],401)

    def test_login_session_v2_cookies(self):
        self.account();self.assertEqual(self.call('/api/me')[1]['user'],'alice')

    def test_header_cookie_fallback(self):
        self.account();saved=self.cookie;self.cookie=None
        self.assertEqual(self.call('/api/me',headers={'cookie':saved})[1]['user'],'alice')

    def test_expired_session(self):
        self.account();token=self.cookie.split('=',1)[1]
        key='session#'+app.hashlib.sha256(token.encode()).hexdigest()
        item=app.store().get(key);item['expires']=int(time.time())-1;app.store().put(item)
        self.assertIsNone(self.call('/api/me')[1]['user'])

    def test_logout_revokes_cookie(self):
        self.account();saved=self.cookie;self.call('/api/logout','POST')
        self.assertEqual(self.call('/api/library',cookie=saved)[0]['statusCode'],401)

    def test_protected_endpoints(self):
        for path in ['/api/library','/api/play/sintel']:
            self.assertEqual(self.call(path)[0]['statusCode'],401)

    def test_first_save_and_remove(self):
        self.account()
        for value in [True,False]:
            self.assertEqual(self.call('/api/library','POST',{'id':'sintel','saved':value})[0]['statusCode'],200)
            self.assertEqual(self.call('/api/library')[1]['library']['sintel'],value)

    def test_first_progress_save(self):
        self.account();self.call('/api/progress','POST',{'id':'sintel','seconds':48})
        self.assertEqual(self.call('/api/library')[1]['progress']['sintel'],48)

    def test_finished_progress(self):
        self.account();self.call('/api/progress','POST',{'id':'sintel','seconds':0})
        self.assertEqual(self.call('/api/library')[1]['progress']['sintel'],0)

    def test_state_survives_new_store(self):
        self.account();self.call('/api/library','POST',{'id':'sintel','saved':True});app._store=None
        self.assertTrue(self.call('/api/library')[1]['library']['sintel'])

    def test_account_isolation(self):
        self.account();self.call('/api/library','POST',{'id':'sintel','saved':True})
        self.register('bob');self.login('bob');self.assertEqual(self.call('/api/library')[1]['library'],{})

    def test_independent_title_state(self):
        self.account()
        for title in ['sintel','spring']:
            self.call('/api/library','POST',{'id':title,'saved':True})
        self.assertEqual(len(self.call('/api/library')[1]['library']),2)

    def test_bad_progress(self):
        self.account()
        for value in [-1,100001,'10',True,None,float('nan')]:
            self.assertEqual(self.call('/api/progress','POST',{'id':'sintel','seconds':value})[0]['statusCode'],400)

    def test_bad_save(self):
        self.account();self.assertEqual(self.call('/api/library','POST',{'id':'sintel','saved':'false'})[0]['statusCode'],400)

    def test_unknown_title(self):
        self.account();self.assertEqual(self.call('/api/play/unknown')[0]['statusCode'],404)
        self.assertEqual(self.call('/api/progress','POST',{'id':[],'seconds':10})[0]['statusCode'],400)

    def test_invalid_json(self):
        self.assertEqual(self.call('/api/login','POST',raw='{')[0]['statusCode'],400)
        self.assertEqual(self.call('/api/login','POST',raw='[]')[0]['statusCode'],400)

    def test_origin_rejection(self):
        self.assertEqual(self.call('/api/login','POST',headers={'origin':'https://evil.example'})[0]['statusCode'],403)

    def test_content_type_rejection(self):
        self.assertEqual(self.call('/api/login','POST',headers={'content-type':'text/plain'})[0]['statusCode'],415)

    def test_username_validation(self):
        for user in ['ab','a'*33,'<script>','a b','Älice']:
            self.assertEqual(self.register(user)[0]['statusCode'],400)

    def test_aws_cookie_secure(self):
        local=app.LOCAL
        try:
            app.LOCAL=False;self.assertIn('; Secure',app.cookie('test'))
        finally:app.LOCAL=local

    def test_base64_body(self):
        raw=base64.b64encode(json.dumps({'username':'alice','password':'valid_password'}).encode()).decode()
        event={'rawPath':'/api/register','requestContext':{'http':{'method':'POST'}},'headers':{'content-type':'application/json'},'body':raw,'isBase64Encoded':True}
        self.assertEqual(app.handler(event)['statusCode'],201)

if __name__=='__main__':unittest.main()
