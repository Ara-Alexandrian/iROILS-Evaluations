"""
Analysis page for the iROILS Evaluations application.

This module provides an interface for administrators to analyze
evaluation data and view statistics.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from app.pages import BasePage
from app.services.database_service import DatabaseService
from app.models.entry import Entry
from app.models.evaluation import Evaluation


class AnalysisPage(BasePage):
    """
    Analysis page component.
    
    This page provides functionality for administrators to analyze
    evaluation data and view statistics.
    """
    
    def __init__(self, db_service: DatabaseService, institution: str = None):
        """
        Initialize the analysis page.
        
        Args:
            db_service (DatabaseService): The database service
            institution (str, optional): The institution to analyze data for
        """
        super().__init__("Analysis Mode")
        self.db_service = db_service
        self.institution = institution
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the analysis page content.
        """
        # Institution selection if not provided
        if self.institution is None:
            self.institution = st.selectbox(
                "Select Institution",
                ["UAB", "MBPCC"],
                key='analysis_institution_select'
            )
        
        st.markdown(f"### Analysis for {self.institution}")
        
        # Load data for analysis
        try:
            # Get entries for the institution
            entries = self.db_service.get_entries(self.institution)
            
            if not entries:
                st.warning(f"No entries found for {self.institution}. Please upload data first.")
                return
            
            # Get evaluators for the institution
            evaluators = [e for e in self.db_service.get_all_evaluators()]
            
            if not evaluators:
                st.warning(f"No evaluations found for {self.institution}.")
                return
            
            # Display analysis tabs
            tabs = st.tabs([
                "Institution Overview", 
                "Evaluator Performance", 
                "Entry Analysis",
                "Statistical Analysis"
            ])
            
            with tabs[0]:
                self._render_institution_overview()
            
            with tabs[1]:
                self._render_evaluator_performance(evaluators)
            
            with tabs[2]:
                self._render_entry_analysis(entries)
            
            with tabs[3]:
                self._render_statistical_analysis(entries, evaluators)
            
        except Exception as e:
            st.error(f"Error loading analysis data: {e}")
            self.logger.error(f"Error loading analysis data: {e}")
    
    def _render_institution_overview(self) -> None:
        """
        Render institution overview.
        """
        st.markdown("### Institution Overview")
        
        try:
            # Get institution stats
            stats = self.db_service.get_institution_stats(self.institution)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Evaluations", stats.total_evaluations)
            
            with col2:
                avg_summary = f"{stats.average_summary:.2f}"
                st.metric("Average Summary Score", avg_summary)
            
            with col3:
                avg_tag = f"{stats.average_tag:.2f}"
                st.metric("Average Tag Score", avg_tag)
            
            # Create institution comparison chart (if institution is not specified)
            if self.institution is None:
                st.markdown("### Institution Comparison")
                
                # Get stats for all institutions
                institutions = ["UAB", "MBPCC"]
                institution_data = []
                
                for inst in institutions:
                    inst_stats = self.db_service.get_institution_stats(inst)
                    institution_data.append({
                        'Institution': inst,
                        'Total Evaluations': inst_stats.total_evaluations,
                        'Average Summary Score': inst_stats.average_summary,
                        'Average Tag Score': inst_stats.average_tag
                    })
                
                # Create comparison chart
                df_inst = pd.DataFrame(institution_data)
                
                fig_inst = go.Figure()
                
                fig_inst.add_trace(go.Bar(
                    x=df_inst['Institution'],
                    y=df_inst['Average Summary Score'],
                    name='Average Summary Score',
                    marker_color='blue'
                ))
                
                fig_inst.add_trace(go.Bar(
                    x=df_inst['Institution'],
                    y=df_inst['Average Tag Score'],
                    name='Average Tag Score',
                    marker_color='green'
                ))
                
                fig_inst.update_layout(
                    barmode='group',
                    title='Average Scores by Institution',
                    xaxis_title='Institution',
                    yaxis_title='Average Score'
                )
                
                st.plotly_chart(fig_inst, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering institution overview: {e}")
            self.logger.error(f"Error rendering institution overview: {e}")
    
    def _render_evaluator_performance(self, evaluators: List[str]) -> None:
        """
        Render evaluator performance analysis.
        
        Args:
            evaluators (List[str]): List of evaluator usernames
        """
        st.markdown("### Evaluator Performance")
        
        try:
            # Create dataframe for evaluator stats
            evaluator_data = []
            
            for evaluator in evaluators:
                # Get evaluator stats
                stats = self.db_service.get_evaluator_stats(evaluator, self.institution)
                
                # Only include evaluators from the selected institution
                if stats['total_evaluations'] > 0:
                    evaluator_data.append({
                        'Evaluator': evaluator,
                        'Total Evaluations': stats['total_evaluations'],
                        'Average Summary Score': stats['average_summary_score'],
                        'Average Tag Score': stats['average_tag_score']
                    })
            
            if not evaluator_data:
                st.info(f"No evaluator data available for {self.institution}.")
                return
                
            # Create dataframe
            df = pd.DataFrame(evaluator_data)
            
            # Display dataframe
            st.dataframe(df, use_container_width=True)
            
            # Create evaluator comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Evaluations per evaluator
                fig_evals = px.bar(
                    df, 
                    x='Evaluator', 
                    y='Total Evaluations',
                    title='Evaluations per Evaluator'
                )
                st.plotly_chart(fig_evals, use_container_width=True)
            
            with col2:
                # Average scores per evaluator
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
                    title='Average Scores per Evaluator',
                    xaxis_title='Evaluator',
                    yaxis_title='Average Score'
                )
                
                st.plotly_chart(fig_scores, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering evaluator performance: {e}")
            self.logger.error(f"Error rendering evaluator performance: {e}")
    
    def _render_entry_analysis(self, entries: List[Entry]) -> None:
        """
        Render entry analysis.
        
        Args:
            entries (List[Entry]): List of entries
        """
        st.markdown("### Entry Analysis")
        
        try:
            # Entry selection
            selected_entries = [e for e in entries if e.selected == 'Selected']
            
            if not selected_entries:
                st.info(f"No selected entries found for {self.institution}.")
                return
            
            # Select entry for analysis
            entry_numbers = [e.event_number for e in selected_entries]
            selected_entry_number = st.selectbox(
                "Select Entry for Analysis",
                entry_numbers
            )
            
            # Get evaluations for the selected entry
            selected_entry = next((e for e in entries if e.event_number == selected_entry_number), None)
            
            if not selected_entry:
                st.error(f"Entry {selected_entry_number} not found.")
                return
            
            # Display entry details
            st.markdown("#### Entry Details")
            
            # Create entry dataframe
            entry_data = {}
            for key, value in selected_entry.data.items():
                if key not in ['Selected'] and value is not None:
                    entry_data[key] = [value]
            
            entry_df = pd.DataFrame(entry_data)
            st.dataframe(entry_df, use_container_width=True)
            
            # Get evaluations for this entry
            st.markdown("#### Evaluations")
            
            evaluations_data = []
            for evaluator in self.db_service.get_all_evaluators():
                eval_obj = self.db_service.get_evaluation(
                    institution=self.institution,
                    evaluator=evaluator,
                    entry_number=selected_entry_number
                )
                
                if eval_obj:
                    evaluations_data.append({
                        'Evaluator': evaluator,
                        'Summary Score': eval_obj.summary_score,
                        'Tag Score': eval_obj.tag_score,
                        'Feedback': eval_obj.feedback or ''
                    })
            
            if not evaluations_data:
                st.info(f"No evaluations found for entry {selected_entry_number}.")
                return
            
            # Display evaluations
            evals_df = pd.DataFrame(evaluations_data)
            st.dataframe(evals_df, use_container_width=True)
            
            # Display evaluation scores chart
            fig_scores = go.Figure()
            
            fig_scores.add_trace(go.Bar(
                x=evals_df['Evaluator'],
                y=evals_df['Summary Score'],
                name='Summary Score',
                marker_color='blue'
            ))
            
            fig_scores.add_trace(go.Bar(
                x=evals_df['Evaluator'],
                y=evals_df['Tag Score'],
                name='Tag Score',
                marker_color='green'
            ))
            
            fig_scores.update_layout(
                barmode='group',
                title=f'Evaluation Scores for Entry {selected_entry_number}',
                xaxis_title='Evaluator',
                yaxis_title='Score'
            )
            
            st.plotly_chart(fig_scores, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering entry analysis: {e}")
            self.logger.error(f"Error rendering entry analysis: {e}")
    
    def _render_statistical_analysis(self, entries: List[Entry], evaluators: List[str]) -> None:
        """
        Render statistical analysis.
        
        Args:
            entries (List[Entry]): List of entries
            evaluators (List[str]): List of evaluator usernames
        """
        st.markdown("### Statistical Analysis")
        
        try:
            # Get evaluations data
            evaluations_data = []
            
            for entry in entries:
                if entry.selected == 'Selected':
                    for evaluator in evaluators:
                        eval_obj = self.db_service.get_evaluation(
                            institution=self.institution,
                            evaluator=evaluator,
                            entry_number=entry.event_number
                        )
                        
                        if eval_obj:
                            evaluations_data.append({
                                'Entry Number': entry.event_number,
                                'Evaluator': evaluator,
                                'Summary Score': eval_obj.summary_score,
                                'Tag Score': eval_obj.tag_score
                            })
            
            if not evaluations_data:
                st.info(f"No evaluation data available for statistical analysis.")
                return
            
            # Create dataframe
            df = pd.DataFrame(evaluations_data)
            
            # Display score distribution
            st.markdown("#### Score Distribution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Summary score histogram
                fig_summary = px.histogram(
                    df,
                    x='Summary Score',
                    nbins=10,
                    title='Summary Score Distribution'
                )
                st.plotly_chart(fig_summary, use_container_width=True)
            
            with col2:
                # Tag score histogram
                fig_tag = px.histogram(
                    df,
                    x='Tag Score',
                    nbins=10,
                    title='Tag Score Distribution'
                )
                st.plotly_chart(fig_tag, use_container_width=True)
            
            # Score statistics
            st.markdown("#### Score Statistics")
            
            summary_stats = {
                'Mean': np.mean(df['Summary Score']),
                'Median': np.median(df['Summary Score']),
                'Standard Deviation': np.std(df['Summary Score']),
                'Min': np.min(df['Summary Score']),
                'Max': np.max(df['Summary Score'])
            }
            
            tag_stats = {
                'Mean': np.mean(df['Tag Score']),
                'Median': np.median(df['Tag Score']),
                'Standard Deviation': np.std(df['Tag Score']),
                'Min': np.min(df['Tag Score']),
                'Max': np.max(df['Tag Score'])
            }
            
            stats_df = pd.DataFrame({
                'Summary Score': summary_stats,
                'Tag Score': tag_stats
            })
            
            st.dataframe(stats_df, use_container_width=True)
            
            # Score correlation
            st.markdown("#### Score Correlation")
            
            fig_corr = px.scatter(
                df,
                x='Summary Score',
                y='Tag Score',
                title='Correlation between Summary and Tag Scores',
                trendline='ols'
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Calculate correlation coefficient
            correlation = np.corrcoef(df['Summary Score'], df['Tag Score'])[0, 1]
            st.markdown(f"**Correlation Coefficient**: {correlation:.3f}")
            
        except Exception as e:
            st.error(f"Error rendering statistical analysis: {e}")
            self.logger.error(f"Error rendering statistical analysis: {e}")