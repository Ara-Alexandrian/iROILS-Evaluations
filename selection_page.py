import streamlit as st

class SelectionPage:
    def __init__(self, institution_manager, institution):
        self.institution_manager = institution_manager
        self.institution = institution

    def show(self):
        st.header(f"Selection Mode - {self.institution}")

        # Load data for the selected institution
        selected_entries, evaluation_scores = self.institution_manager.get_institution_data(self.institution)
        total_entries = len(selected_entries)

        # Navigation buttons for navigating entries
        col1, col2 = st.columns([1, 1])
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0

        with col1:
            if st.button("Previous Entry"):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1

        with col2:
            if st.button("Next Entry"):
                if st.session_state.current_index < total_entries - 1:
                    st.session_state.current_index += 1

        current_entry = selected_entries[st.session_state.current_index]

        # Display the selected entry
        st.write(f"### Event Number: {current_entry['Event Number']}")
        st.write(f"**Narrative:** {current_entry['Narrative']}")
        st.write(f"**Cleaned Narrative:** {current_entry['Cleaned Narrative']}")
        st.write(f"**Assigned Tags:** {current_entry['Assigned Tags']}")
        st.write(f"**Evaluation:** {current_entry['Evaluation']}")
        st.write(f"**Succinct Summary:** {current_entry['Succinct Summary']}")

        # Option to mark the entry as "selected for evaluation"
        selection = st.radio(
            "Select this entry for evaluation",
            options=["Do Not Select", "Select for Evaluation"],
            index=0 if current_entry['Selected'] == "Do Not Select" else 1,
            key=f"radio_{current_entry['Event Number']}"
        )

        # Save selection back to the institution manager (or Redis)
        self.institution_manager.update_selection(self.institution, current_entry['Event Number'], selection)

        # Summary at the bottom
        st.markdown(f"**Total Entries:** {total_entries}")

