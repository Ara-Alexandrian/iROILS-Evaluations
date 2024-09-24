# Search/filter functionality
search_query = st.text_input("Search by Event Number or Status")

# Scrollable list of selected entries with a fixed height
st.write("### Selected Entries:")
container_style = "max-height: 400px; overflow-y: scroll; padding-right: 10px;"
st.markdown(f"<div style='{container_style}'>", unsafe_allow_html=True)

filtered_entries = [entry for entry in st.session_state.selected_entries if 
                    search_query.lower() in str(entry['Event Number']).lower() or
                    (search_query.lower() in "not yet evaluated" and entry['Event Number'] not in st.session_state.evaluation_scores) or
                    (entry['Event Number'] in st.session_state.evaluation_scores and search_query.lower() in str(st.session_state.evaluation_scores[entry['Event Number']]).lower())]

if filtered_entries:
    for entry in filtered_entries:
        event_num = entry['Event Number']

        # Create a card for each entry with evaluation score and event number
        st.markdown(f"""
        <div style='border: 1px solid #ddd; background-color: #fff; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);'>
            <b>Event Number: {event_num}</b><br>
            <span style='font-size: 14px;'>Evaluation Score: 
            <b>{st.session_state.evaluation_scores.get(event_num, '<span style="color: red;">Not yet evaluated</span>')}</b></span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("No entries found.")

st.markdown("</div>", unsafe_allow_html=True)
