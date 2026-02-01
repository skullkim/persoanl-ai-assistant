from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.env_setting import settings

origins = []

if settings.APP_ENV == "dev":
    if settings.CORS_ORIGIN: # Add other CORS_ORIGIN if it's set in dev
        origins.append(settings.CORS_ORIGIN)
elif settings.APP_ENV == "prod":
    if settings.CORS_ORIGIN: # Only add CORS_ORIGIN if it's set in prod
        origins.append(settings.CORS_ORIGIN)

def add_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )