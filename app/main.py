from fastapi import FastAPI
from app.routes import auth_routes, instructor_routes, student_routes, analytics_routes

app = FastAPI(title="Code Judge API", version="1.0")

# Register routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(instructor_routes.router, prefix="/instructor", tags=["Instructor"])
app.include_router(student_routes.router, prefix="/student", tags=["Student"])
app.include_router(analytics_routes.router, prefix="/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "Welcome to Code Judge API 🚀"}
