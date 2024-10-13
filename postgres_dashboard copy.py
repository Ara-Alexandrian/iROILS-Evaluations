import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
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

# Create a connection string for SQLAlchemy
connection_string = f"postgresql://{psql_user}:{psql_password}@{psql_host}:{psql_port}/{psql_dbname}"

# Establish SQLAlchemy engine
engine = create_engine(connection_string)

# Function to load data using SQLAlchemy engine
@st.cache_data
def load_data(query, params=None):
    try:
        df = pd.read_sql_query(query, engine, params=params)
        return df
    except Exception as e:
        st.error(f"Error loading data from PostgreSQL: {e}")
        return pd.DataFrame()

# Step 2: Download Data Snapshot Functionality
def download_snapshot():
    try:
        # Query to fetch the evaluation data
        eval_query = """
        SELECT 
            ev.evaluator, ev.entry_number, ev.summary_score, ev.tag_score, ev.feedback, 
            e.data->>'Narrative' AS narrative
        FROM evaluations ev
        JOIN entries e 
        ON ev.entry_number = e.event_number 
        AND ev.institution = e.institution;
        """
        evaluations = load_data(eval_query)

        # Create an in-memory Excel writer object
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write institution summary to the first sheet
            summary_query = """
            SELECT evaluator, COUNT(*) AS total_evaluations, AVG(summary_score) AS avg_summary, AVG(tag_score) AS avg_tag
            FROM evaluations 
            GROUP BY evaluator;
            """
            summary_df = load_data(summary_query)
            summary_df.to_excel(writer, sheet_name='Institution Summary', index=False)

            # Write evaluation data to another sheet
            evaluations.to_excel(writer, sheet_name='Evaluations', index=False)

        # Prepare the file for download
        output.seek(0)  # Move the pointer to the beginning of the file

        st.download_button(
            label="Download Evaluation Data (.xlsx)",
            data=output,
            file_name="evaluation_data_snapshot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Download ready!")
    except Exception as e:
        st.error(f"Failed to download data snapshot: {e}")


# Main Dashboard - Show Running Averages
st.title("PostgreSQL Evaluation Dashboard")

# Query for Evaluator Data
st.header("Evaluator Data")
evaluator_query = """
SELECT DISTINCT evaluator FROM evaluations ORDER BY evaluator;
"""
evaluators = load_data(evaluator_query)['evaluator'].tolist()

selected_evaluator = st.selectbox("Select Evaluator", evaluators)

if selected_evaluator:
    # Fetch the evaluated entries for the selected evaluator
    entry_query = """
    SELECT 
        entry_number, summary_score, tag_score
    FROM evaluations
    WHERE evaluator = %s
    ORDER BY entry_number;
    """
    entries = load_data(entry_query, (selected_evaluator,))

    # Create a dropdown with checkmarks for evaluated entries
    if not entries.empty:
        st.write(f"### Entries Evaluated by {selected_evaluator}")
        
        # Create the dropdown with checkmarks
        entry_display = [
            f"Entry {i+1} - {row['entry_number']} ✅" for i, row in entries.iterrows()
        ]
        selected_entry_display = st.selectbox("Select an Entry to View", entry_display)
        selected_entry_index = int(selected_entry_display.split()[1]) - 1  # Extract the index from the entry number
        selected_entry = entries.iloc[selected_entry_index]

        # Display the selected entry's details in a card-like format
        st.subheader(f"Entry: {selected_entry['entry_number']}")

        st.markdown(
            """
            <div style="padding: 15px; background-color: #f9f9f9; border-radius: 8px;">
            """,
            unsafe_allow_html=True
        )
        st.write(f"**Summary Score:** {selected_entry['summary_score']}")
        st.write(f"**Tag Score:** {selected_entry['tag_score']}")

        # Fetch the additional entry details from the database
        entry_detail_query = """
        SELECT 
            e.data->>'Narrative' AS narrative,
            e.data->>'Succinct Summary' AS succinct_summary,
            e.data->>'Assigned Tags' AS assigned_tags,
            ev.feedback
        FROM evaluations ev
        JOIN entries e ON ev.entry_number = e.event_number AND ev.institution = e.institution
        WHERE ev.evaluator = %s AND ev.entry_number = %s;
        """
        entry_details = load_data(entry_detail_query, params=(selected_evaluator, selected_entry['entry_number']))

        if not entry_details.empty:
            details = entry_details.iloc[0]
            st.markdown("#### Narrative")
            st.write(details['narrative'])

            st.markdown("#### Succinct Summary")
            st.write(details['succinct_summary'])

            st.markdown("#### Assigned Tags")
            st.write(details['assigned_tags'])

            st.markdown("#### Feedback")
            st.write(details['feedback'])

        st.markdown("</div>", unsafe_allow_html=True)

# Button to download data snapshot
st.header("Download Data Snapshot")
download_snapshot()