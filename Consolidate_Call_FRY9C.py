### Combining the Call data and FR-Y9C data ###

########
# Read the feather file (1986 to 2019)
df_call = pd.read_feather('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/call_clean.feather')

df_call.tail()
df_call.info()

#######
#1. Check if the following variables from IO_final.ipynb have the same variable definitions + a consistent time series from 2000 to 2019:
# ['assets','deposits','numemployees','agloans','liabilities']
# (['rssdhcr','year'])[['intexpdomdep','salaries','exponpremises']

# Importing the FR-Y9C data (1990 to 2021)
df_holding = pd.read_csv('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/Holding_data_raw_FRY9C.csv')
df_holding.head()
#renaming rssdid to rssdhcr
df_holding=df_holding.rename(columns={"rssdid": "rssdhcr"})
df_call=df_call.rename(columns={"bhcid": "rssdhcr"}) 
df_holding.tail()

#All variable names listed above are now consistent in both datasets. 
#All variable names listed above form a consistent time series from 2000 to 2019 (refer folder_structure/code/FRY-9C_Inv.do for graphs). 

#2. Combining both datasets (1990 to 2019)
#Making both consistent wrt time
start_date = pd.to_datetime('1990-03-31 00:00:00')
end_date = pd.to_datetime('2019-12-31 00:00:00')
#Call data 
df_call = df_call[~df_call['date'].isna()].copy() # Remove observations with null dates
df_call['date']  = pd.to_datetime(df_call.date) 

df_call = df_call[(df_call['date']>= start_date) & (df_call['date']<= end_date)]
df_call.sort_values(["date"])

#Holding 
df_holding= df_holding[~df_holding['date'].isna()].copy() # Remove observations with null dates
df_holding['date']  = pd.to_datetime(df_holding.date) 
df_holding = df_holding[(df_holding['date']>= start_date) & (df_holding['date']<= end_date)]

df_holding.sort_values(["date"])

#3. Create unique ID based on rssdhcr+date for both datasets 
#Call data 
# Create a mask for rows where 'rssdhcr' is not 0 and not NaN
mask = (df_call['rssdhcr'] != 0) & (df_call['rssdhcr'].notna())
# Create 'unique_ID' by concatenating 'rssdhcr' and 'date' for rows where 'rssdhcr' is not 0 and not NaN
df_call.loc[mask, 'unique_ID'] = df_call['rssdhcr'].astype(str)  + df_call['date'].astype(str)
df_call.sort_values(["unique_ID"])

#Holding data 
df_holding['unique_ID'] = df_holding[df_holding['rssdhcr'] != 0]['rssdhcr'].astype(str) + df_holding[df_holding['rssdhcr'] != 0]['date'].astype(str)
df_holding.sort_values(["date"])['unique_ID']

#4. Replacing bhc data in call data file with FR-Y9C data 

#We create a dummy for unique ID matches (to remove duplicates later)
df_call['matched'] = df_call['unique_ID'].isin(df_holding['unique_ID']).astype(int)
df_call.sort_values(["unique_ID"])

#Check - manual check of selected columns 
#df_call.sort_values(["date"])[['unique_ID','rssdhcr','assets','agloans','deposits','liabilities']]

#Drop duplicate unique IDs 
#We should remove duplicates at this stage rather than earlier because it is possible that a unique ID exists in call data but does not get matched in FRY9C. 

#We drop duplicates and keep only the first occurence of unique ID/rssdid values
# Separate the DataFrame into two subsets
df_matched_1 = df_call[df_call['matched'] == 1]
df_not_matched_1 = df_call[df_call['matched'] != 1]

# Drop duplicates in the subset where 'matched' == 1 and also merge with FR-Y9C here 
df_matched_1 = df_matched_1.drop_duplicates(subset=['unique_ID'], keep='first')
# Set the 'unique_ID' column as the index for both DataFrames
df_matched_1.set_index('unique_ID', inplace=True)
df_holding.set_index('unique_ID', inplace=True)
# Update the rows in df1 with rows from df2 based on the index
df_matched_1.update(df_holding)
# Reset the index if needed
df_matched_1.reset_index(inplace=True)
df_holding.reset_index(inplace=True)

df_matched_1.sort_values(["date"])
#Checks - there are duplicate unique IDs due to one rssdhcr containing multiple rssdids. 
df_no_nan = df_matched_1.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated()]
duplicates.sort_values(['unique_ID']) #no duplicates


# Combine the filtered subsets back together
df_call = pd.concat([df_matched_1, df_not_matched_1], ignore_index=True)

print(df_call)

#Check 1 - there are duplicate unique IDs due to one rssdhcr containing multiple rssdids. 
df_no_nan = df_call.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated()]
duplicates.sort_values(['unique_ID']) #there will be duplicates - non-matched unique IDs 
#Check 2
filtered_sorted_duplicates = duplicates[duplicates['matched'] == 1]
print(filtered_sorted_duplicates)

#5. Get the list of columns from both DataFrames
columns_df1 = set(df_call.columns)
columns_df2 = set(df_holding.columns)

# Find columns present in df1 but not in df2
columns_in_df1_not_in_df2 = columns_df1 - columns_df2

# Convert the result to a list
columns_in_df1_not_in_df2 = list(columns_in_df1_not_in_df2)
print(columns_in_df1_not_in_df2)

#6. Create a filtered, combined dataframe with only the common columns present in both dfs. 
common_columns = df_call.columns.intersection(df_holding.columns)

common_columns
common_columns=common_columns.union(['rssdid'],sort=False)
common_columns=common_columns.union(['matched'],sort=False)

df_call_filtered = df_call[common_columns]
df_call_filtered

#Cosmetic changes
column_to_move = df_call_filtered.pop("rssdid")
# insert column with insert(location, column_name, column_value)
df_call_filtered.insert(2, "rssdid", column_to_move)

#7. Aggregate line items which have matched == 0 but unique_ID has a value 
#Separate datasets 
df_matched_1 = df_call_filtered[df_call_filtered['matched'] == 1]
df_not_matched_1 = df_call_filtered[df_call_filtered['matched'] != 1 & df_call_filtered['unique_ID'].notna()]

#In not matched dataset, we aggregate on rssdhcr level 
#Check if P&L items are YTD? 
df_no_nan = df_not_matched_1.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated()]
duplicates.sort_values(['unique_ID']) 

df_not_matched_1.head(20)


#8. Plot certain columns to check time series 
# ['assets','deposits','numemployees','agloans','liabilities']
# (['rssdhcr','year'])[['intexpdomdep','salaries','exponpremises']
# Add important variables from BFE regression here and check time series too 




#9. Write file in feather format 
df_call_filtered.to_feather('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/call_FRY9C_consolidated.feather')





