import gradio as gr
import global_session
from user import User
from db_connector import MongoDBConnector
from user_info import create_profile_interface, get_user_info_display

# Initialize database connector
db = MongoDBConnector()


def signup(name_surname: str, email: str, password: str) -> str:
    """Handle user signup"""
    if not name_surname or not email or not password:
        return "Please provide both email and password"

    if db.add_user(name_surname, email, password):
        return "Signup successful! You can now login."
    else:
        return "Email already exists or an error occurred"


def login(email, password):
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
            )
        else:
            print("Login successful, but could not retrieve user data.")
            return "Could not retrieve user data.", *([None] * 15), gr.update()
    else:
        print("Login failed.")
        return "Invalid email or password.", *([None] * 15), gr.update()


# Create Gradio interface
with gr.Blocks() as app:
    gr.Markdown("# User Authentication System")
    
    with gr.Tabs() as tabs:
        with gr.Tab("Signup"):
            with gr.Column():
                signup_name_surname = gr.Textbox(label="Name Surname")
                signup_email = gr.Textbox(label="Email")
                signup_password = gr.Textbox(label="Password", type="password")
                signup_button = gr.Button("Sign Up")
                signup_output = gr.Textbox(label="Result")

                signup_button.click(
                    fn=signup,
                    inputs=[signup_name_surname, signup_email, signup_password],
                    outputs=signup_output,
                )

        with gr.Tab("Login"):
            with gr.Column():
                login_email = gr.Textbox(label="Email")
                login_password = gr.Textbox(label="Password", type="password")
                login_button = gr.Button("Login")
                login_output = gr.Textbox(label="Result")

        with gr.Tab("Profile"):
            profile_components = create_profile_interface()

        # Wire up the login button with all necessary outputs
        login_button.click(
            fn=login,
            inputs=[login_email, login_password],
            outputs=[login_output, *profile_components, tabs],
        )

if __name__ == "__main__":
    app.launch()
