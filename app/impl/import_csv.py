import fastapi, pydantic, pathlib, typing, csv, functools, inspect, sqlite3

from .customer import Customer
from .purchase import Purchase

from .customer_db import create_customer_scheme, upsert_customers
from .purchase_db import create_purchase_scheme, upsert_purchases

class CsvImportRequest(pydantic.BaseModel):
    customers: str = pydantic.Field(..., description="customers.csv path")
    purchases: str = pydantic.Field(..., description="purchases.csv path")

def _ensure_path_exists(func: typing.Callable[[str], typing.List[Customer | Purchase]]):
    sig = inspect.signature(func)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = pathlib.Path(sig.bind_partial(*args, **kwargs).arguments["path_str"])
        if not path.exists():
            raise FileNotFoundError(f"File not found: {p}")
        return func(*args, **kwargs)
    return wrapper

@_ensure_path_exists
def _read_customers(path_str: str) -> typing.List[Customer]:
    path = pathlib.Path(path_str)
    customers: typing.List[Customer] = []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file, delimiter=";"):
            customers.append(Customer(**row))
    return customers

@_ensure_path_exists
def _read_purchases(path_str: str) -> typing.List[Purchase]:
    path = pathlib.Path(path_str)
    purchases: typing.List[Purchase] = []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file, delimiter=";"):
            purchases.append(Purchase(**row))
    return purchases

def _read_csvs(payload: CsvImportRequest) -> typing.Tuple[typing.List[Customer], typing.List[Purchase]]:
    customers = _read_customers(payload.customers)
    purchases = _read_purchases(payload.purchases)
    return customers, purchases

def _open_db(db_path: pathlib.Path=pathlib.Path("/app/db/db.sqlite3")) -> sqlite3.Connection:
    connexion = sqlite3.connect(db_path)
    connexion.execute("PRAGMA foreign_keys = ON;")
    connexion.execute("PRAGMA journal_mode = WAL;")
    connexion.execute("PRAGMA synchronous = NORMAL;")
    return connexion

def _try_to_upsert_db(payload: CsvImportRequest) -> typing.Tuple[int, int]:
        customers, purchases = _read_csvs(payload)
        with _open_db() as connexion:
            create_customer_scheme(connexion)
            n_customers = upsert_customers(connexion, customers)
            create_purchase_scheme(connexion)
            n_purchases = upsert_purchases(connexion, purchases)
        return n_customers, n_purchases

def import_csv_impl(payload: CsvImportRequest):
    try:
        n_customers, n_purchases = _try_to_upsert_db(payload)
    except FileNotFoundError as e:
        raise fastapi.HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise fastapi.HTTPException(status_code=400, detail=f"Error while reading CSV files: {e}")
    return {"status": 0, "n_customers": n_customers, "n_purchases": n_purchases}