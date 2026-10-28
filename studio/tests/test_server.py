import unittest
from unittest.mock import patch
import server

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.client=server.app.test_client()
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
