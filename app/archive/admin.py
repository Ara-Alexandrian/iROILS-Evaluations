import streamlit as st
import pandas as pd
import redis
import json
import configparser
from network_resolver import NetworkResolver
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# Load the .ini configuration file
config = configparser.ConfigParser()
config.read('config.ini')  # Ensure the correct path to your config file is used

# Initialize the NetworkResolver with the loaded config
resolver = NetworkResolver(config)

# Try to resolve the correct Redis host
try:
    redis_host = resolver.resolve_host()  # Resolve only Redis host
    logging.info(f"Resolved Redis host: {redis_host}")
except Exception as e:
    st.error(f"Failed to resolve network settings: {e}")
    st.stop()

# Get Redis port from config (use default 6379 if not provided)
redis_port = config['Redis'].get('redis_port', 6379)

# Connect to Redis using the resolved host and port
try:
    r = redis.StrictRedis(host=redis_host, port=int(redis_port), db=0, decode_responses=True)
    logging.info(f"Connected to Redis at {redis_host}:{redis_port}")
except Exception as e:
    st.error(f"Failed to connect to Redis: {e}")
    st.stop()

# Initialize session state variables if not already set
if 'mode' not in st.session_state:
    st.session_state.mode = 'overview'  # Start with Overview Mode
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'selected_entries' not in st.session_state:
    # Load selected entries from Redis when the app is reloaded
    try:
        selected_entries_json = r.get('evaluation_entries')
        st.session_state.selected_entries = json.loads(selected_entries_json) if selected_entries_json else []
    except Exception as e:
        st.error(f"Error loading selected entries from Redis: {e}")
        st.session_state.selected_entries = []
if 'evaluation_scores' not in st.session_state:
    st.session_state.evaluation_scores = {}

# Admin login
st.title("Admin Dashboard")
admin_username = st.text_input("Username")
admin_password = st.text_input("Password", type="password")

# Replace this check with a proper authentication system
if admin_username == "admin" and admin_password == "admin_password":
    st.success("Logged in as Admin")

    # Divider before select mode
    st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

    # Upload .xlsx file
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)
        total_entries = len(df)

        # Mode selection (start with Overview Mode by default)
        mode = st.selectbox("Select Mode", ["Overview Mode", "Selection Mode"], index=0)

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

            # Correctly update the dropdown based on the current index after navigation
            entry_jump = st.selectbox(
                "Jump to Entry", [f"Entry {i+1}: Event Number {df.iloc[i]['Event Number']}" for i in range(total_entries)],
                index=st.session_state.current_index
            )

            # Update the index when using the dropdown
            entry_index = int(entry_jump.split(" ")[1].replace(":", "")) - 1
            st.session_state.current_index = entry_index

            # Get the current entry based on the index
            current_entry = df.iloc[st.session_state.current_index]
            entry_event_num = str(current_entry['Event Number'])

            # Display current entry details
            st.write(f"### Event Number: {current_entry['Event Number']}")
            st.write(f"**Narrative:** {current_entry['Narrative']}")
            st.write(f"**Cleaned Narrative:** {current_entry['Cleaned Narrative']}")
            st.write(f"**Assigned Tags:** {current_entry['Assigned Tags']}")
            st.write(f"**Evaluation:** {current_entry['Evaluation']}")
            st.write(f"**Succinct Summary:** {current_entry['Succinct Summary']}")
            st.write(f"**Tags:** {current_entry['Tags']}")

            # Placeholder for evaluation score (to be filled in future by users)
            if entry_event_num in st.session_state.evaluation_scores:
                score = st.session_state.evaluation_scores[entry_event_num]
                st.write(f"**Evaluation Score:** {score}/5")
            else:
                st.write(f"**Evaluation Score:** Not yet evaluated")

            # Retrieve the selection status from Redis on entry load
            selection_status = r.get(f"entry:{entry_event_num}:selected")
            if selection_status is None:
                selection_status = "Do Not Select"

            # Create radio button for selection based on Redis value
            selection = st.radio(
                "Select this entry for evaluation", 
                options=["Do Not Select", "Select for Evaluation"],
                index=0 if selection_status == "Do Not Select" else 1,
                key=f"radio_{entry_event_num}"  # Unique key to avoid conflicts
            )

            # Update Redis based on the radio button interaction
            if selection == "Select for Evaluation":
                r.set(f"entry:{entry_event_num}:selected", "Select for Evaluation")
                if current_entry.to_dict() not in st.session_state.selected_entries:
                    st.session_state.selected_entries.append(current_entry.to_dict())
            else:
                r.set(f"entry:{entry_event_num}:selected", "Do Not Select")
                st.session_state.selected_entries = [
                    entry for entry in st.session_state.selected_entries if entry['Event Number'] != entry_event_num
                ]

        # Overview Mode
        elif mode == "Overview Mode":
            st.session_state.mode = "overview"

            # Divider before the card
            st.markdown("<hr style='border: 1px solid #6272A4;'>", unsafe_allow_html=True)

            # Dropdown to jump between selected entries
            selected_event_numbers = [entry['Event Number'] for entry in st.session_state.selected_entries]
            if selected_event_numbers:
                selected_entry_jump = st.selectbox(
                    "Jump to Selected Entry",
                    [f"Event Number {num}" for num in selected_event_numbers],
                    index=0 if 'selected_entry_index' not in st.session_state else st.session_state.selected_entry_index
                )

                selected_event_num = int(selected_entry_jump.split(" ")[-1])
                st.session_state.selected_entry_index = selected_event_numbers.index(selected_event_num)

                selected_entry = next(
                    (entry for entry in st.session_state.selected_entries if entry['Event Number'] == selected_event_num), None
                )

                # Display the selected entry in a central card with Dracula theme
                if selected_entry:
                    st.markdown(f"""
                    <div style='border: 1px solid #6272A4; background-color: #282A36; color: #F8F8F2; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);'>
                        <b>Event Number: {selected_entry['Event Number']}</b><br>
                        <span style='font-size: 14px; color: #b48ead;'>Evaluation Score: 
                        <b>{st.session_state.evaluation_scores.get(selected_event_num, 'Not yet evaluated')}</b></span><br><br>
                        <span style='font-size: 14px;'>Succinct Summary: {selected_entry.get('Succinct Summary', 'N/A')}</span><br><br>
                        <span style='font-size: 14px;'>{''.join([f'<b>Tag {i+1}:</b> {tag.strip()}<br>' for i, tag in enumerate(selected_entry.get('Tags', '').split(','))])}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write("No selected entries available.")

            # Divider before the summary
            st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)


        # Button to submit the selected entries
        if st.button("Submit Selected Entries for Evaluation"):
            # Store selected entries in Redis
            r.set('evaluation_entries', json.dumps(st.session_state.selected_entries))
            st.success(f"{len(st.session_state.selected_entries)} entries have been submitted for evaluation.")

else:
    st.warning("Invalid login credentials")
