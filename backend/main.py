from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user import router as user_router
from routes.chat import router as chat_router  # YENİ SATIR

app = FastAPI(
    title="Chat Bot API",
    description="API for the Chat Bot with Memory Support",  # Açıklama güncellendi
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "domId": "swagger-ui",
        "deepLinking": True,
        "displayOperationId": True,
    }
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])  # YENİ SATIR

# Ana sayfa
@app.get("/")
async def root():
    return {
        "message": "Chat Bot API is running!",
        "version": "0.1.0",
        "docs": "/docs"
    }