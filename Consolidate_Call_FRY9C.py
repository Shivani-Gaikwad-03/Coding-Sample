### Combining the Call data and FR-Y9C data ###

import pandas as pd

########
# Read the Call data feather file (1986 to 2019)
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
# Create df_not_matched_1 based on the condition
df_not_matched_1 = df_call_filtered[(df_call_filtered['matched'] != 1) & (df_call_filtered['unique_ID'].notna())]

# Create df_remaining by excluding rows that are in df_not_matched_1
df_remaining = df_call_filtered[~df_call_filtered.index.isin(df_not_matched_1.index)]

#In not matched dataset, we aggregate on rssdhcr level 
#We are adding variables unique to one time period but across banks (addition is appropriate for both P&L and BS items)
df_no_nan = df_not_matched_1.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated(keep=False)]
duplicates.sort_values(['unique_ID']) 
duplicates[duplicates['unique_ID'] == '1020920.01995-12-31']

df_not_matched_1[df_not_matched_1['unique_ID'] == '1020920.01995-12-31']
df_not_matched_1[df_not_matched_1['unique_ID'] == '1020395.01990-03-31']

df_not_matched_1.head(20)

#Creating a dictionary for agg function 
# Columns for which we need to use 'first'
first_columns = ['unique_ID','chartertype', 'rssdid', 'rssdhcr','date','year', 'month', 'quarter', 'day', 'dateq']

# All columns in the DataFrame
all_columns = df_not_matched_1.columns.tolist()
all_columns

# Reset index if 'unique_ID' is an index level
df_not_matched_1 = df_not_matched_1.reset_index(drop=True)

# Dictionary to hold column:agg_function pairs
agg_dict = {col: 'sum' for col in all_columns if col not in first_columns}
for col in first_columns:
    agg_dict[col] = 'first'


# Group by unique ID using dictionary created above 
df_not_matched_agg = df_not_matched_1.groupby('unique_ID').agg(agg_dict)
df_not_matched_agg
df_not_matched_agg = df_not_matched_agg.reset_index(drop=True)

#Check for duplicates
df_no_nan = df_not_matched_agg.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated(keep=False)]
duplicates.sort_values(['unique_ID']) #No duplicates 
#Checks 
df_not_matched_agg[df_not_matched_agg['unique_ID'] == '1020920.01995-12-31'] #had multiple rssdids previously 
df_not_matched_agg[df_not_matched_agg['unique_ID'] == '1020395.01990-03-31']


#Combine the two datasets 
df_consolidated_final = pd.concat([df_remaining, df_not_matched_agg], ignore_index=True)
df_consolidated_final
df_consolidated_final.info()

#Duplicate check 
df_no_nan = df_consolidated_final.dropna(subset=['unique_ID'])
duplicates = df_no_nan[df_no_nan['unique_ID'].duplicated(keep=False)]
duplicates.sort_values(['unique_ID']) #no duplicates 

#8. Write file in feather format 
df_consolidated_final.to_feather('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/call_FRY9C_consolidated.feather')
#df_consolidated_final = pd.read_feather('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/call_FRY9C_consolidated.feather')
#df_consolidated_final.to_stata('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/clean/call_FRY9C_consolidated.dta')


#9. Plot certain columns to check time series 
# ['assets','deposits','numemployees','agloans','liabilities']
# (['rssdhcr','year'])[['intexpdomdep','salaries','exponpremises']
# check timedep, savingsdep and transactiondep for A1 figures 

#Create time series (consolidation of data over quarters)
df_consolidated_final = df_consolidated_final.groupby('date').agg(agg_dict)
df_consolidated_final


#Plot 
import matplotlib.pyplot as plt

# List of variables to plot
variables = ['assets', 'deposits','timedep','totsavdep','transdep','agloans','liabilities','intexpdomdep','salaries','numemployees','exponpremises','equity']
# Determine the number of subplots
num_vars = len(variables)

# Create a figure and a set of subplots
fig, axes = plt.subplots(4, 3, figsize=(16, 3*4), sharex=True)

# Ensure axes is always iterable
if num_vars == 1:
    axes = [axes]

# Plotting each variable in a separate subplot
for i, variable in enumerate(variables):
    row = i // 3  # Calculate the row index
    col = i % 3  # Calculate the column index
    axes[row, col].plot(df_consolidated_final.index, df_consolidated_final[variable], label=f'Variable {variable}')
    axes[row, col].set_title(f'Time Series of {variable}')
    axes[row, col].set_ylabel('Value')
    axes[row, col].legend()
    axes[row, col].grid(True)
    
    # Calculate rolling mean and rolling standard deviation
    rolling_mean = df_consolidated_final[variable].rolling(window=4).mean()  #4 quarters window 
    rolling_std = df_consolidated_final[variable].rolling(window=4).std()
    
    # Compute upper and lower bounds of the 2 rolling SD interval
    upper_bound = rolling_mean + 2 * rolling_std
    lower_bound = rolling_mean - 2 * rolling_std
    
    # Plot rolling mean and 2 rolling SD interval
    axes[row, col].plot(df_consolidated_final.index, rolling_mean, label='Rolling Mean', color='red')
    axes[row, col].fill_between(df_consolidated_final.index, lower_bound, upper_bound, color='gray', alpha=0.3, label='2 SD Interval')
    axes[row, col].legend()


# Set the x-axis label for the bottom subplot
axes[-1, 0].set_xlabel('Date')

# Adjust layout to prevent overlap
plt.tight_layout()

# Display the plot
plt.show()


#Selected variables comments 
df_consolidated_final['numemployees'].head(20)
#1990-09-30 has an incorrect entry for rssdid 1133736 which results in the spike 

