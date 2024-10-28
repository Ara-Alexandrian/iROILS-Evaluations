import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
import configparser
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import ConfigManager

# Initialize configuration
config_manager = ConfigManager()
pg_config = config_manager.get_postgresql_config('home')

# Create a connection string for SQLAlchemy
connection_string = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['dbname']}"

# Establish SQLAlchemy engine
try:
  engine = create_engine(connection_string)
except Exception as e:
  st.error(f"Failed to create database engine: {e}")
  st.stop()

# Rest of the postgres_dashboard.py code remains the same...

# Ensure cache is refreshed when needed
@st.cache_data(show_spinner=False, ttl=60)
def load_data(query, params=None):
  try:
      # Convert params to tuple if it's a single value
      if params and not isinstance(params, (list, tuple)):
          params = (params,)
      
      df = pd.read_sql_query(
          sql=query, 
          con=engine,
          params=params if params else None
      )
      return df
  except Exception as e:
      st.error(f"Error loading data from PostgreSQL: {e}")
      return pd.DataFrame()

# Main Dashboard - Show Running Averages
st.title("PostgreSQL Evaluation Dashboard")

# Query for Evaluator Data
evaluator_query = """
SELECT DISTINCT evaluator FROM evaluations ORDER BY evaluator;
"""

# Load evaluators
evaluators = load_data(evaluator_query)['evaluator'].tolist()

# Add "All Evaluators" option
evaluators.insert(0, "All Evaluators")

# Dropdown for selecting evaluator
selected_evaluator = st.selectbox("Select Evaluator", evaluators, key="evaluator_selectbox")

# Display the evaluator stats and entries
if selected_evaluator:
  if selected_evaluator == "All Evaluators":
      # Overall institution performance
      st.header("Overall Institution Performance")
      
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
      
      # Display all evaluated entries
      all_entries_query = """
      SELECT entry_number, summary_score, tag_score
      FROM evaluations
      ORDER BY entry_number;
      """
      all_entries = load_data(all_entries_query)
      
      if not all_entries.empty:
          st.write("### All Evaluated Entries")
          entry_display = [
              f"Entry {i+1} - {row['entry_number']} ✅" 
              for i, row in all_entries.iterrows()
          ]
          
          selected_entry_display = st.selectbox(
              "Select an Entry to View", 
              entry_display, 
              key="all_evaluated_entries_selectbox"
          )
          
          if selected_entry_display:
              selected_entry_index = int(selected_entry_display.split()[1]) - 1
              selected_entry = all_entries.iloc[selected_entry_index]
              
              st.subheader(f"Entry: {selected_entry['entry_number']}")
              st.write(f"**Summary Score:** {selected_entry['summary_score']}")
              st.write(f"**Tag Score:** {selected_entry['tag_score']}")
              
              # Fetch additional entry details
              entry_detail_query = """
              SELECT 
                  e.data->>'Narrative' AS narrative,
                  e.data->>'Succinct Summary' AS succinct_summary,
                  e.data->>'Assigned Tags' AS assigned_tags,
                  ev.feedback
              FROM evaluations ev
              JOIN entries e ON ev.entry_number = e.event_number 
                  AND ev.institution = e.institution
              WHERE ev.entry_number = %s;
              """
              entry_details = load_data(entry_detail_query, params=(selected_entry['entry_number'],))
              
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
  
  else:
      # Individual evaluator performance
      st.header(f"Statistics for {selected_evaluator}")
      
      stats_query = """
      SELECT 
          COUNT(*) AS total_evaluations, 
          ROUND(AVG(summary_score)::numeric, 2) AS avg_summary_score, 
          ROUND(AVG(tag_score)::numeric, 2) AS avg_tag_score
      FROM evaluations
      WHERE evaluator = %s;
      """
      stats = load_data(stats_query, params=(selected_evaluator,))
      
      if not stats.empty:
          st.write(f"**Total Evaluations:** {stats.iloc[0]['total_evaluations']}")
          st.write(f"**Average Summary Score:** {stats.iloc[0]['avg_summary_score']}")
          st.write(f"**Average Tag Score:** {stats.iloc[0]['avg_tag_score']}")
          
          # Display evaluator's entries
          entries_query = """
          SELECT entry_number, summary_score, tag_score
          FROM evaluations
          WHERE evaluator = %s
          ORDER BY entry_number;
          """
          entries = load_data(entries_query, params=(selected_evaluator,))
          
          if not entries.empty:
              st.write(f"### Entries Evaluated by {selected_evaluator}")
              entry_display = [
                  f"Entry {i+1} - {row['entry_number']} ✅" 
                  for i, row in entries.iterrows()
              ]
              
              selected_entry_display = st.selectbox(
                  "Select an Entry to View", 
                  entry_display, 
                  key="evaluator_entries_selectbox"
              )
              
              if selected_entry_display:
                  selected_entry_index = int(selected_entry_display.split()[1]) - 1
                  selected_entry = entries.iloc[selected_entry_index]
                  
                  st.subheader(f"Entry: {selected_entry['entry_number']}")
                  st.write(f"**Summary Score:** {selected_entry['summary_score']}")
                  st.write(f"**Tag Score:** {selected_entry['tag_score']}")
                  
                  # Fetch entry details
                  entry_detail_query = """
                  SELECT 
                      e.data->>'Narrative' AS narrative,
                      e.data->>'Succinct Summary' AS succinct_summary,
                      e.data->>'Assigned Tags' AS assigned_tags,
                      ev.feedback
                  FROM evaluations ev
                  JOIN entries e ON ev.entry_number = e.event_number 
                      AND ev.institution = e.institution
                  WHERE ev.evaluator = %s AND ev.entry_number = %s;
                  """
                  entry_details = load_data(
                      entry_detail_query, 
                      params=(selected_evaluator, selected_entry['entry_number'])
                  )
                  
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

# Add download functionality
def download_snapshot():
  try:
      eval_query = """
      SELECT 
          ev.evaluator, ev.entry_number, ev.summary_score, ev.tag_score, 
          ev.feedback, e.data->>'Narrative' AS narrative
      FROM evaluations ev
      JOIN entries e ON ev.entry_number = e.event_number 
          AND ev.institution = e.institution;
      """
      evaluations = load_data(eval_query)
      
      if not evaluations.empty:
          st.success(f"{len(evaluations)} evaluation entries found for export.")
          
          output = BytesIO()
          with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
              # Write summary sheet
              summary_query = """
              SELECT evaluator, 
                     COUNT(*) AS total_evaluations, 
                     ROUND(AVG(summary_score)::numeric, 2) AS avg_summary, 
                     ROUND(AVG(tag_score)::numeric, 2) AS avg_tag
              FROM evaluations 
              GROUP BY evaluator;
              """
              summary_df = load_data(summary_query)
              
              # Add institution average
              institution_avg_query = """
              SELECT 
                  COUNT(*) AS total_evaluations, 
                  ROUND(AVG(summary_score)::numeric, 2) AS avg_summary, 
                  ROUND(AVG(tag_score)::numeric, 2) AS avg_tag
              FROM evaluations;
              """
              institution_avg = load_data(institution_avg_query).iloc[0]
              
              institution_row = pd.DataFrame({
                  'evaluator': ['Institution Average'],
                  'total_evaluations': [institution_avg['total_evaluations']],
                  'avg_summary': [institution_avg['avg_summary']],
                  'avg_tag': [institution_avg['avg_tag']]
              })
              
              summary_df = pd.concat([summary_df, institution_row], ignore_index=True)
              summary_df.to_excel(writer, sheet_name='Institution Summary', index=False)
              evaluations.to_excel(writer, sheet_name='Evaluations', index=False)
          
          output.seek(0)
          st.download_button(
              label="Download Evaluation Data (.xlsx)",
              data=output,
              file_name="evaluation_data_snapshot.xlsx",
              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          )
          st.success("Download ready!")
      else:
          st.warning("No evaluation data found for export.")
  except Exception as e:
      st.error(f"Failed to download data snapshot: {e}")

# Add download button
st.header("Download Data Snapshot")
download_snapshot()