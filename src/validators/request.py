from pydantic import BaseModel as BaseModelPydantic, ConfigDict, Field


class BaseModel(BaseModelPydantic):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        populate_by_name=True
    )


class CustomerPost(BaseModel):
    name: str
    display_name: str
    admins: list[str] = Field(default_factory=list)
