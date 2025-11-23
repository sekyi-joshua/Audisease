from fastapi import FastAPI
from routers import users, items

app = FastAPI()

# Register routers
app.include_router(users.router, prefix="/api/users")
# app.include_router(items.router, prefix="/api/items") - 


@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}

