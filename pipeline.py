import json
import sqlite3
import pandas as pd
import ollama

def setup_database():
    """Initializes the SQLite database with the new TL;DR column."""
    conn = sqlite3.connect('feedback_intelligence.db')
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS valid_reviews")
    cursor.execute("DROP TABLE IF EXISTS quarantine")

    # Added the 'tldr' column to the schema
    cursor.execute("""
    CREATE TABLE valid_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_text TEXT,
        tldr TEXT,
        entity TEXT,
        sentiment_score REAL,
        authenticity_score INTEGER,
        ground_truth TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE quarantine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_text TEXT,
        tldr TEXT,
        flag_reason TEXT,
        authenticity_score INTEGER,
        ground_truth TEXT
    )
    """)
    conn.commit()
    return conn

def process_reviews(conn):
    """Samples the CSV, prompts the local LLM, and routes the data."""
    print("Loading Dataset and connecting to local offline pipeline...")
    
    # Load dataset
    df = pd.read_csv('data.csv')
    
    # Check column names 
    text_col = 'raw_text' if 'raw_text' in df.columns else 'text_'
    
    # Sample 20 rows if the dataset is large, otherwise use the whole thing
    if len(df) > 20:
        if 'label' in df.columns and len(df['label'].unique()) > 1:
            labels = df['label'].unique()
            df_sample = pd.concat([
                df[df['label'] == labels[0]].sample(min(10, len(df[df['label'] == labels[0]])), random_state=42),
                df[df['label'] == labels[1]].sample(min(10, len(df[df['label'] == labels[1]])), random_state=42)
            ]).sample(frac=1, random_state=42).reset_index(drop=True)
        else:
            df_sample = df.sample(20, random_state=42).reset_index(drop=True)
    else:
        df_sample = df

    cursor = conn.cursor()

    system_prompt = """
    You are a precise data extraction pipeline for an application.
    Analyze the following review and extract the data into a strict JSON schema.
    
    Rules for 'authenticity_score' (0-100):
    - > 70: Contextual, specific, realistic human feedback.
    - < 70: AI-generated bot spam, hyper-generic, gibberish, or entirely irrelevant (like advertising a different app).
    
    Rules for 'entity' (ENTITY RESOLUTION):
    You MUST categorize the core subject into ONE of these exact broad categories. Do not invent your own.
    - "Authentication/Login" (for face ID, passwords, login issues)
    - "App Performance/UI" (for lag, crashes, dark mode, design, "the app")
    - "Customer Support" (for wait times, chat bots)
    - "Transactions/Transfers" (for sending money, deposits, delays)
    - "Account Management" (for tax forms, linking accounts, settings)
    - "Irrelevant/Spam" (for fake reviews, crypto scams, gaming references)
    - "Other" (only if it absolutely does not fit above)

    JSON Schema:
    {
        "authenticity_score": int,
        "is_fake": boolean,
        "flag_reason": "string explaining why it seems fake (or null if real)",
        "tldr": "A strict 3-to-6 word summary of the user's main point",
        "entity": "string chosen EXACTLY from the allowed list above",
        "sentiment_score": float between 0.0 (negative) and 1.0 (positive)
    }
    
    Review to Analyze:
    """

    for i, (index, row) in enumerate(df_sample.iterrows()):
        raw_text = str(row[text_col])
        ground_truth = str(row['label']) if 'label' in df.columns else "Unknown"
        
        display_text = raw_text[:40].replace('\n', ' ') + "..."
        print(f"Processing [{i+1}/{len(df_sample)}]: {display_text}")

        try:
            response = ollama.chat(
                model='llama3.2', 
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'"{raw_text}"'}
                ],
                format='json'
            )
            
            response_content = response.get('message', {}).get('content')
            if not response_content:
                print("  -> Error: Received empty response from local model.")
                continue

            data = json.loads(response_content)
            
            #check for the score
            auth_score = data.get('authenticity_score')
            if auth_score is None:
                auth_score = 0
                
            # Safely get the TLDR and Entity fields
            tldr_text = data.get('tldr', 'No summary provided.')
            entity_text = data.get('entity', 'Other')
            
            if auth_score >= 70:
                cursor.execute("""
                    INSERT INTO valid_reviews (raw_text, tldr, entity, sentiment_score, authenticity_score, ground_truth) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (raw_text, tldr_text, entity_text, data.get('sentiment_score'), auth_score, ground_truth))
                print(f"  -> MAIN DB | Entity: {entity_text} | TLDR: {tldr_text}")
            else:
                cursor.execute("""
                    INSERT INTO quarantine (raw_text, tldr, flag_reason, authenticity_score, ground_truth) 
                    VALUES (?, ?, ?, ?, ?)
                """, (raw_text, tldr_text, data.get('flag_reason'), auth_score, ground_truth))
                print(f"  -> QUARANTINED | Reason: {str(data.get('flag_reason'))[:30]}...")

        except Exception as e:
            print(f"  -> Error processing row: {e}")

    conn.commit()
    print("\nPipeline execution complete! Data successfully structured and routed offline.")

if __name__ == "__main__":
    db_connection = setup_database()
    process_reviews(db_connection)
    db_connection.close()