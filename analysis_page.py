# analysis_page.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from institution_manager import InstitutionManager

class AnalysisPage:
    def __init__(self, institution_manager):
        self.institution_manager = institution_manager

    def show(self):
        st.header("Analysis Mode")

        # Load data for all institutions
        institutions = ["UAB", "MBPCC"]
        all_data = {}
        total_entries = 0

        # Collect data from all institutions
        for institution in institutions:
            entries, _ = self.institution_manager.get_institution_data(institution)
            total_entries += len(entries)
            evaluated_entries = [
                entry for entry in entries if 'Evaluations' in entry and entry['Evaluations']
            ]
            all_data[institution] = {
                'entries': entries,
                'evaluated_entries': evaluated_entries
            }

        # Check if there are any evaluations
        total_evaluations = sum(len(data['evaluated_entries']) for data in all_data.values())
        if total_evaluations == 0:
            st.write("No entries have been evaluated yet.")
            st.markdown(f"**Total Entries in Database:** {total_entries}")
            return

        # Display institution-wise averages
        st.subheader("Institution Averages")
        institution_stats = {}

        for institution, data in all_data.items():
            evaluated_entries = data['evaluated_entries']
            summary_scores = []
            tag_scores = []

            for entry in evaluated_entries:
                for eval in entry['Evaluations']:
                    summary_score = eval.get('Summary Score', 0)
                    tag_score = eval.get('Tag Score', 0)
                    summary_scores.append(summary_score)
                    tag_scores.append(tag_score)

            if summary_scores:
                avg_summary_score = np.mean(summary_scores)
            else:
                avg_summary_score = 0

            if tag_scores:
                avg_tag_score = np.mean(tag_scores)
            else:
                avg_tag_score = 0

            institution_stats[institution] = {
                'avg_summary_score': avg_summary_score,
                'avg_tag_score': avg_tag_score,
                'total_evaluations': len(summary_scores)
            }

        # Display averages in a table
        stats_df = pd.DataFrame.from_dict(institution_stats, orient='index')
        stats_df = stats_df.rename(columns={
            'avg_summary_score': 'Average Summary Score',
            'avg_tag_score': 'Average Tag Score',
            'total_evaluations': 'Total Evaluations'
        })
        st.dataframe(stats_df)

        # Calculate combined averages
        all_summary_scores = []
        all_tag_scores = []
        for data in all_data.values():
            evaluated_entries = data['evaluated_entries']
            for entry in evaluated_entries:
                for eval in entry['Evaluations']:
                    all_summary_scores.append(eval.get('Summary Score', 0))
                    all_tag_scores.append(eval.get('Tag Score', 0))

        combined_avg_summary_score = np.mean(all_summary_scores) if all_summary_scores else 0
        combined_avg_tag_score = np.mean(all_tag_scores) if all_tag_scores else 0

        # Aggregate score (average of summary and tag scores)
        combined_aggregate_score = np.mean([
            (s + t) / 2 for s, t in zip(all_summary_scores, all_tag_scores)
        ]) if all_summary_scores and all_tag_scores else 0

        st.subheader("Combined Averages Across All Institutions")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Combined Average Summary Score", f"{combined_avg_summary_score:.2f}")
        with col2:
            st.metric("Combined Average Tag Score", f"{combined_avg_tag_score:.2f}")
        with col3:
            st.metric("Combined Aggregate Score", f"{combined_aggregate_score:.2f}")

        # Navigation to individual entries
        st.subheader("View Individual Entry Evaluations")
        # Collect all evaluated entries
        all_evaluated_entries = []
        for institution, data in all_data.items():
            for entry in data['evaluated_entries']:
                entry_copy = entry.copy()
                entry_copy['Institution'] = institution
                all_evaluated_entries.append(entry_copy)

        # Create a list of event numbers with institution names
        event_options = [
            f"{entry['Event Number']} ({entry['Institution']})"
            for entry in all_evaluated_entries
        ]

        selected_event = st.selectbox("Select Entry", options=event_options)

        # Find the selected entry
        selected_entry = next(
            (entry for entry in all_evaluated_entries if
             f"{entry['Event Number']} ({entry['Institution']})" == selected_event),
            None
        )

        if selected_entry:
            self.display_entry_evaluations(selected_entry)
        else:
            st.write("Entry not found.")

        # Summary at the bottom
        st.markdown(f"**Total Evaluations Across All Institutions:** {len(all_summary_scores)}")
        st.markdown(f"**Total Entries in Database:** {total_entries}")

    def display_entry_evaluations(self, entry):
        st.markdown(f"### Event Number: {entry['Event Number']} ({entry['Institution']})")
        st.write(f"**Succinct Summary:** {entry.get('Succinct Summary', 'N/A')}")
        st.write(f"**Assigned Tags:** {entry.get('Assigned Tags', 'N/A')}")

        evaluations = entry.get('Evaluations', [])
        if not evaluations:
            st.write("No evaluations available for this entry.")
            return

        st.markdown("#### Evaluations")
        for idx, eval in enumerate(evaluations, start=1):
            with st.expander(f"Evaluation {idx} by {eval.get('Evaluator', 'Unknown')}"):
                summary_score = eval.get('Summary Score', 'N/A')
                tag_score = eval.get('Tag Score', 'N/A')
                feedback = eval.get('Feedback', 'No feedback provided.')
                st.write(f"**Summary Score:** {summary_score}")
                st.write(f"**Tag Score:** {tag_score}")
                st.write(f"**Feedback:** {feedback}")

        # Highlight outliers if needed
        # Example: Display evaluations with low scores
        low_score_threshold = 2  # Define threshold for low scores
        low_score_evals = [
            eval for eval in evaluations if
            eval.get('Summary Score', 0) <= low_score_threshold or
            eval.get('Tag Score', 0) <= low_score_threshold
        ]
        if low_score_evals:
            st.warning("Low score evaluations detected:")
            for eval in low_score_evals:
                st.write(f"- Evaluator: {eval.get('Evaluator', 'Unknown')}, "
                         f"Summary Score: {eval.get('Summary Score', 'N/A')}, "
                         f"Tag Score: {eval.get('Tag Score', 'N/A')}")

