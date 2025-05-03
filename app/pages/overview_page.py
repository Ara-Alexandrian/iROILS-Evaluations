"""
Overview page for the iROILS Evaluations application.

This module provides an interface for administrators to get an overview
of entries and upload new data.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional

import streamlit as st

from app.pages import BasePage
from app.services.database_service import DatabaseService
from app.models.entry import Entry


class OverviewPage(BasePage):
    """
    Overview page component.
    
    This page provides functionality for administrators to get an overview
    of entries and upload new data.
    """
    
    def __init__(self, db_service: DatabaseService, institution: str):
        """
        Initialize the overview page.
        
        Args:
            db_service (DatabaseService): The database service
            institution (str): The institution to manage entries for
        """
        super().__init__("Overview Mode")
        self.db_service = db_service
        self.institution = institution
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the overview page content.
        """
        st.markdown(f"### Entry Overview for {self.institution}")
        
        # Get institution statistics
        self._render_institution_stats()
        
        # Get entries
        try:
            entries = self.db_service.get_entries(self.institution)
            
            if not entries:
                st.warning(f"No entries found for {self.institution}. Please upload data first.")
                return
            
            # Display entries
            self._render_entries_overview(entries)
            
        except Exception as e:
            st.error(f"Error loading entries: {e}")
            self.logger.error(f"Error loading entries: {e}")
    
    def _render_institution_stats(self) -> None:
        """
        Render institution statistics.
        """
        try:
            # Get institution stats
            stats = self.db_service.get_institution_stats(self.institution)
            
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
    
    def render_file_upload(self) -> None:
        """
        Render file upload interface.
        """
        st.markdown("### Upload New Data")
        
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
        
        if uploaded_file:
            try:
                # Read Excel file
                df = pd.read_excel(uploaded_file)
                df = df.where(pd.notnull(df), None)
                
                # Check for required columns
                if 'Event Number' not in df.columns:
                    st.error("The uploaded file must contain an 'Event Number' column.")
                    return
                
                # Remove 'Selected' column if present
                if 'Selected' in df.columns:
                    df.drop(columns=['Selected'], inplace=True)
                    st.info("Removed 'Selected' column from uploaded data.")
                
                # Preview data
                st.markdown("### Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Confirm upload
                if st.button("Confirm Upload"):
                    # Convert dataframe to entries
                    entries = []
                    
                    for _, row in df.iterrows():
                        # Convert row to dictionary
                        row_dict = row.to_dict()
                        
                        # Set default selection status
                        row_dict['Selected'] = 'Do Not Select'
                        
                        # Create Entry object
                        entry = Entry(
                            institution=self.institution.lower().strip(),
                            event_number=str(row_dict.get('Event Number', '')),
                            data=row_dict,
                            selected='Do Not Select'
                        )
                        
                        entries.append(entry)
                    
                    # Save entries to database
                    self.db_service.save_entries(entries)
                    
                    # Update session state
                    all_entries = self.db_service.get_entries(self.institution)
                    self.session.set('all_entries', all_entries)
                    self.session.set('total_entries', len(all_entries))
                    
                    st.success(f"Successfully uploaded {len(entries)} entries for {self.institution}.")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error processing uploaded file: {e}")
                self.logger.error(f"Error processing uploaded file: {e}")
        else:
            st.info("Please upload an Excel (.xlsx) file containing entry data.")