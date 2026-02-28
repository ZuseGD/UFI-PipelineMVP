# A Streamlit app that reads the SQLite database, displays the aggregated metrics using Plotly, and provides an interface for the human to audit the "Quarantine" table.

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="AI Feedback Pipeline", layout="wide")
st.title("🛡️ Unstructured Intelligence & Quarantine Pipeline")
st.markdown("Locally hosted Llama-3.2 processing unstructured product feedback.")

# load data from the SQLite database
@st.cache_data
def load_data():
    conn = sqlite3.connect('feedback_intelligence.db')
    valid_df = pd.read_sql_query("SELECT * FROM valid_reviews", conn)
    quar_df = pd.read_sql_query("SELECT * FROM quarantine", conn)
    conn.close()
    return valid_df, quar_df

valid_df, quar_df = load_data()

# Website Layout with tabs
tab1, tab2 = st.tabs(["📊 Strategic Product Dashboard (Valid Data)", "🚨 Security Audit (Quarantine)"])

with tab1:
    st.header("Actionable User Sentiment")
    st.markdown("This data has been filtered for bot-spam and synthetic reviews.")
    
    if not valid_df.empty:
        # KPI Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Valid Reviews", len(valid_df))
        col2.metric("Average Sentiment", f"{valid_df['sentiment_score'].mean():.2f}")
        col3.metric("Data Poisoning Prevented", f"{len(quar_df)} rows")

        # Chart
        st.subheader("Feature Sentiment Breakdown")
        entity_counts = valid_df['entity'].value_counts().reset_index()
        entity_counts.columns = ['Feature', 'Mentions']
        fig = px.bar(entity_counts, x='Feature', y='Mentions', title="Most Discussed Features")
        st.plotly_chart(fig, width='stretch')

        # Show the raw dataframre for valid reviews
        st.dataframe(
            valid_df[['tldr', 'entity', 'sentiment_score', 'authenticity_score', 'raw_text']],
            width='stretch',
            hide_index=True,
            column_config={
                "tldr": st.column_config.TextColumn(
                    "Key Takeaway (TL;DR)", 
                    width="medium",
                    help="AI-generated summary of the review"
                ),
                "entity": st.column_config.TextColumn(
                    "Product/Feature", 
                    width="small"
                ),
                "sentiment_score": st.column_config.ProgressColumn(
                    "Sentiment",
                    help="0 is highly negative, 1 is highly positive",
                    format="%.2f",
                    min_value=0,
                    max_value=1,
                ),
                "authenticity_score": st.column_config.NumberColumn(
                    "AI Trust Score",
                    width="small"
                ),
                "raw_text": st.column_config.TextColumn(
                    "Original Raw Review", 
                    width="large" # This forces long text to have its own wide column
                )
            }
        )
    else:
        st.info("No valid reviews processed yet.")

with tab2:
    st.header("Quarantine Audit Log")
    st.markdown("**Critical Human Decision:** The AI scores the text, but the human sets the threshold and audits the quarantine for false positives.")
    
    if not quar_df.empty:
        # Calculate AI Accuracy based on Ground Truth
        # 'CG' means Computer Generated (Fake). The AI was correct if it quarantined a 'CG' review.
        correct_quarantines = len(quar_df[quar_df['ground_truth'] == 'CG'])
        false_positives = len(quar_df[quar_df['ground_truth'] == 'OR']) # AI thought it was fake, but it was real
        
        st.warning(f"⚠️ {len(quar_df)} reviews quarantined due to low authenticity scores.")
        
        col_a, col_b = st.columns(2)
        col_a.metric("True Fakes Caught ('CG')", correct_quarantines)
        col_b.metric("False Positives ('OR')", false_positives, delta_color="inverse")
        
        # Display the Quarantine Table
        st.dataframe(quar_df[['tldr', 'raw_text', 'flag_reason', 'authenticity_score', 'ground_truth']], width='stretch')
        
        # Simulate the Human Override
        st.subheader("Manual Override")
        override_id = st.selectbox("Select ID to restore to Main Database:", quar_df['id'].tolist() if not quar_df.empty else [])
        if st.button("Restore Review"):
            st.success(f"Review {override_id} restored! (Simulation)")
    else:
        st.success("No reviews currently in quarantine.")