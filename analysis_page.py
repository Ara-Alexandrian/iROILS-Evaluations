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
            # Fetch entries and stats
            entries = self.db_manager.get_selected_entries(institution)
            total_entries += len(entries)

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

        # Add Search/Jump to Specific Entry
        st.subheader("Search for Specific Entry by Event Number")
        event_number_search = st.text_input("Enter Event Number to Search")

        if st.button("Search Entry"):
            entry_found = None
            for institution in institutions:
                entries = self.db_manager.get_selected_entries(institution)
                entry_found = next((entry for entry in entries if entry.get('Event Number') == event_number_search), None)
                if entry_found:
                    break

            if entry_found:
                st.write(f"Entry Found: Event Number {entry_found.get('Event Number')}")
                evaluations = entry_found.get('Evaluations', [])
                if evaluations:
                    st.write("### Evaluations for this Entry")
                    for evaluation in evaluations:
                        st.write(f"Evaluator: {evaluation['Evaluator']}")
                        st.write(f"Summary Score: {evaluation['Summary Score']}")
                        st.write(f"Tag Score: {evaluation['Tag Score']}")
                        st.write(f"Feedback: {evaluation['Feedback']}")
                        st.markdown("---")
                else:
                    st.write("No evaluations found for this entry.")
            else:
                st.write("Entry not found.")

        # Filter Evaluations by Evaluator
        st.subheader("Filter Evaluations by Evaluator")
        evaluators = ["Evaluator1", "Evaluator2", "Evaluator3"]  # Add evaluators or fetch from a relevant source
        selected_evaluator = st.selectbox("Select Evaluator", evaluators)

        if selected_evaluator:
            st.write(f"Evaluations by {selected_evaluator}")
            for institution in institutions:
                entries = self.db_manager.get_selected_entries(institution)
                for entry in entries:
                    evaluations = entry.get('Evaluations', [])
                    for evaluation in evaluations:
                        if evaluation['Evaluator'] == selected_evaluator:
                            st.write(f"### Entry: {entry.get('Event Number')}")
                            st.write(f"Summary Score: {evaluation['Summary Score']}")
                            st.write(f"Tag Score: {evaluation['Tag Score']}")
                            st.write(f"Feedback: {evaluation['Feedback']}")
                            st.markdown("---")
