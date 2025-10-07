import pydantic, typing, sqlite3, pathlib, fastapi, httpx

class CustomerExportRequest(pydantic.BaseModel):
    target_url: pydantic.AnyHttpUrl = pydantic.Field(..., description="URL de l'API distante à appeler en POST")
    timeout   : float               = pydantic.Field(15.0, ge=1.0, le=120.0, description="Timeout HTTP en secondes")

def _open_db(db_path: pathlib.Path=pathlib.Path("/app/db/db.sqlite3")) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite file not found: { db_path }")
    connexion = sqlite3.connect(db_path)
    connexion.row_factory = sqlite3.Row
    connexion.execute("PRAGMA foreign_keys = ON;")
    return connexion

def _load_customers() -> typing.List[typing.Dict[typing.Any, typing.Any]]:
    sql = """
    SELECT
        customer.id         AS customer_id,
        customer.title      AS title,
        customer.lastname   AS lastname,
        customer.firstname  AS firstname,
        customer.zipcode    AS postal_code,
        customer.city       AS city,
        customer.email      AS email,
        purchase.id         AS purchase_id,
        purchase.product_id AS product_id,
        purchase.quantity   AS quantity,
        purchase.price      AS price,
        purchase.currency   AS currency,
        purchase.date       AS date
    FROM customers customer
    LEFT JOIN purchases purchase ON purchase.customer_id = customer.id
    ORDER BY customer.id, purchase.date, purchase.id
    """
    with _open_db() as connexion:
        cursor = connexion.cursor()
        cursor.execute(sql)

        customers: typing.List[typing.Dict[typing.Any, typing.Any]] = []
        current_id, current = None, None

        for row in cursor:
            customer_id = row["customer_id"]
            if customer_id != current_id:
                current = {
                    "customer_id": customer_id,
                    "title"      : row["title"],
                    "lastname"   : row["lastname"],
                    "firstname"  : row["firstname"],
                    "postal_code": row["postal_code"],
                    "city"       : row["city"],
                    "email"      : row["email"],
                    "purchases"  : []
                }
                customers.append(current)
                current_id = customer_id
            
            if row["purchase_id"] is not None:
                current["purchases"].append({
                    "purchase_id": row["purchase_id"],
                    "product_id" : row["product_id"],
                    "quantity"   : row["quantity"],
                    "price"      : row["price"],
                    "currency"   : row["currency"],
                    "date"       : row["date"],
                })

        return customers

async def export_customers_impl(payload: CustomerExportRequest):
    try:
        body = { "customers": _load_customers() }
    except FileNotFoundError as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    except sqlite3.DatabaseError as e:
        raise fastapi.HTTPException(status_code=500, detail=f"SQLite error: {e}")

    headers = {"Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=payload.timeout) as client:
            resp = await client.post(str(payload.target_url), json=body, headers=headers)
    except httpx.ConnectError as e:
        raise fastapi.HTTPException(status_code=502, detail=f"Connection error to target: {e}")
    except httpx.HTTPError as e:
        raise fastapi.HTTPException(status_code=502, detail=f"HTTP error to target: {e}")

    if resp.status_code // 100 != 2:
        raise fastapi.HTTPException(
            status_code=502,
            detail=f"Upstream {resp.status_code}: {resp.text[:500]}"
        )

    return {
        "status"       : 0,
        "customers"    : len(body["customers"]),
        "purchases"    : sum(len(c["purchases"]) for c in body["customers"]),
        "target_status": resp.status_code
    }