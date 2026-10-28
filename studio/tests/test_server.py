import unittest
from unittest.mock import patch
import server

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.client=server.app.test_client()
        server._login_attempts.clear()
    def test_demo_query(self):
        response=self.client.post('/api/query',json={'sql':'SELECT name FROM employees WHERE salary > 120000 ORDER BY salary DESC'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['rows'],[['Ethan Kim'],['Olivia Chen']])
    def test_writes_and_multiple_statements_rejected(self):
        for sql in ['DELETE FROM employees','SELECT 1; SELECT 2',"SELECT * INTO OUTFILE '/tmp/data' FROM employees"]:
            self.assertEqual(self.client.post('/api/query',json={'sql':sql}).status_code,400)
    def test_bad_query_reports_error(self):
        self.assertEqual(self.client.post('/api/query',json={'sql':'SELECT missing FROM employees'}).status_code,400)
    def test_auth(self):
        with patch.object(server,'TOKEN','test-secret'):
            self.assertEqual(self.client.get('/api/schema').status_code,401)
            self.assertEqual(self.client.get('/api/schema',headers={'Authorization':'Bearer test-secret'}).status_code,200)
    def test_session_login_and_logout(self):
        with patch.object(server,'TOKEN','test-secret'):
            self.assertFalse(self.client.get('/api/access').json['authenticated'])
            self.assertEqual(self.client.post('/api/login',json={'token':'wrong'}).status_code,401)
            self.assertEqual(self.client.get('/api/schema').status_code,401)
            response=self.client.post('/api/login',json={'token':'test-secret'})
            self.assertEqual(response.status_code,200)
            self.assertIn('HttpOnly',response.headers['Set-Cookie'])
            self.assertIn('SameSite=Strict',response.headers['Set-Cookie'])
            self.assertEqual(self.client.get('/api/schema').status_code,200)
            self.assertTrue(self.client.get('/api/access').json['authenticated'])
            self.assertEqual(self.client.post('/api/logout',json={}).status_code,200)
            self.assertEqual(self.client.get('/api/schema').status_code,401)
    def test_cross_origin_login_rejected(self):
        self.assertEqual(self.client.post('/api/login',json={'token':''},headers={'Origin':'https://elsewhere.example'}).status_code,403)
    def test_render_https_origin(self):
        with patch.dict(server.os.environ,{'RENDER':'true'}):
            self.assertEqual(self.client.post('/api/login',json={'token':''},headers={'Origin':'https://localhost'}).status_code,200)
    def test_login_throttled(self):
        with patch.object(server,'TOKEN','secret'):
            for _ in range(10):
                self.assertEqual(self.client.post('/api/login',json={'token':'wrong'}).status_code,401)
            self.assertEqual(self.client.post('/api/login',json={'token':'wrong'}).status_code,429)
    def test_public_guide_when_locked(self):
        with patch.object(server,'TOKEN','secret'):
            for path in ['/docs','/static/setup.sql']:
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code,200)
            self.assertEqual(self.client.get('/api/schema').status_code,401)
    def test_demo_does_not_fake_native_features(self):
        for endpoint in ['vector','temporal']:
            self.assertEqual(self.client.post('/api/'+endpoint,json={}).status_code,400)
    def test_temporal_parameterization(self):
        with patch.object(server,'MODE','live'),patch.object(server,'execute',return_value={'rows':[]}) as query:
            r=self.client.post('/api/temporal',json={'table':'employees','as_of':'2026-10-28T12:00'})
            self.assertEqual(r.status_code,200)
            self.assertEqual(query.call_args.args,('SELECT * FROM `employees` FOR SYSTEM_TIME AS OF TIMESTAMP ? LIMIT 500',('2026-10-28 12:00:00',)))
    def test_native_vector_parameters(self):
        with patch.object(server,'MODE','live'),patch.object(server,'execute',return_value={'rows':[]}) as query:
            r=self.client.post('/api/vector',json={'table':'documents','vector':[1,0,0],'top_k':3})
            self.assertEqual(r.status_code,200)
            self.assertIn('VEC_DISTANCE_COSINE',query.call_args.args[0])
            self.assertEqual(query.call_args.args[1],('[1, 0, 0]',3))
    def test_identifier_injection_rejected(self):
        with patch.object(server,'MODE','live'):
            r=self.client.post('/api/vector',json={'table':'documents; DROP TABLE users','vector':[1,0]})
            self.assertEqual(r.status_code,400)
    def test_schema_and_security_headers(self):
        r=self.client.get('/api/schema')
        self.assertEqual(len(r.json['tables']),2)
        self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])

if __name__=='__main__':
    unittest.main()
