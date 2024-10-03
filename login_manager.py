class LoginManager:
    def __init__(self):
        # Admin credentials
        self.admin_credentials = {
            'admin_username': 'admin',
            'admin_password': 'admin_password'
        }

        # Evaluator credentials mapped to their respective institutions
        self.evaluator_credentials = {
            'astam': {'password': 'F8bV4nC1', 'institution': 'MBPCC'},
            'kkirby': {'password': '9xZ7fHk3', 'institution': 'MBPCC'},
            'dsolis': {'password': 'T2hP6vC4', 'institution': 'MBPCC'},
            'gpitcher': {'password': 'B3kN9wL5', 'institution': 'MBPCC'},
            'jashford': {'password': 'P6vT8mJ2', 'institution': 'MBPCC'},
            'hspears': {'password': 'R4xB2gW9', 'institution': 'MBPCC'},
            'aalexandrian': {'password': 'S9hL3dT7', 'institution': 'UAB'},
            'nviscariello': {'password': 'Y8pK4vH1', 'institution': 'UAB'},
            'rsullivan': {'password': 'C7bM5nW2', 'institution': 'UAB'},
            'jbelliveau': {'password': 'F3rP6yV8', 'institution': 'UAB'},
            'lrobinson': {'password': 'G5tV2cQ9', 'institution': 'UAB'},
        }

    def login(self, session_state, username, password):
        if username == self.admin_credentials['admin_username'] and password == self.admin_credentials['admin_password']:
            session_state['user_role'] = 'admin'
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
            return True
        return False

    def logout(self, session_state):
        session_state.pop('user_role', None)
        session_state.pop('evaluator_logged_in', None)
        session_state.pop('evaluator_username', None)
        session_state.pop('evaluator_institution', None)
