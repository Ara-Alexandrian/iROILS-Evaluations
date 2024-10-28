# selection_page.py

import streamlit as st
import random

class SelectionPage:
    def __init__(self, db_manager, institution):
        self.db_manager = db_manager
        self.institution = institution

    def show(self):
        st.header(f"Selection Mode - {self.institution}")

        # Use entries from session state or fetch from the database
        entries = st.session_state.get('all_entries', [])
        if not entries:
            entries = self.db_manager.get_selected_entries(self.institution)
            st.session_state['all_entries'] = entries

        total_entries = len(entries)

        # Add search input and filter options
        self.render_search_and_filters(entries)

        # Update total entries after filtering
        filtered_entries = self.get_filtered_entries(entries)
        total_filtered_entries = len(filtered_entries)

        if total_filtered_entries == 0:
            st.warning("No entries match the search and filter criteria.")
            return

        # Select random entries button
        self.select_random_entries(filtered_entries)

        # Initialize and bound the current index for entry navigation
        self.initialize_current_index(total_filtered_entries)

        # Display navigation and current entry
        self.display_navigation(filtered_entries, total_filtered_entries)

        # Display current entry details
        current_entry = filtered_entries[st.session_state.current_index]
        self.display_entry_details(current_entry, total_filtered_entries)

    def render_search_and_filters(self, entries):
        """Render search and filter options for selecting entries."""
        st.markdown("### Search and Filter Entries")

        # Search input
        st.text_input("Search by Narrative or Assigned Tags", key='selection_search_query')

        # Filter by Selection Status and Tags
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox(
                "Filter by Selection Status",
                options=["All", "Selected", "Not Selected"],
                key='selection_filter'
            )
        with col2:
            all_tags = {tag.strip() for entry in entries for tag in entry.get('Assigned Tags', '').split(',') if tag.strip()}
            st.multiselect(
                "Filter by Assigned Tags",
                options=sorted(all_tags),
                key='tag_filter'
            )

    def get_filtered_entries(self, entries):
        """Filter entries based on search, selection, and tag criteria."""
        search_query = st.session_state.get('selection_search_query', '').lower()
        selection_filter = st.session_state.get('selection_filter', 'All')
        tag_filter = st.session_state.get('tag_filter', [])

        filtered_entries = entries

        # Apply search filter
        if search_query:
            filtered_entries = [
                entry for entry in filtered_entries
                if search_query in entry.get('Narrative', '').lower() or
                   search_query in entry.get('Assigned Tags', '').lower()
            ]

        # Apply selection filter
        if selection_filter != "All":
            status = 'Select for Evaluation' if selection_filter == "Selected" else 'Do Not Select'
            filtered_entries = [
                entry for entry in filtered_entries
                if entry.get('Selected', 'Do Not Select') == status
            ]

        # Apply tag filter
        if tag_filter:
            filtered_entries = [
                entry for entry in filtered_entries
                if any(tag.strip() in tag_filter for tag in entry.get('Assigned Tags', '').split(','))
            ]

        return filtered_entries

    def select_random_entries(self, filtered_entries):
        """Select 200 random entries from the filtered list."""
        if st.button("Select 200 Random Entries"):
            # Filter out unselected entries
            unselected_entries = [entry for entry in filtered_entries if entry.get('Selected', 'Do Not Select') == 'Do Not Select']
            num_to_select = min(200, len(unselected_entries))

            if num_to_select > 0:
                # Randomly select 200 entries from the unselected ones
                random_entries = random.sample(unselected_entries, num_to_select)
                for entry in random_entries:
                    entry['Selected'] = 'Select for Evaluation'

                # Batch update the selected entries in Redis and PostgreSQL
                self.db_manager.update_entries_batch(self.institution, random_entries)

                # Update session state
                for entry in random_entries:
                    for idx, e in enumerate(st.session_state['all_entries']):
                        if e['Event Number'] == entry['Event Number']:
                            st.session_state['all_entries'][idx]['Selected'] = 'Select for Evaluation'
                            break

                # Display a success message
                st.success(f"{num_to_select} random entries have been selected for evaluation.")
                st.rerun()  # Reload to reflect the changes
            else:
                st.warning("No unselected entries are available to select.")

    def initialize_current_index(self, total_filtered_entries):
        """Initialize and ensure current index is within bounds."""
        if 'current_index' not in st.session_state:
            st.session_state['current_index'] = 0

        # Ensure current_index is within bounds
        st.session_state['current_index'] = max(0, min(st.session_state['current_index'], total_filtered_entries - 1))

    def display_navigation(self, filtered_entries, total_filtered_entries):
        """Display entry navigation controls."""
        st.markdown("### Navigate Entries")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Previous Entry") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.rerun()
        with col3:
            if st.button("Next Entry") and st.session_state.current_index < total_filtered_entries - 1:
                st.session_state.current_index += 1
                st.rerun()
        with col2:
            st.session_state.current_index = st.slider(
                "Select Entry",
                min_value=1,
                max_value=total_filtered_entries,
                value=st.session_state.current_index + 1,
                format="Entry %d",
                key='entry_slider'
            ) - 1  # Adjust to 0-based index

        # Display progress bar
        st.progress((st.session_state.current_index + 1) / total_filtered_entries)

    def display_entry_details(self, current_entry, total_filtered_entries):
        """Display the details of the current entry."""
        entry_number_display = st.session_state.current_index + 1
        st.write(f"### Entry {entry_number_display} of {total_filtered_entries} - Event Number: {current_entry.get('Event Number', 'N/A')}")
        st.write(f"**Narrative:** {current_entry.get('Narrative', '')}")
        st.write(f"**Cleaned Narrative:** {current_entry.get('Cleaned Narrative', '')}")
        st.write(f"**Assigned Tags:** {current_entry.get('Assigned Tags', '')}")
        st.write(f"**Evaluation:** {current_entry.get('Evaluation', '')}")
        st.write(f"**Succinct Summary:** {current_entry.get('Succinct Summary', '')}")

        # Selection checkbox
        is_selected = current_entry.get('Selected', 'Do Not Select') == 'Select for Evaluation'
        selection = st.checkbox(
            "Select this entry for evaluation",
            value=is_selected,
            key=f"select_{current_entry.get('Event Number', st.session_state.current_index)}"
        )

        # Handle selection change
        if selection != is_selected:
            current_entry['Selected'] = 'Select for Evaluation' if selection else 'Do Not Select'
            self.update_entry_selection(current_entry)

        # Summary
        st.markdown(f"**Total Filtered Entries:** {total_filtered_entries}")
        st.markdown(f"**Total Entries in Database:** {len(st.session_state['all_entries'])}")

    def update_entry_selection(self, entry):
        """Update the selection status of an entry in both Redis and PostgreSQL."""
        self.db_manager.update_entry(self.institution, entry)

        # Update session state
        for idx, e in enumerate(st.session_state['all_entries']):
            if e['Event Number'] == entry['Event Number']:
                st.session_state['all_entries'][idx]['Selected'] = entry['Selected']
                break
