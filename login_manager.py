# login_manager.py

class LoginManager:
    def __init__(self):
        # Admin credentials
        self.admin_credentials = {
            'admin_username': 'admin',
            'admin_password': 'admin_password'
        }
        # Evaluator credentials
        self.evaluator_credentials = {
            'evaluator1': 'password1',
            'evaluator2': 'password2',
            # Add more evaluators as needed
        }


    def login(self, session_state, username, password):
        if username == self.admin_credentials['admin_username'] and password == self.admin_credentials['admin_password']:
            session_state['user_role'] = 'admin'
            return True
        else:
            return False


    def evaluator_login(self, session_state, username, password):
        if username in self.evaluator_credentials:
            if self.evaluator_credentials[username] == password:
                session_state['evaluator_logged_in'] = True
                session_state['evaluator_username'] = username
                session_state['user_role'] = 'evaluator'
                return True
            else:
                return False
        else:
            return False


    def logout(self, session_state):
        session_state.pop('user_role', None)
