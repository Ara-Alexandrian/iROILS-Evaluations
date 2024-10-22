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

# Query for Evaluator Data
evaluator_query = """
SELECT DISTINCT evaluator FROM evaluations ORDER BY evaluator;
"""

# Ensure cache is refreshed when needed
@st.cache_data(show_spinner=False, ttl=60)  # Set TTL to avoid long-term cache
def load_data(query, reset=False, params=None):
    if reset:
        st.cache_data.clear()  # Clear cache to force data reload after reset
    try:
        df = pd.read_sql_query(query, engine, params=params)
        return df
    except Exception as e:
        st.error(f"Error loading data from PostgreSQL: {e}")
        return pd.DataFrame()

# Function to reset data
def reset_data():
    # Add logic here to clear/reset data for evaluators (e.g., resetting the database)
    # Once reset is done, reload data with cache cleared
    load_data(evaluator_query, reset=True)

# Call the reset function
reset_data()

# Now reload the evaluators after cache invalidation
evaluators = load_data(evaluator_query)['evaluator'].tolist()

# Add "All Evaluators" option to see overall performance for the institution
evaluators.insert(0, "All Evaluators")

# Dropdown for selecting evaluator (with a unique key)
selected_evaluator = st.selectbox("Select Evaluator", evaluators, key="evaluator_selectbox")


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

        # Debugging: Check if evaluations data is loaded properly
        if evaluations.empty:
            st.warning("No evaluation data found for export.")
        else:
            st.success(f"{len(evaluations)} evaluation entries found for export.")

        # Create an in-memory Excel writer object
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write institution summary to the first sheet
            summary_query = """
            SELECT evaluator, COUNT(*) AS total_evaluations, 
                   ROUND(AVG(summary_score)::numeric, 2) AS avg_summary, 
                   ROUND(AVG(tag_score)::numeric, 2) AS avg_tag
            FROM evaluations 
            GROUP BY evaluator;
            """
            summary_df = load_data(summary_query)

            # Calculate the overall institution average
            institution_avg_query = """
            SELECT 
                COUNT(*) AS total_evaluations, 
                ROUND(AVG(summary_score)::numeric, 2) AS avg_summary, 
                ROUND(AVG(tag_score)::numeric, 2) AS avg_tag
            FROM evaluations;
            """
            institution_avg = load_data(institution_avg_query).iloc[0]

            # Append institution average as a new row
            institution_row = pd.DataFrame({
                'evaluator': ['Institution Average'],
                'total_evaluations': [institution_avg['total_evaluations']],
                'avg_summary': [institution_avg['avg_summary']],
                'avg_tag': [institution_avg['avg_tag']]
            })

            # Concatenate the summary dataframe with the institution row
            summary_df = pd.concat([summary_df, institution_row], ignore_index=True)

            # Write the updated summary sheet to the Excel file
            summary_df.to_excel(writer, sheet_name='Institution Summary', index=False)

            # Ensure the evaluations data is written to the "Evaluations" sheet
            if not evaluations.empty:
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

# Ensure cache is refreshed when needed
@st.cache_data(show_spinner=False, ttl=60)  # Set TTL to avoid long-term cache
def load_data(query, params=None):
    try:
        df = pd.read_sql_query(query, engine, params=params)
        return df
    except Exception as e:
        st.error(f"Error loading data from PostgreSQL: {e}")
        return pd.DataFrame()

# Query for Evaluator Data
st.header("Evaluator Data")
evaluator_query = """
SELECT DISTINCT evaluator FROM evaluations ORDER BY evaluator;
"""

# Reload the evaluator list to ensure we have the latest data
evaluators = load_data(evaluator_query)['evaluator'].tolist()

# Check if 'nviscariello' is in the list of evaluators, if not, add it manually
if 'nviscariello' not in evaluators:
    evaluators.append('nviscariello')  # Fallback in case it's missing

# Add "All Evaluators" option to see overall performance for the institution
evaluators.insert(0, "All Evaluators")

# Dropdown for selecting evaluator (with a unique key)
selected_evaluator = st.selectbox("Select Evaluator", evaluators, key="evaluator_performance_selectbox")


# Display the evaluator stats and entries
if selected_evaluator:
    if selected_evaluator == "All Evaluators":
        # Overall institution performance
        st.header("Overall Institution Performance")
        
        # Fetch and display overall stats
        overall_stats_query = """
        SELECT 
            COUNT(*) AS total_evaluations, 
            ROUND(AVG(summary_score)::numeric, 2) AS avg_summary_score, 
            ROUND(AVG(tag_score)::numeric, 2) AS avg_tag_score
        FROM evaluations;
        """
        overall_stats = load_data(overall_stats_query)
        
        if not overall_stats.empty:
            st.write(f"**Total Evaluations:** {overall_stats.iloc[0]['total_evaluations']}")
            st.write(f"**Average Summary Score:** {overall_stats.iloc[0]['avg_summary_score']}")
            st.write(f"**Average Tag Score:** {overall_stats.iloc[0]['avg_tag_score']}")
        else:
            st.write(f"No evaluations found for the institution.")
        
        # Fetch and display all evaluated entries for the institution
        all_entries_query = """
        SELECT 
            entry_number, summary_score, tag_score
        FROM evaluations
        ORDER BY entry_number;
        """
        all_entries = load_data(all_entries_query)
        
        if not all_entries.empty:
            st.write("### All Evaluated Entries")
            
            # Create dropdown with checkmarks for all entries
            all_entry_display = [
                f"Entry {i+1} - {row['entry_number']} ✅" for i, row in all_entries.iterrows()
            ]
            selected_all_entry_display = st.selectbox("Select an Entry to View", all_entry_display, key="all_evaluated_entries_selectbox")
            selected_all_entry_index = int(selected_all_entry_display.split()[1]) - 1  # Extract the index from the entry number
            selected_all_entry = all_entries.iloc[selected_all_entry_index]

            # Display the selected entry's details
            st.subheader(f"Entry: {selected_all_entry['entry_number']}")
            st.write(f"**Summary Score:** {selected_all_entry['summary_score']}")
            st.write(f"**Tag Score:** {selected_all_entry['tag_score']}")

            # Fetch the additional entry details from the database
            all_entry_detail_query = """
            SELECT 
                e.data->>'Narrative' AS narrative,
                e.data->>'Succinct Summary' AS succinct_summary,
                e.data->>'Assigned Tags' AS assigned_tags,
                ev.feedback
            FROM evaluations ev
            JOIN entries e ON ev.entry_number = e.event_number AND ev.institution = e.institution
            WHERE ev.entry_number = %s;
            """
            all_entry_details = load_data(all_entry_detail_query, params=(selected_all_entry['entry_number'],))

            if not all_entry_details.empty:
                details = all_entry_details.iloc[0]
                st.markdown("#### Narrative")
                st.write(details['narrative'])

                st.markdown("#### Succinct Summary")
                st.write(details['succinct_summary'])

                st.markdown("#### Assigned Tags")
                st.write(details['assigned_tags'])

                st.markdown("#### Feedback")
                st.write(details['feedback'])

    else:
        # Individual evaluator performance
        st.header(f"Statistics for {selected_evaluator}")
        
        # Fetch and display evaluator stats
        stats_query = """
        SELECT 
            COUNT(*) AS total_evaluations, 
            ROUND(AVG(summary_score)::numeric, 2) AS avg_summary_score, 
            ROUND(AVG(tag_score)::numeric, 2) AS avg_tag_score
        FROM evaluations
        WHERE evaluator = %s;
        """
        stats = load_data(stats_query, (selected_evaluator,))
        
        if not stats.empty:
            st.write(f"**Total Evaluations by {selected_evaluator}:** {stats.iloc[0]['total_evaluations']}")
            st.write(f"**Average Summary Score:** {stats.iloc[0]['avg_summary_score']}")
            st.write(f"**Average Tag Score:** {stats.iloc[0]['avg_tag_score']}")
        else:
            st.write(f"No evaluations found for {selected_evaluator}.")

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
            selected_entry_display = st.selectbox("Select an Entry to View", entry_display, key="evaluator_entries_selectbox")
            selected_entry_index = int(selected_entry_display.split()[1]) - 1  # Extract the index from the entry number
            selected_entry = entries.iloc[selected_entry_index]

            # Display the selected entry's details
            st.subheader(f"Entry: {selected_entry['entry_number']}")
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

# Button to download data snapshot
st.header("Download Data Snapshot")
download_snapshot()
