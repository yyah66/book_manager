import os

# openGauss connection defaults; override via environment variables if needed
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "book_manager")
DB_USER = os.getenv("DB_USER", "gaussdb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "OpenGauss@123")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")