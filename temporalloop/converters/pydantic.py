#!/usr/bin/env python3

import json
from typing import Any

from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DataConverter,
    DefaultPayloadConverter,
    JSONPlainPayloadConverter,
)


class PydanticJSONPayloadConverter(JSONPlainPayloadConverter):
    """Pydantic JSON payload converter.

    This extends the :py:class:`JSONPlainPayloadConverter` to override
    :py:meth:`to_payload` using the Pydantic encoder.
    """

    def to_payload(self, value: Any) -> Payload | None:
        """Convert all values with Pydantic encoder or fail.

        Like the base class, we fail if we cannot convert. This payload
        converter is expected to be the last in the chain, so it can fail if
        unable to convert.
        """
        # We let JSON conversion errors be thrown to caller
        if hasattr(value, "model_dump_json"):
            return Payload(
                metadata={"encoding": self.encoding.encode()},
                data=value.model_dump_json().encode(),
            )

        return Payload(
            metadata={"encoding": self.encoding.encode()},
            data=json.dumps(value).encode(),
        )


# pyre-ignore[13]:
class PydanticPayloadConverter(CompositePayloadConverter):
    """Payload converter that replaces Temporal JSON conversion with Pydantic
    JSON conversion.
    """

    def __init__(self) -> None:
        super().__init__(
            *(
                (c if not isinstance(c, JSONPlainPayloadConverter) else PydanticJSONPayloadConverter())
                for c in DefaultPayloadConverter.default_encoding_payload_converters
            )
        )


pydantic_data_converter = DataConverter(payload_converter_class=PydanticPayloadConverter)
"""Data converter using Pydantic JSON conversion."""
