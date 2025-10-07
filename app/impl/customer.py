import pydantic

class Customer(pydantic.BaseModel):
    customer_id: int = pydantic.Field(..., description="Customer unique id")
    title      : int | None = pydantic.Field(None, description="Optional customer title (if empty in csv)")
    lastname   : str | None = pydantic.Field(None, description="Optional customer last name (if empty in csv)")
    firstname  : str | None = pydantic.Field(None, description="Optional customer first name (if empty in csv)")
    postal_code: str | None = pydantic.Field(None, description="Optional customer zip code (if empty in csv)")
    city       : str | None = pydantic.Field(None, description="Optional customer city name (if empty in csv)")
    email      : str | None = pydantic.Field(None, description="Optional customer email (if empty in csv)")

    @pydantic.field_validator("title", mode="before")
    def _empty_str_to_none_for_ints(cls, v):
        return None if v == "" else v