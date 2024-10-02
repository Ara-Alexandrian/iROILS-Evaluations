# helper.py

def load_institution_data(redis_manager, institution):
    selected_entries = redis_manager.get_selected_entries(institution)
    evaluation_scores = redis_manager.get_evaluation_scores(institution)
    return selected_entries, evaluation_scores

def save_institution_data(redis_manager, institution, selected_entries, evaluation_scores):
    redis_manager.save_selected_entries(institution, selected_entries)
    redis_manager.save_evaluation_scores(institution, evaluation_scores)
