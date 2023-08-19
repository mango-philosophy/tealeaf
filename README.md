# Tealeaf

[![license](https://img.shields.io/github/license/jackmuskopf/softy.svg)](https://github.com/jackmuskopf/softy/blob/main/LICENSE)

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



Integrates easily with `pydantic` for data validation
```python
import tealeaf
from pydantic import BaseModel

class Message(BaseModel):
    message: str

class EchoResponse(BaseModel):
    data: Message
    url: str

# simple POST
api = tealeaf.Api('https://www.postman-echo.com')
echo = api \
    .post('/post', {"message": "hello tealeaf"}) \
    .astype(EchoResponse)

print(repr(echo))
```

```
>>> EchoResponse(data=Message(message='hello tealeaf'), url='https://www.postman-echo.com/post')
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