import os

# Clear existing environment variables
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']
if 'SECRET_KEY' in os.environ:
    del os.environ['SECRET_KEY']

from dotenv import load_dotenv

# Load environment variables from the .env file
#load_dotenv()
load_dotenv(override=True)

class Config:
    # Retrieve DATABASE_URL and SECRET_KEY directly from environment variables
    # and raise an error if they are not provided in the .env file.
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required but not set.")

    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required but not set.")
    
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', SECRET_KEY)  # Use SECRET_KEY as fallback
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable SQLAlchemy event notifications