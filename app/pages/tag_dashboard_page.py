"""
Dashboard page for the iROILS Evaluations application focusing on tag analysis.

This module provides a tag-focused dashboard interface for analyzing
evaluation data and gaining insights into tag usage and scores.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.pages import BasePage
from app.services.database_service import DatabaseService
from app.models.entry import Entry
from app.models.evaluation import Evaluation


class TagDashboardPage(BasePage):
    """
    Tag Analysis Dashboard page component.
    
    This page provides functionality for administrators to analyze
    tag data and view detailed statistics about tag usage and scoring.
    """
    
    def __init__(self, db_service: DatabaseService, institution: str = None):
        """
        Initialize the dashboard page.
        
        Args:
            db_service (DatabaseService): The database service
            institution (str, optional): The institution to analyze data for
        """
        super().__init__("Tag Analysis Dashboard")
        self.db_service = db_service
        self.institution = institution
        self.logger = logging.getLogger(__name__)
    
    def _render_content(self) -> None:
        """
        Render the dashboard content.
        """
        # Institution selection if not provided
        if self.institution is None:
            self.institution = st.selectbox(
                "Select Institution",
                ["UAB", "MBPCC"],
                key='dashboard_institution_select'
            )
        
        st.markdown(f"## Tag Analysis for {self.institution}")
        
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
                "Tag Score Overview", 
                "Tag Distribution",
                "Tag Comparison",
                "Evaluator Tag Scoring"
            ])
            
            with tabs[0]:
                self._render_tag_score_overview(entries, evaluators)
            
            with tabs[1]:
                self._render_tag_distribution(entries)
            
            with tabs[2]:
                self._render_tag_comparison(entries, evaluators)
            
            with tabs[3]:
                self._render_evaluator_tag_scoring(evaluators)
            
        except Exception as e:
            st.error(f"Error loading tag analysis data: {e}")
            self.logger.error(f"Error loading tag analysis data: {e}")
    
    def _render_tag_score_overview(self, entries: List[Entry], evaluators: List[str]) -> None:
        """
        Render tag score overview.
        
        Args:
            entries (List[Entry]): List of entries
            evaluators (List[str]): List of evaluators
        """
        st.markdown("### Tag Score Overview")
        
        try:
            # Get institution stats
            stats = self.db_service.get_institution_stats(self.institution)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Evaluations", stats.total_evaluations)
            
            with col2:
                avg_tag = f"{stats.average_tag:.2f}"
                st.metric("Average Tag Score", avg_tag)
            
            with col3:
                # Calculate difference from summary score
                diff = stats.average_tag - stats.average_summary
                diff_text = f"{diff:.2f}"
                st.metric("Difference from Summary", diff_text, delta=diff)
            
            # Create score distribution chart
            st.markdown("#### Tag Score Distribution")
            
            # Collect all tag scores
            tag_scores = []
            
            for entry in entries:
                if entry.selected == 'Selected':
                    for evaluator in evaluators:
                        eval_obj = self.db_service.get_evaluation(
                            institution=self.institution,
                            evaluator=evaluator,
                            entry_number=entry.event_number
                        )
                        
                        if eval_obj:
                            tag_scores.append(eval_obj.tag_score)
            
            if tag_scores:
                fig = go.Figure()
                
                # Add histogram of tag scores
                fig.add_trace(go.Histogram(
                    x=tag_scores,
                    nbinsx=10,
                    marker_color='green',
                    name='Tag Scores'
                ))
                
                fig.update_layout(
                    title='Distribution of Tag Scores',
                    xaxis_title='Score',
                    yaxis_title='Frequency',
                    bargap=0.1
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add statistics
                st.markdown("#### Tag Score Statistics")
                
                stats_data = {
                    'Mean': np.mean(tag_scores),
                    'Median': np.median(tag_scores),
                    'Standard Deviation': np.std(tag_scores),
                    'Min': np.min(tag_scores),
                    'Max': np.max(tag_scores)
                }
                
                # Display statistics as a markdown table
                st.markdown("| Statistic | Value |")
                st.markdown("|----------|-------|")
                for stat, value in stats_data.items():
                    st.markdown(f"| **{stat}** | {value:.2f} |")
            else:
                st.info("No tag scores available for analysis.")
                
        except Exception as e:
            st.error(f"Error rendering tag score overview: {e}")
            self.logger.error(f"Error rendering tag score overview: {e}")
    
    def _render_tag_distribution(self, entries: List[Entry]) -> None:
        """
        Render tag distribution analysis.
        
        Args:
            entries (List[Entry]): List of entries
        """
        st.markdown("### Tag Distribution Analysis")
        
        try:
            # Extract tags from entries
            tag_data = []
            
            for entry in entries:
                # Check if 'Assigned Tags' exists in the entry data
                assigned_tags = entry.data.get('Assigned Tags', '')
                
                if assigned_tags:
                    # Split tags if they're in a comma-separated format
                    if isinstance(assigned_tags, str):
                        tags = [tag.strip() for tag in assigned_tags.split(',') if tag.strip()]
                    elif isinstance(assigned_tags, list):
                        tags = assigned_tags
                    else:
                        tags = [str(assigned_tags)]
                    
                    for tag in tags:
                        tag_data.append({
                            'Entry': entry.event_number,
                            'Tag': tag,
                            'Selected': entry.selected == 'Selected'
                        })
            
            if tag_data:
                # Create dataframe
                tag_df = pd.DataFrame(tag_data)
                
                # Count tag frequency
                tag_counts = tag_df['Tag'].value_counts().reset_index()
                tag_counts.columns = ['Tag', 'Count']
                
                # Sort by count
                tag_counts = tag_counts.sort_values('Count', ascending=False)
                
                # Display tag frequency chart
                st.markdown("#### Tag Frequency")
                
                fig = px.bar(
                    tag_counts,
                    x='Tag',
                    y='Count',
                    title='Frequency of Tags',
                    labels={'Count': 'Number of Entries', 'Tag': 'Tag'}
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Tag distribution in selected vs. non-selected entries
                st.markdown("#### Tags in Selected vs. Non-Selected Entries")
                
                # Group by tag and selection status
                selection_counts = tag_df.groupby(['Tag', 'Selected']).size().reset_index(name='Count')
                
                # Pivot for easier plotting
                pivot_df = selection_counts.pivot(index='Tag', columns='Selected', values='Count').fillna(0)
                pivot_df.columns = ['Not Selected', 'Selected']
                pivot_df = pivot_df.reset_index()
                
                # Sort by total count
                pivot_df['Total'] = pivot_df['Selected'] + pivot_df['Not Selected']
                pivot_df = pivot_df.sort_values('Total', ascending=False).head(10)  # Top 10 tags
                
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=pivot_df['Tag'],
                    y=pivot_df['Selected'],
                    name='Selected',
                    marker_color='green'
                ))
                
                fig.add_trace(go.Bar(
                    x=pivot_df['Tag'],
                    y=pivot_df['Not Selected'],
                    name='Not Selected',
                    marker_color='red'
                ))
                
                fig.update_layout(
                    title='Top 10 Tags by Selection Status',
                    xaxis_title='Tag',
                    yaxis_title='Count',
                    barmode='group',
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No tag data available for analysis.")
                
        except Exception as e:
            st.error(f"Error rendering tag distribution: {e}")
            self.logger.error(f"Error rendering tag distribution: {e}")
    
    def _render_tag_comparison(self, entries: List[Entry], evaluators: List[str]) -> None:
        """
        Render tag and summary score comparison.
        
        Args:
            entries (List[Entry]): List of entries
            evaluators (List[str]): List of evaluators
        """
        st.markdown("### Tag and Summary Score Comparison")
        
        try:
            # Collect evaluation data
            evaluation_data = []
            
            for entry in entries:
                if entry.selected == 'Selected':
                    # Extract tags
                    assigned_tags = entry.data.get('Assigned Tags', '')
                    
                    # Process tags
                    if isinstance(assigned_tags, str):
                        tags = [tag.strip() for tag in assigned_tags.split(',') if tag.strip()]
                    elif isinstance(assigned_tags, list):
                        tags = assigned_tags
                    else:
                        tags = [str(assigned_tags)] if assigned_tags else []
                    
                    # Get evaluations for this entry
                    for evaluator in evaluators:
                        eval_obj = self.db_service.get_evaluation(
                            institution=self.institution,
                            evaluator=evaluator,
                            entry_number=entry.event_number
                        )
                        
                        if eval_obj:
                            for tag in tags:
                                evaluation_data.append({
                                    'Entry': entry.event_number,
                                    'Evaluator': evaluator,
                                    'Tag': tag,
                                    'Summary Score': eval_obj.summary_score,
                                    'Tag Score': eval_obj.tag_score
                                })
            
            if evaluation_data:
                # Create dataframe
                eval_df = pd.DataFrame(evaluation_data)
                
                # Overall correlation scatter plot
                st.markdown("#### Correlation Between Summary and Tag Scores")
                
                fig = px.scatter(
                    eval_df,
                    x='Summary Score',
                    y='Tag Score',
                    title='Correlation Between Summary and Tag Scores',
                    trendline='ols',
                    labels={'Summary Score': 'Summary Score', 'Tag Score': 'Tag Score'}
                )
                
                fig.update_layout(
                    xaxis_range=[0, 10],
                    yaxis_range=[0, 10]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate correlation coefficient
                correlation = np.corrcoef(eval_df['Summary Score'], eval_df['Tag Score'])[0, 1]
                st.markdown(f"**Correlation Coefficient**: {correlation:.3f}")
                
                # Average scores by tag
                st.markdown("#### Average Scores by Tag")
                
                tag_avg = eval_df.groupby('Tag').agg({
                    'Summary Score': 'mean',
                    'Tag Score': 'mean',
                    'Entry': 'count'
                }).reset_index()
                
                tag_avg.columns = ['Tag', 'Avg Summary Score', 'Avg Tag Score', 'Count']
                tag_avg = tag_avg.sort_values('Count', ascending=False)
                
                # Display only the top 10 tags by count
                top_tags = tag_avg.head(10)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=top_tags['Tag'],
                    y=top_tags['Avg Summary Score'],
                    name='Avg Summary Score',
                    marker_color='blue'
                ))
                
                fig.add_trace(go.Bar(
                    x=top_tags['Tag'],
                    y=top_tags['Avg Tag Score'],
                    name='Avg Tag Score',
                    marker_color='green'
                ))
                
                fig.update_layout(
                    title='Average Scores by Tag (Top 10)',
                    xaxis_title='Tag',
                    yaxis_title='Average Score',
                    barmode='group',
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate score differences by tag
                top_tags['Score Difference'] = top_tags['Avg Tag Score'] - top_tags['Avg Summary Score']
                top_tags = top_tags.sort_values('Score Difference')
                
                # Plot score differences
                st.markdown("#### Tag vs Summary Score Differences")
                
                fig = px.bar(
                    top_tags,
                    x='Tag',
                    y='Score Difference',
                    title='Difference Between Tag and Summary Scores',
                    labels={'Score Difference': 'Tag Score - Summary Score', 'Tag': 'Tag'},
                    color='Score Difference',
                    color_continuous_scale=['red', 'white', 'green'],
                    color_continuous_midpoint=0
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No evaluation data available for tag comparison.")
                
        except Exception as e:
            st.error(f"Error rendering tag comparison: {e}")
            self.logger.error(f"Error rendering tag comparison: {e}")
    
    def _render_evaluator_tag_scoring(self, evaluators: List[str]) -> None:
        """
        Render evaluator tag scoring analysis.
        
        Args:
            evaluators (List[str]): List of evaluators
        """
        st.markdown("### Evaluator Tag Scoring Analysis")
        
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
                        'Average Tag Score': stats['average_tag_score'],
                        'Difference': stats['average_tag_score'] - stats['average_summary_score']
                    })
            
            if not evaluator_data:
                st.info(f"No evaluator data available for {self.institution}.")
                return
                
            # Create dataframe
            df = pd.DataFrame(evaluator_data)
            
            # Display evaluator data
            st.markdown("#### Evaluator Tag Scoring Patterns")
            
            # Create custom table display
            st.markdown("| Evaluator | Total Evaluations | Avg Summary | Avg Tag | Difference |")
            st.markdown("|-----------|-------------------|-------------|---------|------------|")
            
            for _, row in df.iterrows():
                diff = row['Difference']
                diff_formatted = f"{diff:.2f}"
                
                # Format the difference with a visual indicator
                if diff > 0:
                    diff_cell = f"{diff_formatted} ↑"
                elif diff < 0:
                    diff_cell = f"{diff_formatted} ↓"
                else:
                    diff_cell = f"{diff_formatted} ="
                
                st.markdown(
                    f"| {row['Evaluator']} | {row['Total Evaluations']} | "
                    f"{row['Average Summary Score']:.2f} | {row['Average Tag Score']:.2f} | {diff_cell} |"
                )
            
            # Average scores by evaluator chart
            st.markdown("#### Tag Scoring by Evaluator")
            
            # Sort evaluators by difference
            df_sorted = df.sort_values('Difference')
            
            # Create a horizontal bar chart showing the difference
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=df_sorted['Evaluator'],
                x=df_sorted['Difference'],
                orientation='h',
                name='Tag vs Summary Difference',
                marker=dict(
                    color=df_sorted['Difference'],
                    colorscale='RdBu',
                    cmin=-2,
                    cmax=2,
                    colorbar=dict(title='Difference')
                )
            ))
            
            fig.update_layout(
                title='Difference Between Tag and Summary Scores by Evaluator',
                xaxis_title='Tag Score - Summary Score',
                yaxis_title='Evaluator',
                height=max(400, len(df) * 40)  # Dynamically adjust height based on number of evaluators
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Evaluator comparison with dual-axis chart
            st.markdown("#### Summary vs Tag Scores by Evaluator")
            
            # Sort by evaluator name for this chart
            df_name_sorted = df.sort_values('Evaluator')
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=df_name_sorted['Evaluator'],
                    y=df_name_sorted['Average Summary Score'],
                    name="Avg Summary Score",
                    marker_color='blue'
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Bar(
                    x=df_name_sorted['Evaluator'],
                    y=df_name_sorted['Average Tag Score'],
                    name="Avg Tag Score",
                    marker_color='green'
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_name_sorted['Evaluator'],
                    y=df_name_sorted['Difference'],
                    name="Difference",
                    mode="lines+markers",
                    marker_color='red',
                    line=dict(width=3, dash='dot')
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title="Summary vs Tag Scores by Evaluator",
                barmode='group',
                xaxis_tickangle=-45
            )
            
            fig.update_yaxes(title_text="Average Score", secondary_y=False)
            fig.update_yaxes(title_text="Difference", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering evaluator tag scoring: {e}")
            self.logger.error(f"Error rendering evaluator tag scoring: {e}")