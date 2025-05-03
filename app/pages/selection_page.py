"""
Selection page for the iROILS Evaluations application.

This module provides an interface for administrators to select
entries for evaluation.
"""

import logging
import random
from typing import Dict, List, Any, Optional

import streamlit as st
import pandas as pd

from app.pages import BasePage
from app.services.database_service import DatabaseService
from app.models.entry import Entry


class SelectionPage(BasePage):
    """
    Selection page component.
    
    This page provides functionality for administrators to select
    entries for evaluation.
    """
    
    def __init__(self, db_service: DatabaseService, institution: str):
        """
        Initialize the selection page.
        
        Args:
            db_service (DatabaseService): The database service
            institution (str): The institution to manage entries for
        """
        super().__init__("Selection Mode")
        self.db_service = db_service
        self.institution = institution
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the selection page content.
        """
        st.markdown(f"### Entry Selection for {self.institution}")
        
        # Load entries if not already loaded
        all_entries = self.session.get('all_entries')
        if not all_entries:
            try:
                all_entries = self.db_service.get_entries(self.institution)
                
                if not all_entries:
                    st.warning(f"No entries found for {self.institution}. Please upload data first.")
                    return
                
                self.session.set('all_entries', all_entries)
                self.session.set('total_entries', len(all_entries))
                
            except Exception as e:
                st.error(f"Error loading entries: {e}")
                self.logger.error(f"Error loading entries: {e}")
                return
        
        # Display selection controls
        self._render_selection_controls()
        
        # Display entries table
        self._render_entries_table(all_entries)
    
    def _render_selection_controls(self) -> None:
        """
        Render selection control buttons.
        """
        st.markdown("### Selection Controls")
        
        # Selection options
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Select All"):
                self._update_selection_status("Selected", None)
        
        with col2:
            if st.button("Deselect All"):
                self._update_selection_status("Do Not Select", None)
        
        with col3:
            random_count = st.number_input(
                "Random Count", 
                min_value=1, 
                max_value=self.session.get('total_entries', 100),
                value=10
            )
        
        with col4:
            if st.button("Select Random"):
                self._select_random_entries(random_count)
        
        # Selection statistics
        selected_count = self._count_selected_entries()
        total_count = self.session.get('total_entries', 0)
        
        st.markdown(
            f"**Selection Status**: {selected_count} of {total_count} entries selected "
            f"({(selected_count / total_count * 100) if total_count > 0 else 0:.1f}%)"
        )
    
    def _render_entries_table(self, entries: List[Entry]) -> None:
        """
        Render a table of entries with selection controls.
        
        Args:
            entries (List[Entry]): The entries to display
        """
        st.markdown("### Entries")
        
        # Convert entries to dataframe for display
        entries_data = []
        
        for entry in entries:
            # Extract key fields for display
            entry_data = {
                'Event Number': entry.event_number,
                'Selected': entry.selected
            }
            
            # Add other fields from entry data
            for key, value in entry.data.items():
                if key not in ['Event Number', 'Selected'] and value is not None:
                    entry_data[key] = value
            
            entries_data.append(entry_data)
        
        if not entries_data:
            st.warning("No entries to display.")
            return
        
        # Create dataframe
        df = pd.DataFrame(entries_data)
        
        # Add selection column with checkboxes
        selection_col = []
        for i, row in df.iterrows():
            selection_col.append(row['Selected'] == 'Selected')
        
        # Display dataframe with selection column
        edited_df = st.data_editor(
            df,
            column_config={
                "Selected": st.column_config.CheckboxColumn(
                    "Select",
                    default=False,
                    help="Select this entry for evaluation"
                )
            },
            disabled=["Event Number"],
            hide_index=True,
            use_container_width=True
        )
        
        # Check for changes in selection
        for i, row in edited_df.iterrows():
            event_number = row['Event Number']
            is_selected = row['Selected']
            
            # Find entry by event number
            entry = next((e for e in entries if e.event_number == event_number), None)
            
            if entry and ((is_selected and entry.selected != 'Selected') or 
                         (not is_selected and entry.selected == 'Selected')):
                # Update entry selection status
                new_status = 'Selected' if is_selected else 'Do Not Select'
                self._update_entry_selection(entry, new_status)
    
    def _update_selection_status(self, status: str, event_numbers: Optional[List[str]]) -> None:
        """
        Update selection status for entries.
        
        Args:
            status (str): The new selection status
            event_numbers (Optional[List[str]]): Event numbers to update, or None for all
        """
        try:
            entries = self.session.get('all_entries', [])
            updated_entries = []
            
            for entry in entries:
                if event_numbers is None or entry.event_number in event_numbers:
                    # Update entry selection status
                    entry.update_selection_status(status)
                    updated_entries.append(entry)
            
            # Save updated entries to database
            if updated_entries:
                self.db_service.save_entries(updated_entries)
                st.success(f"Updated selection status for {len(updated_entries)} entries.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error updating selection status: {e}")
            self.logger.error(f"Error updating selection status: {e}")
    
    def _update_entry_selection(self, entry: Entry, status: str) -> None:
        """
        Update selection status for a single entry.
        
        Args:
            entry (Entry): The entry to update
            status (str): The new selection status
        """
        try:
            # Update entry selection status
            entry.update_selection_status(status)
            
            # Save updated entry to database
            self.db_service.save_entry(entry)
            
        except Exception as e:
            st.error(f"Error updating entry selection: {e}")
            self.logger.error(f"Error updating entry selection: {e}")
    
    def _select_random_entries(self, count: int) -> None:
        """
        Select a random number of entries.
        
        Args:
            count (int): The number of entries to select
        """
        try:
            # Reset all entries to "Do Not Select"
            self._update_selection_status("Do Not Select", None)
            
            # Get all entries
            entries = self.session.get('all_entries', [])
            
            if not entries:
                st.warning("No entries to select from.")
                return
            
            # Ensure count is not greater than total entries
            count = min(count, len(entries))
            
            # Select random entries
            random_entries = random.sample(entries, count)
            event_numbers = [entry.event_number for entry in random_entries]
            
            # Update selection status for random entries
            self._update_selection_status("Selected", event_numbers)
            
            st.success(f"Selected {count} random entries.")
            
        except Exception as e:
            st.error(f"Error selecting random entries: {e}")
            self.logger.error(f"Error selecting random entries: {e}")
    
    def _count_selected_entries(self) -> int:
        """
        Count the number of selected entries.
        
        Returns:
            int: The number of selected entries
        """
        entries = self.session.get('all_entries', [])
        return sum(1 for entry in entries if entry.selected == 'Selected')