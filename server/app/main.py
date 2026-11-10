import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import auth, files, notes
from . import products, stores, wishlist
from .errors import ApiError, json_response
from .seed import seed_if_empty

seed_if_empty()

app = FastAPI(title="PAM Backend Template", docs_url=None, redoc_url=None)


@app.get("/health")
async def health():
    return json_response({"status": "ok"})


app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(files.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(wishlist.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Origin", "Content-Type", "Authorization"],
)

@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return exc.to_response()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = {401: "UNAUTHORIZED", 404: "NOT_FOUND", 409: "EMAIL_TAKEN"}.get(
        exc.status_code, "VALIDATION_ERROR"
    )
    message = "Route not found" if exc.status_code == 404 else str(exc.detail)
    return json_response(
        {"error": {"code": code, "message": message}}, status=exc.status_code
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return json_response(
        {"error": {"code": "VALIDATION_ERROR", "message": "Invalid request"}},
        status=400,
    )

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    print("Backend listening on http://localhost:%d" % port)
    uvicorn.run(app, host="0.0.0.0", port=port)
