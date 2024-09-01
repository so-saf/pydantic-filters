from fastapi import FastAPI

from .routers import address_router, user_router

app = FastAPI(title="Full chain Example")

app.include_router(address_router, prefix="/addresses", tags=["Addresses"])
app.include_router(user_router, prefix="/users", tags=["Users"])
