import unittest
import tealeaf

class TestRequest(unittest.TestCase):

    def test_json_requests(self):
        secrets = dict(mysecret='test3323')
        body = dict(color='orange')

        credentials = tealeaf.JsonBodyCredentials(fields=secrets)
        api = tealeaf.Api('https://www.postman-echo.com', credentials=credentials)
        response = api.get('/get', json=body).json()

        expected_args = {**secrets, **body}
        self.assertEqual(response['args'], expected_args)
        self.assertEqual(response['headers']['content-type'], 'application/json')

        credentials = tealeaf.HeaderSecrets(**secrets)
        api = tealeaf.Api('https://www.postman-echo.com', credentials=credentials)
        response = api.get('/get', json=body).json()
        print(response)

        self.assertEqual(response['args'], body)
        self.assertEqual(response['headers']['content-type'], 'application/json')
        self.assertEqual(response['headers']['mysecret'], secrets['mysecret'])