import streamlit as st
import redis
import json

# Initialize Redis connection
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# User login
st.title("User Dashboard")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if username and password:  # Add more robust auth later

    # Fetch entries from Redis
    entries = json.loads(r.get('evaluation_entries'))

    for i, entry in enumerate(entries):
        st.write(f"Entry {i + 1}")
        st.json(entry)  # Display the entry content

        # Evaluation form
        rating = st.slider(f"Rate the Summary and Tags for Entry {i + 1}", 1, 5, 3)
        feedback = st.text_area(f"Feedback for Entry {i + 1}", "")

        if st.button(f"Submit Evaluation for Entry {i + 1}"):
            # Store user submission in Redis (could be keyed by username)
            user_data = {'rating': rating, 'feedback': feedback}
            r.rpush(f'evaluations_{username}', json.dumps(user_data))
            st.success(f"Evaluation submitted for Entry {i + 1}.")

