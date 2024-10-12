import streamlit as st
import pandas as pd
import psycopg2
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# PostgreSQL connection settings
psql_host = config['postgresql']['psql_home']
psql_port = config['postgresql'].getint('psql_port', 5432)
psql_user = config['postgresql']['psql_user']
psql_password = config['postgresql']['psql_password']
psql_dbname = config['postgresql']['psql_dbname']

# Establish PostgreSQL connection
@st.cache_data
def load_data(query, params=None):
    try:
        conn = psycopg2.connect(
            host=psql_host,
            port=psql_port,
            user=psql_user,
            password=psql_password,
            dbname=psql_dbname
        )
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data from PostgreSQL: {e}")
        return pd.DataFrame()

# Main Dashboard - Show Running Averages
st.title("PostgreSQL Evaluation Dashboard")

st.header("Overall Statistics")
query_averages = """
SELECT 
    AVG(summary_score) as avg_summary, 
    AVG(tag_score) as avg_tag, 
    COUNT(*) as total_evaluations
FROM evaluations;
"""
average_data = load_data(query_averages)

if not average_data.empty:
    avg_summary = average_data['avg_summary'][0]
    avg_tag = average_data['avg_tag'][0]
    total_evaluations = average_data['total_evaluations'][0]

    st.metric("Average Summary Score", f"{avg_summary:.2f}")
    st.metric("Average Tag Score", f"{avg_tag:.2f}")
    st.metric("Total Evaluations", total_evaluations)
else:
    st.write("No data available to display statistics.")

# Evaluator Selection and List of Entries
st.header("Evaluator Data")
evaluator_query = """
SELECT DISTINCT evaluator FROM evaluations ORDER BY evaluator;
"""
evaluators = load_data(evaluator_query)['evaluator'].tolist()

selected_evaluator = st.selectbox("Select Evaluator", evaluators)

if selected_evaluator:
    # List of entries evaluated by the selected evaluator
    entry_query = """
    SELECT 
        entry_number, summary_score, tag_score, feedback
    FROM evaluations
    WHERE evaluator = %s
    ORDER BY entry_number;
    """
    entries = load_data(entry_query, (selected_evaluator,))

    if not entries.empty:
        st.write(f"### Entries Evaluated by {selected_evaluator}")
        for idx, row in entries.iterrows():
            entry_number = row['entry_number']
            summary_score = row['summary_score']
            tag_score = row['tag_score']

            if st.button(f"View Entry {entry_number}", key=f"entry_{entry_number}"):
                st.session_state['selected_entry'] = entry_number
                st.session_state['selected_evaluator'] = selected_evaluator
                st.rerun()

            st.write(f"Entry #{entry_number}: Summary Score = {summary_score}, Tag Score = {tag_score}")

    else:
        st.write("This evaluator has not evaluated any entries.")

# Display Selected Entry Details
if 'selected_entry' in st.session_state and 'selected_evaluator' in st.session_state:
    selected_entry = st.session_state['selected_entry']
    selected_evaluator = st.session_state['selected_evaluator']

    st.header(f"Details for Entry #{selected_entry}")

    entry_detail_query = """
    SELECT 
        narrative, succinct_summary, assigned_tags, summary_score, tag_score, feedback
    FROM evaluations
    WHERE evaluator = %s AND entry_number = %s;
    """
    entry_details = load_data(entry_detail_query, (selected_evaluator, selected_entry))

    if not entry_details.empty:
        details = entry_details.iloc[0]
        st.markdown("#### Narrative")
        st.write(details['narrative'])

        st.markdown("#### Succinct Summary")
        st.write(details['succinct_summary'])

        st.markdown("#### Assigned Tags")
        st.write(details['assigned_tags'])

        st.markdown("#### Evaluation Scores")
        st.write(f"**Summary Score:** {details['summary_score']}")
        st.write(f"**Tag Score:** {details['tag_score']}")

        st.markdown("#### Feedback")
        st.write(details['feedback'])
    else:
        st.write(f"No details found for Entry #{selected_entry}.")
