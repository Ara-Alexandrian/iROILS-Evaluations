"""
PostgreSQL dashboard page for the iROILS Evaluations application.

This module provides a dashboard interface for visualizing and analyzing
evaluation data from the PostgreSQL database.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from app.pages import SecurePage
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService


class DashboardPage(SecurePage):
    """
    PostgreSQL dashboard page component.
    
    This page provides a visualization interface for administrators
    to analyze evaluation data.
    """
    
    def __init__(self, auth_service: AuthService, db_service: DatabaseService):
        """
        Initialize the dashboard page.
        
        Args:
            auth_service (AuthService): The authentication service
            db_service (DatabaseService): The database service
        """
        super().__init__("PostgreSQL Dashboard", auth_service, required_role='admin')
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the dashboard content.
        """
        # Institution selection
        institution = st.selectbox(
            "Select Institution",
            ["UAB", "MBPCC"],
            key='dashboard_institution_select'
        )
        
        # Load evaluators and entries
        try:
            # Get all evaluators
            evaluators = self.db_service.get_all_evaluators()
            
            if not evaluators:
                st.warning("No evaluators found. No data to display.")
                return
                
            # Get entries for the selected institution
            entries = self.db_service.get_entries(institution)
            
            if not entries:
                st.warning(f"No entries found for {institution}.")
                return
                
            # Display dashboard
            self._display_institution_stats(institution)
            self._display_evaluator_stats(evaluators, institution)
            self._display_entry_stats(entries)
            
        except Exception as e:
            st.error(f"Error loading dashboard data: {e}")
            self.logger.error(f"Error loading dashboard data: {e}")
    
    def _display_institution_stats(self, institution: str) -> None:
        """
        Display institution statistics.
        
        Args:
            institution (str): The institution to display statistics for
        """
        st.markdown("## Institution Statistics")
        
        try:
            # Get institution stats
            stats = self.db_service.get_institution_stats(institution)
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Evaluations", stats.total_evaluations)
                
            with col2:
                # Format average summary score to 2 decimal places
                avg_summary = f"{stats.average_summary:.2f}"
                st.metric("Average Summary Score", avg_summary)
                
            with col3:
                # Format average tag score to 2 decimal places
                avg_tag = f"{stats.average_tag:.2f}"
                st.metric("Average Tag Score", avg_tag)
            
        except Exception as e:
            st.error(f"Error loading institution statistics: {e}")
            self.logger.error(f"Error loading institution statistics: {e}")
    
    def _display_evaluator_stats(self, evaluators: List[str], institution: str) -> None:
        """
        Display evaluator statistics.
        
        Args:
            evaluators (List[str]): List of evaluator usernames
            institution (str): The institution to filter evaluations by
        """
        st.markdown("## Evaluator Statistics")
        
        try:
            # Create dataframe for evaluator stats
            evaluator_data = []
            
            for evaluator in evaluators:
                # Get evaluator stats
                stats = self.db_service.get_evaluator_stats(evaluator, institution)
                
                # Only include evaluators from the selected institution
                if stats['total_evaluations'] > 0:
                    evaluator_data.append({
                        'Evaluator': evaluator,
                        'Total Evaluations': stats['total_evaluations'],
                        'Average Summary Score': stats['average_summary_score'],
                        'Average Tag Score': stats['average_tag_score']
                    })
            
            if not evaluator_data:
                st.info(f"No evaluators found for {institution}.")
                return
                
            # Create dataframe
            df = pd.DataFrame(evaluator_data)
            
            # Display dataframe
            st.dataframe(df)
            
            # Create bar chart for evaluations per evaluator
            fig_evals = px.bar(
                df, 
                x='Evaluator', 
                y='Total Evaluations',
                title=f'Evaluations per Evaluator ({institution})'
            )
            st.plotly_chart(fig_evals, use_container_width=True)
            
            # Create bar chart for average scores
            fig_scores = go.Figure()
            
            fig_scores.add_trace(go.Bar(
                x=df['Evaluator'],
                y=df['Average Summary Score'],
                name='Average Summary Score',
                marker_color='blue'
            ))
            
            fig_scores.add_trace(go.Bar(
                x=df['Evaluator'],
                y=df['Average Tag Score'],
                name='Average Tag Score',
                marker_color='green'
            ))
            
            fig_scores.update_layout(
                barmode='group',
                title=f'Average Scores per Evaluator ({institution})',
                xaxis_title='Evaluator',
                yaxis_title='Average Score'
            )
            
            st.plotly_chart(fig_scores, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading evaluator statistics: {e}")
            self.logger.error(f"Error loading evaluator statistics: {e}")
    
    def _display_entry_stats(self, entries: List[Any]) -> None:
        """
        Display entry statistics.
        
        Args:
            entries (List[Any]): List of entries
        """
        st.markdown("## Entry Statistics")
        
        try:
            # Count selected vs. non-selected entries
            selection_counts = {}
            
            for entry in entries:
                selected = entry.selected
                if selected not in selection_counts:
                    selection_counts[selected] = 0
                selection_counts[selected] += 1
            
            # Prepare data for pie chart
            selection_data = [{
                'Selection Status': status,
                'Count': count
            } for status, count in selection_counts.items()]
            
            df_selection = pd.DataFrame(selection_data)
            
            # Create pie chart for selection status
            fig_selection = px.pie(
                df_selection,
                values='Count',
                names='Selection Status',
                title='Entry Selection Status',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            
            st.plotly_chart(fig_selection, use_container_width=True)
            
            # Display entry count
            st.metric("Total Entries", len(entries))
            
        except Exception as e:
            st.error(f"Error loading entry statistics: {e}")
            self.logger.error(f"Error loading entry statistics: {e}")