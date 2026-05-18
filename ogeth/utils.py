import requests
import urllib3
import ssl
import socket


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """Transport adapter for UN Data Portal SSL quirk.

    The UN Data Portal server doesn't support "RFC 5746 secure
    renegotiation". This causes an error when the client is using
    OpenSSL 3, which enforces that standard by default. The fix is to
    create a custom SSL context that allows for legacy connections.
    See `get_legacy_session()`, which should be used instead of
    `requests()` directly.
    """

    # "Transport adapter" that allows us to use custom ssl_context.
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # OP_LEGACY_SERVER_CONNECT. In Python 3.12+ this can be replaced
    # with ssl.OP_LEGACY_SERVER_CONNECT.
    ctx.options |= 0x4
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


# Function to check if connected to internet
def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False
