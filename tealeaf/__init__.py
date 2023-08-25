from tealeaf.core import (
    Api,
    Request,
    Response,
    ApiCredential,
    ApiError,
    HeaderSecrets,
    BearerToken,
    JsonBodyCredentials,
    ClientSslCertificate,
    CredentialChain
)

def get(url, *args, **kws) -> Response:
    return Api(url).get(*args, **kws)

def put(url, *args, **kws) -> Response:
    return Api(url).put(*args, **kws)

def post(url, *args, **kws) -> Response:
    return Api(url).post(*args, **kws)

def patch(url, *args, **kws) -> Response:
    return Api(url).patch(*args, **kws)

def delete(url, *args, **kws) -> Response:
    return Api(url).delete(*args, **kws)
