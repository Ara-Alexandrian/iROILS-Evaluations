"""
User submission page for the iROILS Evaluations application.

This module provides the interface for evaluators to submit
evaluations for entries.
"""

import logging
import random
from typing import Dict, List, Any, Optional

import streamlit as st

from app.pages import SecurePage
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.models.entry import Entry
from app.models.evaluation import Evaluation


class SubmissionPage(SecurePage):
    """
    User submission page component.
    
    This page provides functionality for evaluators to submit
    evaluations for entries.
    """
    
    def __init__(self, auth_service: AuthService, db_service: DatabaseService):
        """
        Initialize the submission page.
        
        Args:
            auth_service (AuthService): The authentication service
            db_service (DatabaseService): The database service
        """
        super().__init__("Evaluator Dashboard", auth_service, required_role='evaluator')
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the submission page content.
        """
        # Get evaluator information from session
        evaluator_username = self.session.get('username')
        institution = self.session.get('evaluator_institution')
        
        if not evaluator_username or not institution:
            st.error("Session data is incomplete. Please log out and log in again.")
            return
        
        # Display evaluator information
        st.markdown(f"### Welcome, {evaluator_username}")
        st.markdown(f"**Institution**: {institution}")
        
        # Get evaluator stats
        try:
            stats = self.db_service.get_evaluator_stats(evaluator_username, institution)
            st.markdown(f"**Evaluations completed**: {stats['total_evaluations']}")
            
            if stats['total_evaluations'] > 0:
                st.markdown(f"**Average Summary Score**: {stats['average_summary_score']:.2f}")
                st.markdown(f"**Average Tag Score**: {stats['average_tag_score']:.2f}")
        except Exception as e:
            st.error(f"Error retrieving evaluator statistics: {e}")
        
        # Divider
        st.markdown("---")
        
        # Get selected entries for the institution
        try:
            selected_entries = self.db_service.get_entries(institution, selected_only=True)
            
            if not selected_entries:
                st.warning("No entries have been selected for evaluation. Please contact an administrator.")
                return
            
            # Get current entry index from session or initialize
            current_index = self.session.get('current_entry_index', 0)
            if current_index >= len(selected_entries):
                current_index = 0
            
            # Display navigation controls
            self._render_navigation_controls(current_index, len(selected_entries))
            
            # Render current entry
            current_entry = selected_entries[current_index]
            self._render_entry(current_entry, evaluator_username)
            
        except Exception as e:
            st.error(f"Error loading entries: {e}")
    
    def _render_navigation_controls(self, current_index: int, total_entries: int) -> None:
        """
        Render navigation controls for entries.
        
        Args:
            current_index (int): The current entry index
            total_entries (int): The total number of entries
        """
        st.markdown(f"### Entry Navigation ({current_index + 1}/{total_entries})")
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("Previous"):
                new_index = (current_index - 1) % total_entries
                self.session.set('current_entry_index', new_index)
                st.rerun()
        
        with col2:
            if st.button("Next"):
                new_index = (current_index + 1) % total_entries
                self.session.set('current_entry_index', new_index)
                st.rerun()
        
        with col3:
            if st.button("Random"):
                new_index = random.randint(0, total_entries - 1)
                self.session.set('current_entry_index', new_index)
                st.rerun()
        
        with col4:
            entry_number = st.number_input(
                "Go to", 
                min_value=1, 
                max_value=total_entries, 
                value=current_index + 1,
                step=1
            )
            if entry_number != current_index + 1:
                self.session.set('current_entry_index', entry_number - 1)
                st.rerun()
    
    def _render_entry(self, entry: Entry, evaluator_username: str) -> None:
        """
        Render an entry for evaluation.
        
        Args:
            entry (Entry): The entry to render
            evaluator_username (str): The evaluator's username
        """
        st.markdown("### Entry Details")
        
        # Extract event number
        event_number = entry.event_number
        
        # Display entry metadata
        st.markdown(f"**Event Number**: {event_number}")
        
        # Display entry data
        for key, value in entry.data.items():
            if key not in ['Event Number', 'Selected'] and value is not None:
                st.markdown(f"**{key}**: {value}")
        
        # Divider
        st.markdown("---")
        
        # Get existing evaluation if any
        existing_evaluation = None
        try:
            existing_evaluation = self.db_service.get_evaluation(
                institution=entry.institution,
                evaluator=evaluator_username,
                entry_number=event_number
            )
        except Exception as e:
            st.error(f"Error retrieving existing evaluation: {e}")
        
        # Evaluation form
        st.markdown("### Submit Evaluation")
        
        with st.form(key=f"evaluation_form_{event_number}"):
            # Summary score (1-10)
            summary_score = st.slider(
                "Summary Score (1-10)", 
                min_value=1, 
                max_value=10, 
                value=existing_evaluation.summary_score if existing_evaluation else 5
            )
            
            # Tag score (1-10)
            tag_score = st.slider(
                "Tag Score (1-10)", 
                min_value=1, 
                max_value=10, 
                value=existing_evaluation.tag_score if existing_evaluation else 5
            )
            
            # Feedback
            feedback = st.text_area(
                "Feedback (optional)", 
                value=existing_evaluation.feedback if existing_evaluation else "",
                height=150
            )
            
            # Submit button
            submit_button = st.form_submit_button(
                "Submit Evaluation" if not existing_evaluation else "Update Evaluation"
            )
        
        # Process form submission
        if submit_button:
            try:
                # Create evaluation object
                evaluation = Evaluation(
                    institution=entry.institution,
                    evaluator=evaluator_username,
                    entry_number=event_number,
                    summary_score=summary_score,
                    tag_score=tag_score,
                    feedback=feedback
                )
                
                # Determine if this is a new evaluation
                is_new = existing_evaluation is None
                
                # Get old scores for updating institution stats
                old_summary = existing_evaluation.summary_score if existing_evaluation else 0
                old_tag = existing_evaluation.tag_score if existing_evaluation else 0
                
                # Save evaluation
                self.db_service.save_evaluation(evaluation)
                
                # Update institution stats
                self.db_service.add_evaluation_to_stats(
                    institution=entry.institution,
                    summary_score=summary_score,
                    tag_score=tag_score,
                    is_new=is_new,
                    old_summary=old_summary,
                    old_tag=old_tag
                )
                
                # Show success message
                st.success(
                    f"Evaluation {'submitted' if is_new else 'updated'} successfully!"
                )
                
                # Move to next entry
                current_index = self.session.get('current_entry_index', 0)
                total_entries = len(self.db_service.get_entries(entry.institution, selected_only=True))
                new_index = (current_index + 1) % total_entries
                self.session.set('current_entry_index', new_index)
                
                # Refresh page
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving evaluation: {e}")
                self.logger.error(f"Error saving evaluation for {event_number}: {e}")