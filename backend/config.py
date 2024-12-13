import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    # Retrieve DATABASE_URL and SECRET_KEY directly from environment variables
    # and raise an error if they are not provided in the .env file.
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required but not set.")

    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required but not set.")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable SQLAlchemy event notifications
