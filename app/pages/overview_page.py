"""
Overview page for the iROILS Evaluations application.

This module provides the overview interface for the application.
"""

import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.pages import BasePage


class OverviewPage(BasePage):
    """
    Overview page component.
    
    This page provides a high-level overview of the application status
    and available features.
    """
    
    def __init__(self, auth_service: AuthService, db_service: DatabaseService):
        """
        Initialize the overview page.
        
        Args:
            auth_service (AuthService): The authentication service
            db_service (DatabaseService): The database service
        """
        super().__init__("iROILS Evaluations Overview")
        self.auth_service = auth_service
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the overview page content.
        """
        st.markdown("## Welcome to iROILS Evaluations")
        
        st.markdown("""
        This application provides a comprehensive platform for evaluation and analysis of entries.
        
        ### Available Features:
        
        - **Admin Dashboard**: Manage entries, evaluators, and view statistics
        - **Data Analysis**: Explore evaluation data with interactive visualizations
        - **Tag Analysis**: Analyze tag usage and scoring patterns
        - **User Submission**: Submit evaluations for selected entries
        
        Select a module from the sidebar to get started.
        """)
        
        # Display system statistics
        self._display_system_stats()
    
    def _display_system_stats(self) -> None:
        """
        Display system statistics.
        """
        st.markdown("## System Statistics")
        
        try:
            # Get institutions
            institutions = ["UAB", "MBPCC"]
            
            # Initialize statistics
            total_entries = 0
            total_evaluations = 0
            evaluator_count = 0
            
            # Get statistics for each institution
            institution_stats = []
            
            for institution in institutions:
                # Get institution stats
                stats = self.db_service.get_institution_stats(institution)
                
                # Get entries
                entries = self.db_service.get_entries(institution)
                
                # Get selected entries
                selected_entries = [e for e in entries if e.selected == 'Selected']
                
                # Add to totals
                total_entries += len(entries)
                total_evaluations += stats.total_evaluations
                
                # Add institution stats
                institution_stats.append({
                    'Institution': institution,
                    'Total Entries': len(entries),
                    'Selected Entries': len(selected_entries),
                    'Total Evaluations': stats.total_evaluations,
                    'Average Summary Score': stats.average_summary,
                    'Average Tag Score': stats.average_tag
                })
            
            # Get evaluator count
            evaluators = self.db_service.get_all_evaluators()
            evaluator_count = len(evaluators)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Entries", total_entries)
            
            with col2:
                st.metric("Total Evaluations", total_evaluations)
            
            with col3:
                st.metric("Evaluators", evaluator_count)
            
            # Display institution statistics
            if institution_stats:
                st.markdown("### Institution Statistics")
                
                # Create dataframe
                df = pd.DataFrame(institution_stats)
                
                # Display as a table using markdown
                st.markdown("| Institution | Total Entries | Selected Entries | Total Evaluations | Avg Summary | Avg Tag |")
                st.markdown("|-------------|---------------|------------------|-------------------|-------------|---------|")
                
                for _, row in df.iterrows():
                    st.markdown(
                        f"| {row['Institution']} | {row['Total Entries']} | {row['Selected Entries']} | "
                        f"{row['Total Evaluations']} | {row['Average Summary Score']:.2f} | {row['Average Tag Score']:.2f} |"
                    )
                
                # Create institution comparison chart
                st.markdown("### Institution Comparison")
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df['Institution'],
                    y=df['Average Summary Score'],
                    name='Average Summary Score',
                    marker_color='blue'
                ))
                
                fig.add_trace(go.Bar(
                    x=df['Institution'],
                    y=df['Average Tag Score'],
                    name='Average Tag Score',
                    marker_color='green'
                ))
                
                fig.update_layout(
                    barmode='group',
                    title='Average Scores by Institution',
                    xaxis_title='Institution',
                    yaxis_title='Average Score'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading system statistics: {e}")
            self.logger.error(f"Error loading system statistics: {e}")
            
    def render(self) -> None:
        """
        Render the overview page.
        """
        # Set title
        st.title(self.title)
        
        # Render content
        self._render_content()