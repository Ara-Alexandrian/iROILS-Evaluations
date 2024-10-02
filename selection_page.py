# selection_page.py

import streamlit as st

class SelectionPage:
    def __init__(self, institution_manager, institution):
        self.institution_manager = institution_manager
        self.institution = institution

    def show(self):
        st.header(f"Selection Mode - {self.institution}")

        # Use entries from session state
        entries = st.session_state.get('all_entries', [])
        total_entries = len(entries)

        # Add search input and filter options
        st.markdown("### Search and Filter Entries")

        # Search input
        search_query = st.text_input("Search by Narrative or Assigned Tags", key='selection_search_query')

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            selection_filter = st.selectbox(
                "Filter by Selection Status",
                options=["All", "Selected", "Not Selected"],
                key='selection_filter'
            )
        with col2:
            # Filter by Assigned Tag
            all_tags = set()
            for entry in entries:
                tags = entry.get('Assigned Tags', '').split(',')
                tags = [tag.strip() for tag in tags if tag.strip()]
                all_tags.update(tags)
            tag_filter = st.multiselect(
                "Filter by Assigned Tags",
                options=sorted(all_tags),
                key='tag_filter'
            )

        # Filter entries based on search and filter criteria
        filtered_entries = entries

        # Apply search filter
        if search_query:
            filtered_entries = [
                entry for entry in filtered_entries
                if search_query.lower() in entry.get('Narrative', '').lower() or
                   search_query.lower() in entry.get('Assigned Tags', '').lower()
            ]

        # Apply selection status filter
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

        # Update total entries after filtering
        total_filtered_entries = len(filtered_entries)

        # Handle case where no entries match the filters
        if total_filtered_entries == 0:
            st.warning("No entries match the search and filter criteria.")
            return

        # Initialize current index if not set
        if 'current_index' not in st.session_state:
            st.session_state['current_index'] = 0

        # Ensure current_index is within bounds
        if st.session_state.current_index >= total_filtered_entries:
            st.session_state.current_index = total_filtered_entries - 1
        if st.session_state.current_index < 0:
            st.session_state.current_index = 0

        # Navigation
        st.markdown("### Navigate Entries")

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Previous Entry") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
        with col2:
            # Slider to navigate entries
            st.session_state.current_index = st.slider(
                "Select Entry",
                min_value=0,
                max_value=total_filtered_entries - 1,
                value=st.session_state.current_index,
                format="Entry %d",
                key='entry_slider'
            )
        with col3:
            if st.button("Next Entry") and st.session_state.current_index < total_filtered_entries - 1:
                st.session_state.current_index += 1

        # Display progress bar or visual indicator
        progress = (st.session_state.current_index + 1) / total_filtered_entries
        st.progress(progress)

        current_entry = filtered_entries[st.session_state.current_index]

        # Display the current entry
        st.write(f"### Event Number: {current_entry.get('Event Number', 'N/A')}")
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

        # Update selection status if changed
        if selection != is_selected:
            selection_status = 'Select for Evaluation' if selection else 'Do Not Select'
            current_entry['Selected'] = selection_status

            # Update entry in Redis
            self.institution_manager.update_entry(self.institution, current_entry)

            # Update session state
            for idx, entry in enumerate(st.session_state['all_entries']):
                if entry['Event Number'] == current_entry['Event Number']:
                    st.session_state['all_entries'][idx]['Selected'] = selection_status
                    break

            st.success(f"Entry {current_entry.get('Event Number', 'N/A')} updated.")

        # Summary at the bottom
        st.markdown(f"**Total Filtered Entries:** {total_filtered_entries}")
        st.markdown(f"**Total Entries in Database:** {total_entries}")
