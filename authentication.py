import gradio as gr
import global_session
from user import User
from db_connector import MongoDBConnector
from user_info import create_profile_interface, get_user_info_display

db = MongoDBConnector()

def signup(name_surname: str, email: str, password: str) -> str:
    """Handle user signup"""
    if not name_surname or not email or not password:
        return "Please provide both email and password"

    if db.add_user(name_surname, email, password):
        return "Signup successful! You can now login."
    else:
        return "Email already exists or an error occurred"


def login(email, password) -> tuple:
    if db.verify_user(email, password):
        user_data = db.get_user(email)
        if user_data and "_id" in user_data:
            del user_data["_id"]  # Remove MongoDB ID before creating User object

        if user_data:
            global_session.current_user = User(**user_data)
            print(f"User {global_session.current_user.name_surname} logged in.")
            return (
                "Login successful! Redirecting to profile...",
                *get_user_info_display(),
                gr.update(selected=2),
                True
            )
        else:
            print("Login successful, but could not retrieve user data.")
            return "Could not retrieve user data.", *([None] * 15), gr.update(), True
    else:
        print("Login failed.")
        return "Invalid email or password.", *([None] * 15), gr.update(), False