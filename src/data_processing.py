# /home/wmfs0449/reddit_dashboard/src/data_processing.py

import pandas as pd
import os
from datetime import datetime, timedelta
from supabase import create_client
import io
from src.sentiment_analysis import add_sentiment_analysis

DATA_DIR = "/home/wmfs0449/reddit_dashboard/data"

# Supabase configuration
SUPABASE_URL = "https://mcvnrkoogobezgjcsivw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1jdm5ya29vZ29iZXpnamNzaXZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzgzMjIyNCwiZXhwIjoyMDYzNDA4MjI0fQ.D-uJysR1NPx1gZNdHPiNdjgFlZ1lLTJB_dJ2exopD_E"
BUCKET_NAME = "redditdashboard"

def get_all_csv_from_supabase():
    """Récupère tous les fichiers CSV du bucket Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.storage.from_(BUCKET_NAME).list()

        if not response:
            print(f"No files found in Supabase bucket '{BUCKET_NAME}'")
            return pd.DataFrame(), []

        csv_files = [file for file in response if file.get('name', '').startswith('reddit_trends_') and file.get('name', '').endswith('.csv')]

        if not csv_files:
            print(f"No CSV files found matching pattern in Supabase bucket")
            return pd.DataFrame(), []

        files_with_dates = {}
        for file in csv_files:
            try:
                filename = file.get('name')
                date_str = filename.replace('reddit_trends_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y%m%d')
                files_with_dates[filename] = file_date
            except ValueError:
                print(f"Skipping file with unexpected name format: {file.get('name')}")
                continue

        sorted_files = sorted(files_with_dates.items(), key=lambda x: x[1], reverse=True)

        all_data = []
        file_list = []
        for filename, file_date in sorted_files:
            try:
                file_data = supabase.storage.from_(BUCKET_NAME).download(filename)
                df_temp = pd.read_csv(io.BytesIO(file_data))
                df_temp['file_date'] = file_date # Keep as datetime for now
                all_data.append(df_temp)
                file_list.append({'name': filename, 'date': file_date.strftime('%Y-%m-%d')})
                print(f"Downloaded and processed: {filename}")
            except Exception as e:
                print(f"Error downloading or processing {filename}: {e}")
                continue

        if not all_data:
            return pd.DataFrame(), []

        combined_df = pd.concat(all_data, ignore_index=True)

        # --- Centralized Data Cleaning ---
        combined_df['created_utc'] = pd.to_datetime(combined_df['created_utc'])
        combined_df['author'] = combined_df['author'].fillna('N/A')
        combined_df['flair'] = combined_df['flair'].fillna('None')
        # Ensure 'title' and 'selftext' are strings
        if 'title' in combined_df.columns:
            combined_df['title'] = combined_df['title'].fillna('').astype(str)
        if 'selftext' in combined_df.columns: # Assuming you might have selftext
             combined_df['selftext'] = combined_df['selftext'].fillna('').astype(str)
        else: # Add selftext if not present, for keyword search consistency
            combined_df['selftext'] = ''

        numeric_cols = ['score', 'num_comments']
        for col in numeric_cols:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
        combined_df = combined_df.dropna(subset=numeric_cols) # Drop rows where score/comments couldn't be parsed
        combined_df['score'] = combined_df['score'].astype(int)
        combined_df['num_comments'] = combined_df['num_comments'].astype(int)
        combined_df['file_date'] = pd.to_datetime(combined_df['file_date']).dt.strftime('%Y-%m-%d') # Now convert to string

        return combined_df, file_list

    except Exception as e:
        print(f"Error accessing Supabase storage (get_all_csv_from_supabase): {e}")
        return pd.DataFrame(), []

def find_latest_csv_from_supabase():
    """Finds the most recent CSV file in Supabase bucket based on filename date."""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.storage.from_(BUCKET_NAME).list()

        if not response:
            print(f"No files found in Supabase bucket '{BUCKET_NAME}'")
            return None, None

        csv_files = [file for file in response if file.get('name', '').startswith('reddit_trends_') and file.get('name', '').endswith('.csv')]

        if not csv_files:
            print(f"No CSV files found matching pattern in Supabase bucket")
            return None, None

        files_with_dates = {}
        for file in csv_files:
            try:
                filename = file.get('name')
                date_str = filename.replace('reddit_trends_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y%m%d')
                files_with_dates[filename] = file_date
            except ValueError:
                print(f"Skipping file with unexpected name format: {file.get('name')}")
                continue

        if not files_with_dates:
            print(f"No valid dated CSV files found in Supabase bucket")
            return None, None

        latest_filename = max(files_with_dates, key=files_with_dates.get)
        file_data = supabase.storage.from_(BUCKET_NAME).download(latest_filename)

        print(f"Found and downloaded latest CSV from Supabase: {latest_filename}")
        return file_data, latest_filename

    except Exception as e:
        print(f"Error accessing Supabase storage (find_latest_csv_from_supabase): {e}")
        return None, None

def find_latest_csv(directory):
    """Finds the most recent CSV file in the specified directory based on filename date."""
    list_of_files = glob.glob(os.path.join(directory, 'reddit_trends_*.csv'))
    if not list_of_files:
        print(f"No CSV files found matching pattern in {directory}")
        return None

    files_with_dates = {}
    for f in list_of_files:
        try:
            date_str = os.path.basename(f).replace('reddit_trends_', '').replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y%m%d')
            files_with_dates[f] = file_date
        except ValueError:
            print(f"Skipping file with unexpected name format: {f}")
            continue

    if not files_with_dates:
        print(f"No valid dated CSV files found in {directory}")
        return None

    latest_file = max(files_with_dates, key=files_with_dates.get)
    print(f"Found latest CSV: {latest_file}")
    return latest_file

def _clean_dataframe(df, filename_for_date=None):
    """Helper function to clean a dataframe and add file_date if filename is provided."""
    df['created_utc'] = pd.to_datetime(df['created_utc'])
    df['author'] = df['author'].fillna('N/A')
    df['flair'] = df['flair'].fillna('None')
    if 'title' in df.columns:
        df['title'] = df['title'].fillna('').astype(str)
    if 'selftext' in df.columns: # Assuming you might have selftext
        df['selftext'] = df['selftext'].fillna('').astype(str)
    else: # Add selftext if not present, for keyword search consistency
        df['selftext'] = ''

    numeric_cols = ['score', 'num_comments']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df['score'] = df['score'].astype(int)
    df['num_comments'] = df['num_comments'].astype(int)

    if filename_for_date:
        try:
            date_str = os.path.basename(filename_for_date).replace('reddit_trends_', '').replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y%m%d')
            df['file_date'] = file_date.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Warning: Could not parse date from filename {filename_for_date} for 'file_date' column.")
            df['file_date'] = datetime.now().strftime('%Y-%m-%d') # Fallback
    return df

def load_data(time_period='day'):
    """Loads data from CSV files based on time period, prioritizing Supabase."""
    if time_period in ['week', 'month', 'all']:
        combined_df, file_list = get_all_csv_from_supabase() # Already cleaned here
        if not combined_df.empty:
            print(f"Successfully loaded {len(file_list)} files from Supabase for {time_period} analysis.")

            combined_df['file_date_dt'] = pd.to_datetime(combined_df['file_date'])
            now = datetime.now()
            if time_period == 'week':
                cutoff_date = now - timedelta(days=7)
                combined_df = combined_df[combined_df['file_date_dt'] >= cutoff_date]
            elif time_period == 'month':
                month_ago = now - timedelta(days=30) # Defined month_ago
                combined_df = combined_df[combined_df['file_date_dt'] >= month_ago]

            if not combined_df.empty: # Check if df is empty after filtering
                combined_df = combined_df.drop(columns=['file_date_dt'])
                # Ajouter l'analyse de sentiment
                combined_df = add_sentiment_analysis(combined_df)
            else: # if empty after filtering, return empty df with original columns
                empty_df_cols = list(combined_df.columns)
                empty_df_cols.remove('file_date_dt') # remove temporary column
                return pd.DataFrame(columns=empty_df_cols), f"Supabase: 0 files after time filter ({time_period} analysis)"

            return combined_df, f"Supabase: {len(file_list)} files ({time_period} analysis)"
        else:
            print(f"No data found in Supabase for {time_period} analysis, trying local files (not implemented for multi-file local).")

    file_data, latest_filename_supabase = find_latest_csv_from_supabase()

    if file_data:
        try:
            df = pd.read_csv(io.BytesIO(file_data))
            df = _clean_dataframe(df, latest_filename_supabase) # Cleaned here
            # Ajouter l'analyse de sentiment
            df = add_sentiment_analysis(df)
            print(f"Successfully loaded data from Supabase: {latest_filename_supabase}")
            return df, f"Supabase: {latest_filename_supabase}"
        except Exception as e:
            print(f"Error processing data from Supabase: {e}. Trying local.")

    latest_csv_local = find_latest_csv(DATA_DIR)
    if latest_csv_local and os.path.exists(latest_csv_local):
        try:
            df = pd.read_csv(latest_csv_local)
            df = _clean_dataframe(df, latest_csv_local) # Cleaned here
            # Ajouter l'analyse de sentiment
            df = add_sentiment_analysis(df)
            print(f"Successfully loaded data from local file: {latest_csv_local}")
            return df, f"Local: {os.path.basename(latest_csv_local)}"
        except Exception as e:
            print(f"Error loading or processing data from {latest_csv_local}: {e}")
            return pd.DataFrame(), "Error: Could not load local data."

    print(f"No CSV data file found or accessible (Supabase or local in {DATA_DIR}).")
    return pd.DataFrame(), "No data source found."

