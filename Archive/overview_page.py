# overview_page.py

import streamlit as st

class OverviewPage:
    def __init__(self, institution_manager, institution):
        self.institution_manager = institution_manager
        self.institution = institution

    def show(self):
        st.header(f"Overview Mode - {self.institution}")

        # Use entries from session state
        all_entries = st.session_state.get('all_entries', [])
        total_entries = len(all_entries)

        # Get selected entries
        selected_entries = [
            entry for entry in all_entries if entry.get('Selected') == 'Select for Evaluation'
        ]
        total_selected = len(selected_entries)

        if total_selected == 0:
            st.write("No selected entries available.")
            st.markdown(f"**Total Selected Entries:** {total_selected}")
            st.markdown(f"**Total Entries in Database:** {total_entries}")
            return

        # Add search input and filter options
        st.markdown("### Search and Filter Selected Entries")

        # Search input
        search_query = st.text_input("Search by Narrative or Assigned Tags", key='overview_search_query')

        # Filter options
        all_tags = set()
        for entry in selected_entries:
            tags = entry.get('Assigned Tags', '').split(',')
            tags = [tag.strip() for tag in tags if tag.strip()]
            all_tags.update(tags)

        tag_filter = st.multiselect(
            "Filter by Assigned Tags",
            options=sorted(all_tags),
            key='overview_tag_filter'
        )

        # Filter selected entries based on search and filter criteria
        filtered_entries = selected_entries

        # Apply search filter
        if search_query:
            filtered_entries = [
                entry for entry in filtered_entries
                if search_query.lower() in entry.get('Narrative', '').lower() or
                   search_query.lower() in entry.get('Assigned Tags', '').lower()
            ]

        # Apply tag filter
        if tag_filter:
            filtered_entries = [
                entry for entry in filtered_entries
                if any(tag.strip() in tag_filter for tag in entry.get('Assigned Tags', '').split(','))
            ]

        # Update total entries after filtering
        total_filtered_entries = len(filtered_entries)

        if total_filtered_entries == 0:
            st.warning("No selected entries match the search and filter criteria.")
            st.markdown(f"**Total Selected Entries:** {total_selected}")
            st.markdown(f"**Total Entries in Database:** {total_entries}")
            st.markdown(f"**Number of Filtered Entries:** {total_filtered_entries}")
            return

        # Jump to Selected Entry
        st.markdown("### Jump to Selected Entry")
        selected_event_numbers = [entry['Event Number'] for entry in filtered_entries]
        selected_event_num = st.selectbox(
            "Select Event",
            selected_event_numbers,
            key='overview_event_num'
        )

        selected_entry = next(
            (entry for entry in filtered_entries if entry['Event Number'] == selected_event_num), None
        )

        # Display the selected entry
        if selected_entry:
            st.write(f"### Event Number: {selected_entry['Event Number']}")
            st.write(f"**Succinct Summary:** {selected_entry.get('Succinct Summary', 'N/A')}")
            st.write(f"**Tags:** {selected_entry.get('Assigned Tags', 'N/A')}")
        else:
            st.write("No selected entries available.")

        # Summary at the bottom
        st.markdown(f"**Total Selected Entries:** {total_selected}")
        st.markdown(f"**Number of Filtered Entries:** {total_filtered_entries}")
        st.markdown(f"**Total Entries in Database:** {total_entries}")


        # Slider to navigate filtered entries
        st.markdown("### Navigate Entries")
        index = st.slider(
            "Select Entry",
            min_value=0,
            max_value=total_filtered_entries - 1,
            value=0,
            format="Entry %d",
            key='overview_entry_slider'
        )

        selected_entry = filtered_entries[index]

        # Display progress bar or visual indicator
        progress = (index + 1) / total_filtered_entries
        st.progress(progress)

        # Display the selected entry
        st.write(f"### Event Number: {selected_entry['Event Number']}")
        st.write(f"**Succinct Summary:** {selected_entry.get('Succinct Summary', 'N/A')}")
        st.write(f"**Tags:** {selected_entry.get('Assigned Tags', 'N/A')}")

        # Summary at the bottom
        st.markdown(f"**Total Selected Entries:** {total_selected}")
        st.markdown(f"**Number of Filtered Entries:** {total_filtered_entries}")
        st.markdown(f"**Total Entries in Database:** {total_entries}")
