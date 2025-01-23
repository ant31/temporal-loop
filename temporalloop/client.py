from temporalio.client import Client

from temporalloop.converters.pydantic import pydantic_data_converter

TEMPORAL_CLIENT: Client | None = None


async def tclient(host: str, namespace: str) -> Client:
    return await GTClient(host, namespace).client()


class TClient:
    def __init__(self, host: str, namespace: str) -> None:
        self.host = host
        self.namespace = namespace
        self._client = None

    def set_client(self, client: Client) -> None:
        self._client = client

    async def client(self) -> Client:
        if self._client is None:
            self._client = await Client.connect(
                self.host,
                namespace=self.namespace,
                lazy=True,
                data_converter=pydantic_data_converter,
            )
        return self._client


class GTClient(TClient):
    def __new__(cls, host: str, namespace: str):
        if not hasattr(cls, "instance") or cls.instance is None:
            cls.instance = TClient(host, namespace)
        return cls.instance

    def reinit(self) -> None:
        self.instance = None
