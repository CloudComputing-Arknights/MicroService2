from __future__ import annotations
import os
from fastapi import FastAPI

from resources import item_resource

where_am_i = os.environ.get("WHERE_AM_I", None)

port = int(os.environ.get("FASTAPIPORT", 8000))
app = FastAPI(
    title="Item API",
    description="Item microservice",
    version="0.1.0",
)
app.include_router(item_resource.router)

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    global where_am_i
    if where_am_i is None:
        where_am_i = "NOT IN DOCKER"
    return {"message": f"Welcome to the Item API from {where_am_i}. See /docs for OpenAPI UI."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
