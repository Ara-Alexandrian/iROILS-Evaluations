import streamlit as st
import pandas as pd
import redis
import json

# Initialize Redis connection
r = redis.StrictRedis(host='192.168.1.4', port=6379, db=0, decode_responses=True)

# Initialize session state variables if not already set
if 'mode' not in st.session_state:
    st.session_state.mode = 'selection'
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'selected_entries' not in st.session_state:
    st.session_state.selected_entries = []
if 'evaluation_scores' not in st.session_state:
    st.session_state.evaluation_scores = {}
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = {}  # To track the checkbox state for each entry

# Admin login
st.title("Admin Dashboard")
admin_username = st.text_input("Username")
admin_password = st.text_input("Password", type="password")

# Replace this check with a proper authentication system
if admin_username == "admin" and admin_password == "admin_password":
    st.success("Logged in as Admin")

    # Upload .xlsx file
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)
        total_entries = len(df)

        # Mode selection
        mode = st.selectbox("Select Mode", ["Selection Mode", "Overview Mode"])

        # Selection Mode
        if mode == "Selection Mode":
            st.session_state.mode = "selection"

            # Navigation buttons for previous and next
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous Entry"):
                    if st.session_state.current_index > 0:
                        st.session_state.current_index -= 1
            with col3:
                if st.button("Next Entry"):
                    if st.session_state.current_index < total_entries - 1:
                        st.session_state.current_index += 1

            # Directly update the dropdown based on the current index after navigation
            entry_jump = st.selectbox(
                "Jump to Entry", [f"Entry {i+1}: Event Number {df.iloc[i]['Event Number']}" for i in range(total_entries)],
                index=st.session_state.current_index
            )

            # Correctly update the index when using the dropdown
            entry_index = int(entry_jump.split(" ")[1].replace(":", "")) - 1
            st.session_state.current_index = entry_index

            # Get the current entry based on the index
            current_entry = df.iloc[st.session_state.current_index]

            # Display current entry details
            st.write(f"### Event Number: {current_entry['Event Number']}")
            st.write(f"**Narrative:** {current_entry['Narrative']}")
            st.write(f"**Cleaned Narrative:** {current_entry['Cleaned Narrative']}")
            st.write(f"**Assigned Tags:** {current_entry['Assigned Tags']}")
            st.write(f"**Evaluation:** {current_entry['Evaluation']}")
            st.write(f"**Succinct Summary:** {current_entry['Succinct Summary']}")
            st.write(f"**Tags:** {current_entry['Tags']}")

            # Placeholder for evaluation score (to be filled in future by users)
            if current_entry['Event Number'] in st.session_state.evaluation_scores:
                score = st.session_state.evaluation_scores[current_entry['Event Number']]
                st.write(f"**Evaluation Score:** {score}/5")
            else:
                st.write(f"**Evaluation Score:** Not yet evaluated")

            # Ensure checkbox state is correctly managed for each entry
            entry_event_num = current_entry['Event Number']
            
            # Initialize the checkbox state if it hasn't been set yet
            if entry_event_num not in st.session_state.selected_state:
                st.session_state.selected_state[entry_event_num] = False

            # Get the state of the checkbox for the current entry
            include_for_evaluation = st.session_state.selected_state[entry_event_num]

            # Render the checkbox for the current entry
            new_state = st.checkbox("Select this entry for evaluation", value=include_for_evaluation)

            # If the state of the checkbox has changed, update it
            if new_state != include_for_evaluation:
                st.session_state.selected_state[entry_event_num] = new_state

            # Add or remove the entry from the selected list based on checkbox state
            if new_state and current_entry.to_dict() not in st.session_state.selected_entries:
                st.session_state.selected_entries.append(current_entry.to_dict())
            elif not new_state:
                st.session_state.selected_entries = [
                    entry for entry in st.session_state.selected_entries if entry['Event Number'] != entry_event_num
                ]

        # Overview Mode
        elif mode == "Overview Mode":
            st.session_state.mode = "overview"

            # Running list of selected entries
            st.write("### Selected Entries:")
            if st.session_state.selected_entries:
                for entry in st.session_state.selected_entries:
                    event_num = entry['Event Number']
                    st.write(f"- Event Number: {event_num}")
                    if event_num in st.session_state.evaluation_scores:
                        score = st.session_state.evaluation_scores[event_num]
                        st.write(f"**Evaluation Score:** {score}/5")
                    else:
                        st.write("**Evaluation Score:** Not yet evaluated")
            else:
                st.write("No entries selected.")

            # Running total
            st.write(f"**Total Selected:** {len(st.session_state.selected_entries)} / {total_entries}")

        # Button to submit the selected entries
        if st.button("Submit Selected Entries for Evaluation"):
            # Store selected entries in Redis
            r.set('evaluation_entries', json.dumps(st.session_state.selected_entries))
            st.success(f"{len(st.session_state.selected_entries)} entries have been submitted for evaluation.")

else:
    st.warning("Invalid login credentials")
