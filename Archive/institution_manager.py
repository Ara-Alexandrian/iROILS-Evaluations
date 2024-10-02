class InstitutionManager:
    def __init__(self, redis_manager):
        self.redis_manager = redis_manager

    def get_selected_entries(self, institution):
        return self.redis_manager.get_selected_entries(institution)

    def get_evaluation_scores(self, institution):
        return self.redis_manager.get_evaluation_scores(institution)

    def get_institution_data(self, institution):
        # Combine selected entries and evaluation scores into one method
        selected_entries = self.get_selected_entries(institution)
        evaluation_scores = self.get_evaluation_scores(institution)
        return selected_entries, evaluation_scores

    def reset_institution_data(self, institution):
        self.redis_manager.reset_data(institution)

    def save_institution_data(self, institution, selected_entries, evaluation_scores):
        self.redis_manager.save_selected_entries(institution, selected_entries)
        self.redis_manager.save_evaluation_scores(institution, evaluation_scores)
