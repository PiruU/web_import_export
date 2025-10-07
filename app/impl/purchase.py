import pydantic

class Purchase(pydantic.BaseModel):
    purchase_id: str   = pydantic.Field(..., description="Purchase unique id", validation_alias=pydantic.AliasChoices("purchase_identifier"))
    customer_id: int   = pydantic.Field(..., description="Purchase related customer id")
    product_id : int   = pydantic.Field(..., description="Purchase related product id")
    quantity   : int   = pydantic.Field(..., description="")
    price      : float = pydantic.Field(..., description="")
    currency   : str   = pydantic.Field(..., description="")
    date       : str   = pydantic.Field(..., description="")