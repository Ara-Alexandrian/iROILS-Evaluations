"""
Admin dashboard page for the iROILS Evaluations application.

This module provides the admin dashboard interface for managing
institutions, data, and accessing various application features.
"""

import logging
import random
import pandas as pd
from typing import Dict, List, Any, Optional

import streamlit as st

from app.pages import SecurePage
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.core.session import SessionState
from app.models.entry import Entry
from app.pages.analysis_page import AnalysisPage


class AdminPage(SecurePage):
    """
    Admin dashboard page component.
    
    This page provides administrative functionality for managing
    institutions, data, and accessing various application features.
    """
    
    def __init__(self, auth_service: AuthService, db_service: DatabaseService):
        """
        Initialize the admin page.
        
        Args:
            auth_service (AuthService): The authentication service
            db_service (DatabaseService): The database service
        """
        super().__init__("Admin Dashboard", auth_service, required_role='admin')
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the admin dashboard content.
        """
        # Institution selection
        institution = st.selectbox(
            "Select Institution", 
            ["UAB", "MBPCC"], 
            key='institution_select',
            on_change=self._reset_session_state
        )
        
        # Load entries if not already loaded
        if not self.session.has('all_entries'):
            try:
                all_entries = self.db_service.get_entries(institution)
                
                if not all_entries:
                    self.session.set('all_entries', [])
                    self.session.set('total_entries', 0)
                    st.warning("No data available for the selected institution.")
                else:
                    self.session.set('all_entries', all_entries)
                    self.session.set('total_entries', len(all_entries))
            except Exception as e:
                st.error(f"Error loading entries: {e}")
                return
        
        # Mode selection
        mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode", "Analysis Mode"], index=0)
        
        # Render appropriate content based on mode
        if mode == "Analysis Mode" and self.session.get('total_entries', 0) > 0:
            self._render_analysis_mode(institution)
        elif mode == "Selection Mode" and self.session.get('total_entries', 0) > 0:
            self._render_selection_mode(institution)
        elif mode == "Overview Mode":
            self._render_overview_mode(institution)
    
    def _render_analysis_mode(self, institution: str) -> None:
        """
        Render analysis mode content.
        
        Args:
            institution (str): The selected institution
        """
        st.markdown("## Analysis Mode")
        
        # Import analysis page component
        from app.pages.analysis_page import AnalysisPage
        
        # Create and render the analysis page
        analysis_page = AnalysisPage(self.db_service, institution)
        analysis_page._render_content()  # Direct call to avoid title duplication
    
    def _render_selection_mode(self, institution: str) -> None:
        """
        Render selection mode content.
        
        Args:
            institution (str): The selected institution
        """
        st.markdown("## Selection Mode")
        
        # Import selection page component
        from app.pages.selection_page import SelectionPage
        
        # Create and render the selection page
        selection_page = SelectionPage(self.db_service, institution)
        
        # Load entries if not already loaded
        all_entries = self.session.get('all_entries')
        if not all_entries:
            try:
                all_entries = self.db_service.get_entries(institution)
                
                if not all_entries:
                    st.warning(f"No entries found for {institution}. Please upload data first.")
                    return
                
                self.session.set('all_entries', all_entries)
                self.session.set('total_entries', len(all_entries))
                
            except Exception as e:
                st.error(f"Error loading entries: {e}")
                self.logger.error(f"Error loading entries: {e}")
                return
        
        # Display selection controls
        self._render_selection_controls(institution)
        
        # Display entries table
        self._render_entries_table(all_entries)
        
    def _render_selection_controls(self, institution: str) -> None:
        """
        Render selection control buttons.
        
        Args:
            institution (str): The selected institution
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
    
    def _render_overview_mode(self, institution: str) -> None:
        """
        Render overview mode content.
        
        Args:
            institution (str): The selected institution
        """
        st.markdown("## Overview Mode")
        
        # Get institution statistics
        self._render_institution_stats(institution)
        
        # Get entries
        try:
            entries = self.db_service.get_entries(institution)
            
            if not entries:
                st.warning(f"No entries found for {institution}. Please upload data first.")
                return
            
            # Display entries
            self._render_entries_overview(entries)
            
        except Exception as e:
            st.error(f"Error loading entries: {e}")
            self.logger.error(f"Error loading entries: {e}")
        
        # Add data management section
        st.markdown("### Data Management")
        self._render_file_upload(institution)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Reset Data"):
                self._reset_institution_data(institution)
                st.rerun()
                
    def _render_institution_stats(self, institution: str) -> None:
        """
        Render institution statistics.
        """
        try:
            # Get institution stats
            stats = self.db_service.get_institution_stats(institution)
            
            # Calculate derived statistics
            total_entries = self.session.get('total_entries', 0)
            selected_entries = sum(1 for entry in self.session.get('all_entries', []) 
                                 if entry.selected == 'Selected')
            
            # Display statistics
            st.markdown("### Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Entries", total_entries)
            
            with col2:
                st.metric("Selected Entries", selected_entries)
            
            with col3:
                st.metric("Total Evaluations", stats.total_evaluations)
            
            with col4:
                if stats.total_evaluations > 0:
                    avg_summary = f"{stats.average_summary:.2f}"
                    st.metric("Avg Summary Score", avg_summary)
                else:
                    st.metric("Avg Summary Score", "N/A")
            
        except Exception as e:
            st.error(f"Error loading institution statistics: {e}")
            self.logger.error(f"Error loading institution statistics: {e}")
            
    def _render_entries_overview(self, entries: List[Entry]) -> None:
        """
        Render an overview of entries.
        
        Args:
            entries (List[Entry]): The entries to display
        """
        st.markdown("### Entries Overview")
        
        # Filter options
        selection_filter = st.selectbox(
            "Filter by Selection Status",
            ["All", "Selected", "Not Selected"],
            index=0
        )
        
        # Apply filters
        filtered_entries = entries
        
        if selection_filter == "Selected":
            filtered_entries = [e for e in entries if e.selected == 'Selected']
        elif selection_filter == "Not Selected":
            filtered_entries = [e for e in entries if e.selected != 'Selected']
        
        # Convert entries to dataframe for display
        entries_data = []
        
        for entry in filtered_entries:
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
            st.warning("No entries match the selected filters.")
            return
        
        # Create dataframe
        df = pd.DataFrame(entries_data)
        
        # Display dataframe
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )
        
        # Display summary
        st.markdown(f"**Showing {len(filtered_entries)} of {len(entries)} entries**")
    
    def _render_file_upload(self, institution: str) -> None:
        """
        Render file upload interface.
        
        Args:
            institution (str): The selected institution
        """
        st.markdown("### Upload New Data")
        uploaded_file = st.file_uploader("Upload New Data", type="xlsx")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                df = df.where(pd.notnull(df), None)
                
                if 'Selected' in df.columns:
                    df.drop(columns=['Selected'], inplace=True)
                    st.write("Removed 'Selected' column from uploaded data.")
                
                new_entries = df.to_dict(orient="records")
                entries_to_save = []
                
                for entry_data in new_entries:
                    entry_data['Selected'] = 'Do Not Select'  # Force 'Do Not Select' for every entry
                    
                    # Create Entry object
                    entry = Entry(
                        institution=institution.lower().strip(),
                        event_number=str(entry_data.get('Event Number', '')),
                        data=entry_data,
                        selected='Do Not Select'
                    )
                    entries_to_save.append(entry)
                
                # Save entries to database
                self.db_service.save_entries(entries_to_save)
                
                # Reload entries
                all_entries = self.db_service.get_entries(institution)
                self.session.set('all_entries', all_entries)
                self.session.set('total_entries', len(all_entries))
                
                st.success(f"New data for {institution} uploaded successfully!")
                st.rerun()  # Refresh the page
            except Exception as e:
                self.logger.error(f"Error processing uploaded file: {e}")
                st.error(f"Error processing uploaded file: {e}")
        else:
            st.info("Please upload an Excel (.xlsx) file.")
    
    def _reset_institution_data(self, institution: str) -> None:
        """
        Reset all data for an institution.
        
        Args:
            institution (str): The institution to reset data for
        """
        try:
            st.write(f"Resetting data for institution: {institution}")
            self.db_service.reset_institution_data(institution)
            
            # Clear session state
            self._reset_session_state()
            
            st.success(f"All data for {institution} has been reset.")
        except Exception as e:
            st.error(f"Error during reset: {e}")
    
    def _reset_session_state(self) -> None:
        """Reset session state related to entries."""
        self.session.pop('all_entries', None)
        self.session.pop('total_entries', None)
        self.session.pop('current_index', None)