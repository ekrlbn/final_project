from pymongo import MongoClient
from dotenv import load_dotenv
import os
from user import User  # Import the User class

# Load environment variables
load_dotenv()


class MongoDBConnector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnector, cls).__new__(cls)
            # Initialize MongoDB connection using environment variables
            cls._instance.client = MongoClient(
                os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            )
            cls._instance.db = cls._instance.client[os.getenv("DB_NAME", "SENG472")]
            cls._instance.users = cls._instance.db[
                os.getenv("USER_COLLECTION_NAME", "user")
            ]
        return cls._instance

    def add_user(self, name_surname: str, email: str, password: str) -> bool:
        """Add a new user to the database"""
        try:
            # Check if user already exists
            if self.users.find_one({"email": email}):
                return False

            # Create a new user instance
            new_user = User(name_surname=name_surname, email=email, password=password)

            # Insert new user
            self.users.insert_one(new_user.to_dict())
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def verify_user(self, email: str, password: str) -> bool:
        """Verify user credentials"""
        try:
            user = self.users.find_one({"email": email, "password": password})
            return user is not None
        except Exception as e:
            print(f"Error verifying user: {e}")
            return False

    def get_user(self, email: str) -> dict | None:
        """Retrieve user details from the database by email."""
        try:
            user_data = self.users.find_one({"email": email})
            if user_data:
                # Convert ObjectId to string if necessary, or remove it if not needed by the User class
                if "_id" in user_data:
                    user_data["_id"] = str(user_data["_id"])
                return user_data
            return None
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
