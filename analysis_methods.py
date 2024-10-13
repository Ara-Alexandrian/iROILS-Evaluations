import json
import logging

# Set up logging for the analysis methods
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def evaluate_entry(entry):
    """Evaluate a single entry and return a score based on specific criteria."""
    try:
        # Example evaluation logic; implement your actual calculation here
        score = len(entry.get('Narrative', '')) / 100  # Example scoring logic
        logger.info(f"Evaluated entry {entry.get('Event Number')}, score: {score}")
        return score
    except Exception as e:
        logger.error(f"Failed to evaluate entry: {e}")
        return None

def calculate_statistics(entries):
    """Calculate and return statistics from a list of entries."""
    try:
        total_entries = len(entries)
        total_score = sum(evaluate_entry(entry) for entry in entries if evaluate_entry(entry) is not None)
        average_score = total_score / total_entries if total_entries > 0 else 0
        logger.info(f"Calculated statistics: average score {average_score}, total entries {total_entries}")
        return {'average_score': average_score, 'total_entries': total_entries}
    except Exception as e:
        logger.error(f"Failed to calculate statistics: {e}")
        return {'average_score': 0, 'total_entries': 0}

def evaluate_and_tag_entries(entries):
    """Evaluate entries and tag them based on conditions."""
    try:
        evaluated_entries = []
        for entry in entries:
            # Remove auto-scoring logic and replace with tagging logic based on certain conditions.
            tags = []  # Add your custom logic for tagging based on other conditions if necessary
            # For example, you can create tags based on specific text in the narrative.
            if "critical" in entry.get('Narrative', '').lower():
                tags.append('Critical Incident')
            if "safety" in entry.get('Narrative', '').lower():
                tags.append('Safety Concern')
            
            entry['Tags'] = tags  # Only update tags, not the score
            evaluated_entries.append(entry)
        logger.info(f"Evaluated and tagged {len(evaluated_entries)} entries without automatic scoring.")
        return evaluated_entries
    except Exception as e:
        logger.error(f"Failed to evaluate and tag entries: {e}")
        return entries

def save_evaluation(self, evaluator, entry_number, institution, summary_score, tag_score, feedback):
    try:
        institution_clean = institution.strip().lower()
        with self.connection.cursor() as cursor:
            # Use UPSERT to insert or update the evaluation
            cursor.execute("""
                INSERT INTO evaluations (institution, evaluator, entry_number, summary_score, tag_score, feedback)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (institution, evaluator, entry_number)
                DO UPDATE SET summary_score = EXCLUDED.summary_score,
                              tag_score = EXCLUDED.tag_score,
                              feedback = EXCLUDED.feedback;
            """, (institution_clean, evaluator, entry_number, summary_score, tag_score, feedback))
        self.logger.debug(f"Saved evaluation for evaluator {evaluator}, entry {entry_number}.")
    except Exception as e:
        self.logger.error(f"Error saving evaluation for evaluator {evaluator}, entry {entry_number}: {e}")
        raise e

def evaluate_entry(entry):
    """Evaluate a single entry and return a score based on specific criteria."""
    # Removed scoring logic here since it should only happen from user input
    logger.info(f"Evaluated entry {entry.get('Event Number')} but no score assigned (user evaluation needed).")
    return None  # Return None since we are no longer auto-scoring
