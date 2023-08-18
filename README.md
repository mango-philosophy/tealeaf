# Tealeaf

A simple interface for readable Python HTTP clients

- No dependencies 
- Simple and readable
- Lightweight

<br>

A simple example
```python
import tealeaf

# simple POST
api = tealeaf.Api('https://www.postman-echo.com')
api.post('/post', {"message": "hello tealeaf"}).json()

# Using bearer tokens
api = tealeaf.Api(
    'https://www.postman-echo.com',
    credentials=tealeaf.BearerToken('my-jwt')
)
api.post('/post', {"message": "hello authorized tealeaf"}).json()
```

<br>

An example with custom auth algorithm:
```python
# define a custom auth handler with a `preprocess_request` method
class CustomCredentialHandler(tealeaf.ApiCredential):

    def __init__(self, secret: str):
        super().__init__()
        self.__secret = secret

    def preprocess_request(self, request: tealeaf.Request):
        # your algorithm goes here and modifies the request object
        request.headers['secret-key'] = f'{request.data}{self.__secret}'
        return request

api = tealeaf.Api(
    'https://www.postman-echo.com',
    credentials=CustomCredentialHandler('my-super-secret')
)
api.post('/post', {"message": "hello custom tealeaf auth"}).json()
```