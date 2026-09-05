from fastapi import FastAPI
app =  FastAPI(title = "Flash Commerce API")
@app.get("/")
def read_root():
    return{"message": "Flash Commerce API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}