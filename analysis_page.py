import streamlit as st

class AnalysisPage:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def show(self):
        st.header("Analysis Mode")

        # Institution Averages (existing code remains unchanged)
        st.subheader("Institution Averages")

        institutions = ["UAB", "MBPCC"]
        total_entries = 0
        total_evaluations = 0
        cumulative_summary_total = 0
        cumulative_tag_total = 0
        institution_stats_list = []

        # Calculate stats for each institution
        for institution in institutions:
            # Fetch only selected entries for this institution
            selected_entries = self.db_manager.get_selected_entries(institution)
            selected_entries = [entry for entry in selected_entries if entry.get('Selected') == 'Select for Evaluation']
            total_entries += len(selected_entries)

            stats = self.db_manager.get_institution_stats(institution)
            cumulative_summary = stats['cumulative_summary']
            cumulative_tag = stats['cumulative_tag']
            total_evals = stats['total_evaluations']

            # Compute averages
            avg_summary = cumulative_summary / total_evals if total_evals > 0 else 0.0
            avg_tag = cumulative_tag / total_evals if total_evals > 0 else 0.0

            total_evaluations += total_evals
            cumulative_summary_total += cumulative_summary
            cumulative_tag_total += cumulative_tag

            institution_stats_list.append({
                'Institution': institution,
                'Average Summary Score': round(avg_summary, 2),
                'Average Tag Score': round(avg_tag, 2),
                'Total Evaluations': total_evals
            })

        # Display stats for each institution
        for stats in institution_stats_list:
            st.write(f"**{stats['Institution']}**")
            st.write(f"- Average Summary Score: {stats['Average Summary Score']}")
            st.write(f"- Average Tag Score: {stats['Average Tag Score']}")
            st.write(f"- Total Evaluations: {stats['Total Evaluations']}")

        # Display combined averages across all institutions
        st.subheader("Combined Averages Across All Institutions")

        combined_avg_summary_score = cumulative_summary_total / total_evaluations if total_evaluations > 0 else 0.0
        combined_avg_tag_score = cumulative_tag_total / total_evaluations if total_evaluations > 0 else 0.0
        combined_aggregate_score = (combined_avg_summary_score + combined_avg_tag_score) / 2

        st.metric("Combined Average Summary Score", f"{combined_avg_summary_score:.2f}")
        st.metric("Combined Average Tag Score", f"{combined_avg_tag_score:.2f}")
        st.metric("Combined Aggregate Score", f"{combined_aggregate_score:.2f}")

        st.write(f"Total Evaluations Across All Institutions: {total_evaluations}")
        st.write(f"Total Entries in Database: {total_entries}")

        # Filter Evaluations by Evaluator
        st.subheader("Filter Evaluations by Evaluator")
        # Fetch evaluators from the database
        evaluators = self.db_manager.get_all_evaluators()
        selected_evaluator = st.selectbox("Select Evaluator", evaluators)

        if selected_evaluator:
            # Get selected entries evaluated by the evaluator
            evaluator_entries = []
            for institution in institutions:
                # Fetch only selected entries for this institution
                selected_entries = self.db_manager.get_selected_entries(institution)
                selected_entries = [entry for entry in selected_entries if entry.get('Selected') == 'Select for Evaluation']
                
                for entry in selected_entries:
                    evaluations = self.db_manager.get_evaluations_by_evaluator(selected_evaluator, entry.get('Event Number'))
                    
                    if evaluations:
                        # Evaluated entry
                        for evaluation in evaluations:
                            evaluator_entries.append({
                                'Event Number': entry.get('Event Number'),
                                'Evaluated': True,
                                'Summary Score': evaluation['summary_score'],
                                'Tag Score': evaluation['tag_score'],
                                'Feedback': evaluation['feedback'],
                                'Narrative': entry.get('Narrative', ''),
                                'Assigned Tags': entry.get('Assigned Tags', '')
                            })
                    else:
                        # Non-evaluated entry
                        evaluator_entries.append({
                            'Event Number': entry.get('Event Number'),
                            'Evaluated': False,
                            'Narrative': entry.get('Narrative', ''),
                            'Assigned Tags': entry.get('Assigned Tags', '')
                        })

            # Dropdown list for the entries with check marks or X's
            entry_display = [
                f"Entry {i+1} - {entry['Event Number']} {'✅' if entry['Evaluated'] else '❌'}"
                for i, entry in enumerate(evaluator_entries)
            ]

            selected_entry_display = st.selectbox("Select an Entry", entry_display)
            selected_entry_index = int(selected_entry_display.split()[1]) - 1  # Extract index from selected entry
            selected_entry = evaluator_entries[selected_entry_index]

            # Display selected entry details in a card
            st.subheader(f"Entry: {selected_entry['Event Number']}")

            # Display Narrative, Tags, Evaluation, and Feedback inside a card-like container
            st.markdown(
                """
                <div style="padding: 15px; background-color: #f9f9f9; border-radius: 8px;">
                """,
                unsafe_allow_html=True
            )
            st.write(f"**Narrative:** {selected_entry['Narrative']}")
            st.write(f"**Assigned Tags:** {selected_entry['Assigned Tags']}")

            if selected_entry['Evaluated']:
                st.write(f"**Summary Score:** {selected_entry['Summary Score']}")
                st.write(f"**Tag Score:** {selected_entry['Tag Score']}")
                st.write(f"**Feedback:** {selected_entry['Feedback']}")
            else:
                st.write("This entry has not been evaluated yet.")
            st.markdown("</div>", unsafe_allow_html=True)
