import streamlit as st

class OverviewPage:
    def __init__(self, institution_manager, institution):
        self.institution_manager = institution_manager
        self.institution = institution

    def show(self):
        st.header(f"Overview Mode - {self.institution}")

        # Load data for the selected institution
        selected_entries, evaluation_scores = self.institution_manager.get_institution_data(self.institution)
        total_entries = len(selected_entries)

        # Filter by tags or jump to specific entries
        st.markdown("### Jump to Selected Entry")
        selected_event_numbers = [entry['Event Number'] for entry in selected_entries]
        selected_event_num = st.selectbox("Select Event", selected_event_numbers)

        selected_entry = next(
            (entry for entry in selected_entries if entry['Event Number'] == selected_event_num), None
        )

        # Display the selected entry
        if selected_entry:
            st.write(f"### Event Number: {selected_entry['Event Number']}")
            st.write(f"**Evaluation Score:** {evaluation_scores.get(selected_entry['Event Number'], 'Not yet evaluated')}")
            st.write(f"**Succinct Summary:** {selected_entry['Succinct Summary']}")
            st.write(f"**Tags:** {selected_entry['Assigned Tags']}")
        else:
            st.write("No selected entries available.")

        # Summary at the bottom
        st.markdown(f"**Total Selected Entries:** {len(selected_entries)} / {total_entries}")
        st.markdown(f"**Average Evaluation Score:** {(sum(evaluation_scores.values()) / len(evaluation_scores)) if evaluation_scores else 'N/A'}")

