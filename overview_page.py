import streamlit as st
import pandas as pd
import logging

class OverviewPage:
    def __init__(self, db_manager, institution):
        self.db_manager = db_manager
        self.institution = institution

    def show(self):
        st.header(f"Overview Mode - {self.institution}")

        # Use entries from session state
        entries = st.session_state.get('all_entries', [])
        total_entries = len(entries)

        if total_entries == 0:
            st.warning("No entries available.")
            return

        # Add search input and filter options
        self.render_search_and_filters(entries)

        # Get filtered entries
        filtered_entries = self.get_filtered_entries(entries)
        total_filtered_entries = len(filtered_entries)

        if total_filtered_entries == 0:
            st.warning("No entries match the search and filter criteria.")
            return

        # Allow the user to jump to a selected entry
        self.render_entry_navigation(filtered_entries, total_filtered_entries)

        # Handle data upload
        self.render_file_upload()

    def render_search_and_filters(self, entries):
        """Render search and filter options for overview."""
        st.markdown("### Search and Filter Selected Entries")

        # Search input
        st.text_input("Search by Narrative or Assigned Tags", key='overview_search_query')

        # Filter by Assigned Tags
        all_tags = {tag.strip() for entry in entries for tag in entry.get('Assigned Tags', '').split(',') if tag.strip()}
        st.multiselect("Filter by Assigned Tags", options=sorted(all_tags), key='overview_tag_filter')

    def get_filtered_entries(self, entries):
        """Filter entries based on search, tag criteria, and selection status."""
        search_query = st.session_state.get('overview_search_query', '').lower()
        tag_filter = st.session_state.get('overview_tag_filter', [])

        # Filter entries that are selected for evaluation
        filtered_entries = [
            entry for entry in entries
            if entry.get('Selected', 'Do Not Select') == 'Select for Evaluation'
        ]

        # Apply search filter
        if search_query:
            filtered_entries = [
                entry for entry in filtered_entries
                if search_query in entry.get('Narrative', '').lower() or
                search_query in entry.get('Assigned Tags', '').lower()
            ]

        # Apply tag filter
        if tag_filter:
            filtered_entries = [
                entry for entry in filtered_entries
                if any(tag.strip() in tag_filter for tag in entry.get('Assigned Tags', '').split(','))
            ]

        return filtered_entries

    def render_entry_navigation(self, filtered_entries, total_filtered_entries):
        """Render a dropdown to allow users to jump to a specific entry."""
        st.markdown("### Jump to Selected Entry")
        selected_event = st.selectbox("Select Event", [entry.get('Event Number', 'N/A') for entry in filtered_entries], key='overview_event_select')

        selected_entry = next((entry for entry in filtered_entries if entry.get('Event Number') == selected_event), None)
        
        if selected_entry:
            self.display_entry_details(selected_entry, total_filtered_entries)

    def display_entry_details(self, current_entry, total_filtered_entries):
        """Display the details of the current entry."""
        st.write(f"### Event Number: {current_entry.get('Event Number', 'N/A')}")
        st.write(f"**Narrative:** {current_entry.get('Narrative', '')}")
        st.write(f"**Assigned Tags:** {current_entry.get('Assigned Tags', '')}")
        st.write(f"**Succinct Summary:** {current_entry.get('Succinct Summary', '')}")

        # Summary
        st.markdown(f"**Total Selected Entries:** {total_filtered_entries}")
        st.markdown(f"**Total Entries in Database:** {len(st.session_state['all_entries'])}")

    def reset_session_state():
        """Reset session state variables."""
        st.session_state.pop('all_entries', None)
        st.session_state.pop('total_entries', None)
        st.session_state.pop('current_index', None)

    def reset_institution_data():
        selected_institution = st.session_state.get('institution_select', 'UAB')
        try:
            st.write(f"Resetting data for institution: {selected_institution}")
            db_manager.reset_data(selected_institution)  # Reset data in PostgreSQL

            # Ensure session state is cleared after resetting
            st.session_state.pop('all_entries', None)
            st.session_state.pop('total_entries', None)
            st.session_state.pop('current_eval_index', None)
            st.session_state.pop('evaluator_data', None)  # Add this to clear evaluated data
            st.success(f"All data for {selected_institution} has been reset.")

        except Exception as e:
            st.error(f"Error during reset: {e}")

        # Optionally trigger a refresh or rerun if needed
        st.rerun()



    def render_file_upload(self):
        """Handle the file upload process."""
        st.markdown("### Upload New Data")

        # Add a unique key to avoid duplicate file upload issues
        uploaded_file = st.file_uploader("Upload New Data", type="xlsx", key='file_upload_overview')

        if uploaded_file:
            try:
                # Read the uploaded file into a pandas DataFrame
                df = pd.read_excel(uploaded_file)

                # Replace NaN values with None (null in JSON)
                df = df.where(pd.notnull(df), None)

                # Remove 'Selected' column if it exists
                if 'Selected' in df.columns:
                    df.drop(columns=['Selected'], inplace=True)
                    st.write("Removed 'Selected' column from uploaded data.")

                # Convert the DataFrame to a list of dictionaries (entries)
                new_entries = df.to_dict(orient="records")

                # Ensure that 'Selected' is set to 'Do Not Select' by default
                for entry in new_entries:
                    entry['Selected'] = 'Do Not Select'

                # Save entries to the database (PostgreSQL)
                self.db_manager.save_selected_entries(self.institution, new_entries)

                # Reload the entries into session state
                all_entries = self.db_manager.get_selected_entries(self.institution)
                st.session_state['all_entries'] = all_entries
                st.session_state['total_entries'] = len(all_entries)

                st.success(f"New data for {self.institution} uploaded successfully!")
            except Exception as e:
                logging.error(f"Error processing uploaded file: {e}")
                st.error(f"Error processing uploaded file: {e}")
