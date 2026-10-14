"""Shared base for models that mirror the frozen OpenAPI contract."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ContractModel(BaseModel):
    """Contract-shaped model: camelCase JSON aliases, no unknown properties.

    The frozen contract declares ``unevaluatedProperties: false`` on the
    financial rule schemas, so unknown keys are rejected rather than ignored.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )
