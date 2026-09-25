import os

import requests
from flask import Flask, Response, request

app = Flask(__name__)

TARGET = "https://1001meloch.up.railway.app"

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

    headers = {}

    for key, value in request.headers.items():
        if key.lower() != "host" and key.lower() not in HOP_BY_HOP_HEADERS:
            headers[key] = value

    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
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

    for key, value in response.headers.items():
        if key.lower() not in HOP_BY_HOP_HEADERS:
            response_headers.append((key, value))

    return Response(
        response.content,
        status=response.status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
