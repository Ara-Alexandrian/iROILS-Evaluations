# login_manager.py

import time

class LoginManager:
    def __init__(self):
        # Admin credentials
        self.admin_credentials = {
            'admin_username': 'iroils',
            'admin_password': 'iROILS'
        }

        # Evaluator credentials mapped to their respective institutions
        self.evaluator_credentials = {
            'astam': {'password': 'A3nR6yP7', 'institution': 'MBPCC'},
            'kkirby': {'password': 'K4wT9bQ1', 'institution': 'MBPCC'},
            'dsolis': {'password': 'T2hP6vC4', 'institution': 'MBPCC'},
            'gpitcher': {'password': 'B3kN9wL5', 'institution': 'MBPCC'},
            'jashford': {'password': 'P6vT8mJ2', 'institution': 'MBPCC'},
            'hspears': {'password': 'R4xB2gW9', 'institution': 'MBPCC'},
            'aalexandrian': {'password': 'M7jH2xV5', 'institution': 'UAB'},
            'nviscariello': {'password': 'L8kY5nJ3', 'institution': 'UAB'},
            'rsullivan': {'password': 'C7bM5nW2', 'institution': 'UAB'},
            'jbelliveau': {'password': 'F3rP6yV8', 'institution': 'UAB'},
            'lrobinson': {'password': 'G5tV2cQ9', 'institution': 'UAB'},
        }

        # Session timeout threshold in seconds (e.g., 15 minutes)
        self.session_timeout = 15 * 60

    def login(self, session_state, username, password):
        if username == self.admin_credentials['admin_username'] and password == self.admin_credentials['admin_password']:
            session_state['user_role'] = 'admin'
            session_state['last_activity'] = time.time()
            return True
        else:
            return False

    def evaluator_login(self, session_state, username, password):
        evaluator_data = self.evaluator_credentials.get(username)
        if evaluator_data and evaluator_data['password'] == password:
            session_state['evaluator_logged_in'] = True
            session_state['evaluator_username'] = username
            session_state['user_role'] = 'evaluator'
            session_state['evaluator_institution'] = evaluator_data['institution']  # Assign institution
            session_state['last_activity'] = time.time()
            return True
        return False

    def logout(self, session_state):
        session_state.pop('user_role', None)
        session_state.pop('evaluator_logged_in', None)
        session_state.pop('evaluator_username', None)
        session_state.pop('evaluator_institution', None)
        session_state.pop('last_activity', None)

    def check_session_timeout(self, session_state):
        """Check if the user session has timed out."""
        if 'last_activity' in session_state:
            current_time = time.time()
            if current_time - session_state['last_activity'] > self.session_timeout:
                self.logout(session_state)
                return True
            else:
                session_state['last_activity'] = current_time  # Update last activity timestamp
        return False
