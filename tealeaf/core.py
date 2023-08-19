import os
import logging
import gzip
import functools
import tempfile
import ssl
import json
import http.client
import urllib.parse
import urllib.request
from tealeaf.headers import Headers

logger = logging.getLogger(__name__)

def urljoin(*parts: str) -> str:
    return "/".join([str(s).strip('/') for s in parts])

def format_cls(instance, **kws):
    return f'{instance.__class__.__name__}({", ".join(f"{key}={repr(value)}" for key, value in kws.items())})'

class ApiError(Exception):
    pass

class Request:

    def __init__(self,
            url: str='', 
            method: str='get',
            headers: dict=None,
            json: dict=None,
            data: bytes=None,
            ssl_context: ssl.SSLContext=None
        ):
        self.url = url
        self.method = method
        headers = headers or dict()
        self.headers = Headers(**headers)
        self.json = json
        self._data = data
        self.ssl_context = ssl_context

        self.headers['Accept'] = self.headers.get('Accept') or '*/*'
        self.headers['Accept-Encoding'] = self.headers.get('Accept-Encoding') or 'gzip, deflate, br'

    def __new__(cls, *args, **kws):
        _json = kws.get('json')
        _data = kws.get('data')
        if _json and _data:
            raise ValueError('Must specify at most one of ["json", "data"] arguments')
        elif _json:
            return super(Request, JsonRequest).__new__(JsonRequest)
        else:
            return super().__new__(cls)

    @property
    def data(self):
        return self._data

    def get_request_kws(self):
        '''
        See source: https://github.com/python/cpython/tree/main/Lib/urllib
        '''
        return dict(
            url=self.url,
            method=self.method,
            headers=self.headers,
            data=self.data
        )

    def create_request(self):
        return urllib.request.Request(**self.get_request_kws())

    def execute(self):
        
        # create a urllib.request.Request object
        request=self.create_request()

        # kws to pass to urllib.request.urlopen
        urlopen_kws = dict() if self.ssl_context is None else dict(ssl_context=self.ssl_context)

        # response data used to construct a response object
        response_kws = dict()

        try:
            with urllib.request.urlopen(request, **urlopen_kws) as response:
                response_kws['content'] = response.read()
                response_kws['response'] = response
        except urllib.error.HTTPError as e:
            response_kws['content'] = e.read()
            response_kws['response'] = e
        response_kws['request'] = request
        return Response(**response_kws)
    
class JsonRequest(Request):

    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.headers['Content-Type'] = 'application/json'

    def get_request_kws(self):
        if self.json is not None:
            return {**super().get_request_kws(), **dict(data=json.dumps(self.json).encode('utf-8'))}
        else:
            return super().get_request_kws()
        
    @property
    def data(self):
        return json.dumps(self.json).encode('utf-8')

class ApiCredential:
    
    def preprocess_request(self, request: Request) -> Request:
        headers = getattr(self, 'headers', {})
        request.headers.update(headers)
        return request
    
class HeaderSecrets(ApiCredential):

    def __init__(self, **headers):
        self.__headers = headers

    @property
    def headers(self): return self.__headers

class BearerToken(ApiCredential):
    
    def __init__(self, token: str):
        self.__token = token
    
    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.__token}"}

class JsonBodyCredentials(ApiCredential):

    def __init__(self, fields: dict, **kws):
        self.__fields = fields
    
    def preprocess_request(self, request: Request) -> JsonRequest:
        if request.json is None:
            return JsonRequest(**request.get_request_kws(), json=self.__fields)
        else:
            request.json.update(self.__fields)
            return request

class ClientSslCertificate(ApiCredential):

    def __init__(
            self, 
            certificate: bytes=b'', 
            key: bytes=b''
        ):
        self.__certificate = certificate
        self.__key = key
        self.__context = None

    def preprocess_request(self, request: Request) -> Request:
        request.ssl_context = self.get_context()
        return request

    def get_context(self):
        """
        Generates a `ssl.SSLContext` object that can be passed to `urllib.request.urlopen`
        """
        if self.__context is None:
            
            # create ssl context
            self.__context = ssl.SSLContext()

            # get temporary cert file
            cert = tempfile.NamedTemporaryFile(
                mode='wb', 
                delete=False
            )
            cert.write(self.__certificate)
            cert.close()

            # get temporary key file
            key = tempfile.NamedTemporaryFile(
                mode='wb', 
                delete=False
            )
            key.write(self.__key)
            key.close()

            # create ssl context
            self.__context.load_cert_chain(
                certfile=cert.name,
                keyfile=key.name
            )

            # remove files
            os.remove(key.name)
            os.remove(cert.name)
        
        return self.__context
    
class CredentialChain(ApiCredential):

    def __init__(self, *credentials: ApiCredential):
        self.__credentials = credentials

    def preprocess_request(self, request: Request) -> Request:
        for credential in self.__credentials:
            request = credential.preprocess_request(request)
        return request

class Response:

    def __init__(self, 
            content: bytes, 
            response: http.client.HTTPResponse,
            request: urllib.request.Request=None
        ):

        self.content = content
        self.response = response
        self.request = request

        self._data = None
        self.content_encoding = self.response.headers.get('Content-Encoding')
        if self.content_encoding == 'gzip':
            self.content = gzip.decompress(self.content)

    def __new__(cls, *args, **kws):
        code = getattr(kws.get('response'), 'code', -1)
        if code == -1:
            return super(Response, UnknownResponse).__new__(UnknownResponse)
        elif 200 <= code < 300:
            return super().__new__(cls)
        else:
            return super(Response, ErrorResponse).__new__(ErrorResponse)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return format_cls(self, code=self.code)

    def __getattr__(self, attr):
        if hasattr(self.response, attr):
            return getattr(self.response, attr)
        raise AttributeError(attr)

    @property
    def ok(self):
        return 200 <= self.code < 300

    def json(self, *args, **kws):
        return json.loads(self.content.decode(kws.get('encoding', 'utf-8')))
    
    def raise_(self):
        pass

    def astype(self, cls: type):
        return cls(**self.json())

class ErrorResponse(Response):

    def __str__(self):
        return format_cls(self, code=self.code, reason=self.reason, content=self.content)
    
    def raise_(self):
        raise ApiError(self.__str__())

class UnknownResponse(Response):
    pass

class Api:

    supported_methods = ['get', 'head', 'put', 'patch', 'post', 'delete', 'options']

    def __init__(self, 
            url: str, 
            credentials: ApiCredential=None,
            raise_for_status: bool = False
        ):
        self.url = url
        self.credentials = credentials or ApiCredential()
        self.raise_for_status = raise_for_status

    def __str__(self):
        return f'{self.__class__.__name__}("{self.url}")'
    
    def __repr__(self): return self.__str__()

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url: str):
        """
        Parse url and validate scheme on attribute set
        """
        self._url = url
        self._parsed_url = urllib.parse.urlparse(self._url)
        if not self._parsed_url.scheme:
            self.url = f'https://{self._url.strip("/")}'

    def request(self, 
        url: str='', 
        json: dict=None,
        method: str='get',
        headers: dict=None,
        data: bytes=None
    ):
        
        url=urljoin(self.url, url) if url else self.url
        logger.info(f'{method} {url}')
            
        request = Request(
            url=url,
            method=method,
            headers=headers,
            json=json,
            data=data
        )
        request = self.credentials.preprocess_request(request)
        response = request.execute()
        logger.info(f'{method} {url} responded with {response.code}')
        if self.raise_for_status:
            response.raise_()
        return response

    def __getattr__(self, attr: str):
        if attr in self.supported_methods:
            return functools.partial(self.request, method=attr.upper())
        raise AttributeError(attr)
