from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load .env file for local development.
load_dotenv()

# --- Check which environment we are in ---
IS_IN_CLOUD_RUN = os.getenv("K_SERVICE")

# Load common variables
username = os.getenv("USER")
password = os.getenv("PASSWORD")
database = os.getenv("DATABASE")

if IS_IN_CLOUD_RUN:
    # --- Cloud Run Configuration (Unix Socket) ---
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_socket_path = f"/cloudsql/{instance_connection_name}"

    # MySQL + PyMySQL connection string for Unix socket
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{username}:{password}@/{database}?unix_socket={db_socket_path}"
    )
else:
    # --- Local Configuration (IP Hostname) ---
    hostname = os.getenv("HOSTNAME")
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{username}:{password}@{hostname}/{database}"
    )

# print(f"Connecting to: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()