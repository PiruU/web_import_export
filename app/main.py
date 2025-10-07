import fastapi, fastapi.responses

from impl.import_csv import CsvImportRequest, import_csv_impl
from impl.export_customers import CustomerExportRequest, export_customers_impl
from impl.receive_export import receive_export_impl

app = fastapi.FastAPI(title="CSV import API")

@app.post("/api/import_csv", summary="Import purchases and customers")
def import_csv(payload: CsvImportRequest):
    return import_csv_impl(payload)

@app.post("/api/export_customers", summary="Send customer purchases to distant url")
async def export_customers(payload: CustomerExportRequest):
    return await export_customers_impl(payload)

@app.post("/api/receive_export", response_class=fastapi.responses.HTMLResponse, summary="Display received JSON")
async def receive_export(request: fastapi.Request):
    return await receive_export_impl(request)