import os

import requests
from flask import Flask, Response, request

app = Flask(__name__)

TARGET = "https://1001meloch.up.railway.app"

# Заголовки, которые нельзя бездумно пересылать между двумя HTTP-соединениями.
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}


@app.route(
    "/",
    defaults={"path": ""},
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
@app.route(
    "/<path:path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
def proxy(path):
    target_url = f"{TARGET}/{path}"

    request_headers = {}

    for key, value in request.headers.items():
        key_lower = key.lower()

        if key_lower == "host":
            continue

        if key_lower in HOP_BY_HOP_HEADERS:
            continue

        request_headers[key] = value

    # ВАЖНО:
    # Просим Railway вернуть несжатый ответ.
    # Тогда requests не распаковывает gzip/br,
    # и Safari получает обычные байты.
    request_headers["Accept-Encoding"] = "identity"

    try:
        upstream = requests.request(
            method=request.method,
            url=target_url,
            headers=request_headers,
            params=request.args,
            data=request.get_data(),
            allow_redirects=False,
            timeout=60,
        )
    except requests.RequestException as exc:
        return Response(
            f"Proxy error: {exc}",
            status=502,
            mimetype="text/plain",
        )

    response_headers = []

    for key, value in upstream.headers.items():
        key_lower = key.lower()

        if key_lower in HOP_BY_HOP_HEADERS:
            continue

        response_headers.append((key, value))

    # Запрещаем промежуточному CDN изменять тело ответа.
    response_headers.append(
        ("Cache-Control", "no-store, no-transform")
    )

    return Response(
        upstream.content,
        status=upstream.status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
