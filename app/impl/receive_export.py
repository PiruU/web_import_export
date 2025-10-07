import fastapi, json, html

async def receive_export_impl(request: fastapi.Request):
    raw = await request.body()
    try:
        data = json.loads(raw)
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        body = html.escape(pretty)
    except Exception:
        body = html.escape(raw.decode("utf-8", "replace"))
    return f"""<!doctype html>
    <html>
        <head>
        <meta charset="utf-8">
        <title>Payload reçu</title>
            <style>
                body {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; margin: 24px; }}
                pre  {{ white-space: pre-wrap; word-break: break-word; }}
                .wrap {{ max-width: 1000px; }}
            </style>
        </head>
        <body>
            <div class="wrap">
                <h1>Payload reçu</h1>
                <pre>{body}</pre>
            </div>
        </body>
    </html>
    """