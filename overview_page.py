import streamlit as st

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

    def render_search_and_filters(self, entries):
        """Render search and filter options for overview."""
        st.markdown("### Search and Filter Selected Entries")

        # Search input
        st.text_input("Search by Narrative or Assigned Tags", key='overview_search_query')

        # Filter by Assigned Tags
        all_tags = {tag.strip() for entry in entries for tag in entry.get('Assigned Tags', '').split(',') if tag.strip()}
        st.multiselect("Filter by Assigned Tags", options=sorted(all_tags), key='overview_tag_filter')

    def get_filtered_entries(self, entries):
        """Filter entries based on search and tag criteria."""
        search_query = st.session_state.get('overview_search_query', '').lower()
        tag_filter = st.session_state.get('overview_tag_filter', [])

        filtered_entries = entries

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
