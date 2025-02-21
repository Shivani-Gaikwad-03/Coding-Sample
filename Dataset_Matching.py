# Code to link the Infra360 and Dealscan databases using fuzzy matching and exact matching

import pandas as pd
from rapidfuzz import fuzz, process
from rapidfuzz.distance.JaroWinkler import similarity
import numpy as np

# Configure display settings
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Load datasets
db1 = pd.read_stata('Data/Database1.dta')  # Anonymized 
db2 = pd.read_stata('Data/Database2.dta')   #Anonymized 

# Count unique IDs 
unique_ids_count = db2['UniqueID'].nunique()
print(f"Number of unique IDs in db2: {unique_ids_count}")

# Define relevant columns
relevant_columns = ['UniqueID', 'Date', 'EntityName', 'Region', 'IndustryCode',
                    'TotalAmount', 'DealID', 'Borrower', 'Sponsor', 'LoanType']

# Normalize text for matching
def normalize_text(text):
    return text.lower().strip().replace('&', 'and').replace('-', ' ') if isinstance(text, str) else ''

db1['NormalizedEntity'] = db1['EntityName'].apply(normalize_text)
db2['NormalizedBorrower'] = db2['Borrower'].apply(normalize_text)
db1['NormalizedSponsor'] = db1['Sponsor'].apply(normalize_text)
db2['NormalizedSponsor'] = db2['Sponsor'].apply(normalize_text)

# Tier-1: Exact Match (EntityName with Borrower)
tier1_matches = []
db2_borrowers = db2['NormalizedBorrower'].tolist()

for _, row in db1.iterrows():
    matching_rows = db2[db2['NormalizedBorrower'] == row['NormalizedEntity']]
    for _, match in matching_rows.iterrows():
        match_data = {col: row.get(col, None) for col in relevant_columns}
        match_data.update({col: match.get(col, None) for col in relevant_columns})
        match_data["Tier"] = 1
        tier1_matches.append(match_data)

tier1_df = pd.DataFrame(tier1_matches)
matched_ids_tier1 = set(tier1_df['UniqueID'].tolist())

# Tier-2: Exact Match (Sponsor with Sponsor)
tier2_matches = []
for _, row in db1.iterrows():
    if row['UniqueID'] not in matched_ids_tier1 and row['NormalizedSponsor']:
        matching_rows = db2[db2['NormalizedSponsor'] == row['NormalizedSponsor']]
        for _, match in matching_rows.iterrows():
            match_data = {col: row.get(col, None) for col in relevant_columns}
            match_data.update({col: match.get(col, None) for col in relevant_columns})
            match_data["Tier"] = 2
            tier2_matches.append(match_data)

tier2_df = pd.DataFrame(tier2_matches)
matched_ids = set(tier1_df['UniqueID'].tolist() + tier2_df['UniqueID'].tolist())

# Tier-3: Fuzzy Matching
def fuzzy_match(target, candidates, threshold=0.85):
    matches = process.extract(target, candidates, scorer=similarity, score_cutoff=threshold, limit=5)
    return matches[0] if matches else (None, 0, None)

tier3_matches = []
for _, row in db1.iterrows():
    if row['UniqueID'] not in matched_ids:
        best_match, match_score, _ = fuzzy_match(row['NormalizedEntity'], db2_borrowers)
        if match_score >= 0.85:
            matching_rows = db2[db2['NormalizedBorrower'] == best_match]
            for _, match in matching_rows.iterrows():
                match_data = {col: row.get(col, None) for col in relevant_columns}
                match_data.update({col: match.get(col, None) for col in relevant_columns})
                match_data["BestMatch"] = best_match
                match_data["MatchScore"] = match_score
                match_data["Tier"] = 3
                tier3_matches.append(match_data)

tier3_df = pd.DataFrame(tier3_matches)

# Combine results
final_matches = pd.concat([tier1_df, tier2_df, tier3_df], ignore_index=True)
final_matches.to_stata("final_matches.dta", version=117)

# Identify unmatched records
unmatched_db1 = db1[~db1['UniqueID'].isin(final_matches['UniqueID'])]
unmatched_db1['Tier'] = 'No Match'
for col in relevant_columns:
    if col not in unmatched_db1:
        unmatched_db1[col] = np.nan

# Combine all data
final_results = pd.concat([final_matches, unmatched_db1[relevant_columns + ['Tier']]], ignore_index=True)
final_results.to_stata("final_results.dta", version=117)

# Data check
final_results['Date'] = pd.to_datetime(final_results['Date'], errors='coerce')
final_results['DealDate'] = pd.to_datetime(final_results['DealID'], errors='coerce')
final_results['DateMismatch'] = final_results['Date'] != final_results['DealDate']

# Summarize and validate
print(final_results.info())
