# login_manager.py

class LoginManager:
    def __init__(self):
        self.admin_credentials = {"admin": "admin_password"}  # Can be extended for multiple users

    def authenticate(self, username, password):
        return self.admin_credentials.get(username) == password

    def is_logged_in(self, session_state):
        return session_state.get("logged_in", False)

    def login(self, session_state, username, password):
        if self.authenticate(username, password):
            session_state["logged_in"] = True
            return True
        return False

    def logout(self, session_state):
        session_state["logged_in"] = False
