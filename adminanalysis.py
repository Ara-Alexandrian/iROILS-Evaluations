import streamlit as st
import redis
import json
import numpy as np

# Initialize Redis connection
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

st.title("Admin Dashboard - Statistics")

# Retrieve all evaluations
users = ["user1", "user2"]  # Example users, dynamically fetch if needed

all_evaluations = []

for user in users:
    user_evals = r.lrange(f'evaluations_{user}', 0, -1)  # Get all entries for user
    all_evaluations.extend([json.loads(e) for e in user_evals])

# Compute stats
if all_evaluations:
    ratings = [eval['rating'] for eval in all_evaluations]
    avg_rating = np.mean(ratings)
    st.write(f"Average Rating: {avg_rating:.2f}")
else:
    st.write("No evaluations available yet.")

