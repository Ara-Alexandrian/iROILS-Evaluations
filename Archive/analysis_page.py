# analysis_page.py

import streamlit as st
from institution_manager import InstitutionManager
from redis_manager import RedisManager
from network_resolver import NetworkResolver
import configparser

class AnalysisPage:
    def __init__(self, institution_manager, redis_manager):
        self.institution_manager = institution_manager
        self.redis_manager = redis_manager

    def show(self):
        st.header("Analysis Mode")

        # List of institutions
        institutions = ["UAB", "MBPCC"]

        # Check if there are any evaluations
        total_entries = 0
        total_evaluations = 0
        institution_stats_list = []

        for institution in institutions:
            # Get institution data
            entries, _ = self.institution_manager.get_institution_data(institution)
            total_entries += len(entries)

            # Retrieve stats from Redis
            stats_key = f"{institution}_stats"
            stats = self.redis_manager.redis_client.hgetall(stats_key)

            if stats:
                cumulative_summary = float(stats.get('cumulative_summary', 0))
                cumulative_tag = float(stats.get('cumulative_tag', 0))
                total_evals = int(stats.get('total_evaluations', 0))

                if total_evals > 0:
                    avg_summary = cumulative_summary / total_evals
                    avg_tag = cumulative_tag / total_evals
                else:
                    avg_summary = 0.0
                    avg_tag = 0.0

                total_evaluations += total_evals

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

        if total_evaluations == 0:
            st.write("No evaluations have been submitted yet.")
            st.markdown(f"**Total Entries in Database:** {total_entries}")
            return

        # Display institution-wise averages
        st.subheader("Institution Averages")

        # Display the statistics
        for stats in institution_stats_list:
            st.write(f"**{stats['Institution']}**")
            st.write(f"- Average Summary Score: {stats['Average Summary Score']}")
            st.write(f"- Average Tag Score: {stats['Average Tag Score']}")
            st.write(f"- Total Evaluations: {stats['Total Evaluations']}")

        # Calculate combined averages
        total_cumulative_summary = sum(
            float(self.redis_manager.redis_client.hget(f"{inst}_stats", 'cumulative_summary') or 0)
            for inst in institutions
        )
        total_cumulative_tag = sum(
            float(self.redis_manager.redis_client.hget(f"{inst}_stats", 'cumulative_tag') or 0)
            for inst in institutions
        )

        if total_evaluations > 0:
            combined_avg_summary_score = total_cumulative_summary / total_evaluations
            combined_avg_tag_score = total_cumulative_tag / total_evaluations
            combined_aggregate_score = (combined_avg_summary_score + combined_avg_tag_score) / 2
        else:
            combined_avg_summary_score = 0.0
            combined_avg_tag_score = 0.0
            combined_aggregate_score = 0.0

        st.subheader("Combined Averages Across All Institutions")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Combined Average Summary Score", f"{combined_avg_summary_score:.2f}")
        with col2:
            st.metric("Combined Average Tag Score", f"{combined_avg_tag_score:.2f}")
        with col3:
            st.metric("Combined Aggregate Score", f"{combined_aggregate_score:.2f}")

        # Summary at the bottom
        st.markdown(f"**Total Evaluations Across All Institutions:** {total_evaluations}")
        st.markdown(f"**Total Entries in Database:** {total_entries}")

