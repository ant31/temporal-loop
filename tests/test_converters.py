import json

import pytest
from pydantic import BaseModel

from temporalloop.converters.pydantic import (
    PydanticJSONPayloadConverter,
    pydantic_data_converter,
)


class MyPydanticModel(BaseModel):
    a: str
    b: int


def test_pydantic_json_payload_converter_to_payload_pydantic():
    """Test converting a Pydantic model to a payload."""
    converter = PydanticJSONPayloadConverter()
    model = MyPydanticModel(a="test", b=123)
    payload = converter.to_payload(model)
    assert payload is not None
    assert payload.metadata["encoding"] == b"json/plain"
    assert payload.data == model.model_dump_json().encode()


def test_pydantic_json_payload_converter_to_payload_dict():
    """Test converting a dictionary to a payload."""
    converter = PydanticJSONPayloadConverter()
    data = {"a": "test", "b": 123}
    payload = converter.to_payload(data)
    assert payload is not None
    assert payload.metadata["encoding"] == b"json/plain"
    assert payload.data == json.dumps(data).encode()


@pytest.mark.asyncio
async def test_pydantic_data_converter_pydantic_model():
    """Test the full data converter with a Pydantic model."""
    model = MyPydanticModel(a="foo", b=42)
    payloads = await pydantic_data_converter.encode([model])
    assert len(payloads) == 1
    result = await pydantic_data_converter.decode(payloads, [MyPydanticModel])
    assert result == [model]


@pytest.mark.asyncio
async def test_pydantic_data_converter_dict():
    """Test the full data converter with a dictionary."""
    data = {"a": "bar", "b": 99}
    payloads = await pydantic_data_converter.encode([data])
    assert len(payloads) == 1
    result = await pydantic_data_converter.decode(payloads, [dict])
    assert result == [data]
