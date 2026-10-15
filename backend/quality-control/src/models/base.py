"""Shared base for models that mirror the frozen OpenAPI contract."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContractModel(BaseModel):
    """Contract-shaped model: camelCase JSON aliases, no unknown properties.

    The frozen contract fixes the request and response shapes for the QC and
    assembly operations, so unknown keys are rejected rather than ignored. That
    is what refuses a caller-supplied repair operator before it can be trusted.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )
