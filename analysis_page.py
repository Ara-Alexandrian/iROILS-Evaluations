import streamlit as st

class AnalysisPage:
    def __init__(self, institution_manager, redis_manager, login_manager):
        self.institution_manager = institution_manager
        self.redis_manager = redis_manager
        self.login_manager = login_manager

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

        for institution in institutions:
            # Fetching data from Redis
            entries = self.institution_manager.get_all_entries(institution)
            total_entries += len(entries)

            # Redis stats retrieval
            stats_key = f"{institution}_stats"
            stats = self.redis_manager.redis_client.hgetall(stats_key)

            if stats:
                cumulative_summary = float(stats.get('cumulative_summary', 0))
                cumulative_tag = float(stats.get('cumulative_tag', 0))
                total_evals = int(stats.get('total_evaluations', 0))

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
            else:
                institution_stats_list.append({
                    'Institution': institution,
                    'Average Summary Score': 0.0,
                    'Average Tag Score': 0.0,
                    'Total Evaluations': 0
                })

        # Display the institution stats
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
                entries = self.institution_manager.get_all_entries(institution)
                for entry in entries:
                    if entry.get('Event Number') == event_number_search:
                        entry_found = entry
                        break

            if entry_found:
                st.write(f"Entry Found: Event Number {entry_found.get('Event Number')}")
                if 'Evaluations' in entry_found:
                    st.write("### Evaluations for this Entry")
                    for evaluation in entry_found['Evaluations']:
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
        evaluators = sorted(self.login_manager.evaluator_credentials.keys())
        selected_evaluator = st.selectbox("Select Evaluator", evaluators)

        if selected_evaluator:
            st.write(f"Evaluations by {selected_evaluator}")
            for institution in institutions:
                entries = self.institution_manager.get_all_entries(institution)
                for entry in entries:
                    if 'Evaluations' in entry:
                        for evaluation in entry['Evaluations']:
                            if evaluation['Evaluator'] == selected_evaluator:
                                st.write(f"### Entry: {entry.get('Event Number')}")
                                st.write(f"Summary Score: {evaluation['Summary Score']}")
                                st.write(f"Tag Score: {evaluation['Tag Score']}")
                                st.write(f"Feedback: {evaluation['Feedback']}")
                                st.markdown("---")
