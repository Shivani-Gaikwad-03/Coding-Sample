# For adding large bank dummy to WRDS call data 

from folder_structure.code.Convert_to_JSON import add_large_bank_indicator
import pandas as pd
import json

#Import WRDS subsetted data 
Merged_call_data = pd.read_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data.dta')

#Import and create large bank entity code list 
with open('/Users/shivani/Documents/GitHub/deposit/folder_structure/code/largebhc.json','r') as user_file:
  bhclist=json.load(user_file) 

bhclist= pd.DataFrame(bhclist)

# Create an indicator for large banks - entity number which is the RSSD ID
bhc_entity= bhclist.entity.to_list()

#Add the dummy variable 
Merged_call_data  = add_large_bank_indicator(Merged_call_data,'bhcid',bhc_entity)

#Save file 
Merged_call_data.to_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data.dta')


# For adding large bank dummy to WRDS call data - Bank year level 

from folder_structure.code.Convert_to_JSON import add_large_bank_indicator
import pandas as pd
import json

#Import WRDS subsetted data 
Merged_call_data = pd.read_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_2.dta')

#Import and create large bank entity code list 
with open('/Users/shivani/Documents/GitHub/deposit/folder_structure/code/largebhc.json','r') as user_file:
  bhclist=json.load(user_file) 

bhclist= pd.DataFrame(bhclist)

# Create an indicator for large banks - entity number which is the RSSD ID
bhc_entity= bhclist.entity.to_list()

#Add the dummy variable 
Merged_call_data  = add_large_bank_indicator(Merged_call_data,'bhcid',bhc_entity)

#Save file 
Merged_call_data.to_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_2.dta')



# For adding large bank dummy to WRDS call data - Z score version  

from folder_structure.code.Convert_to_JSON import add_large_bank_indicator
import pandas as pd
import json

#Import WRDS subsetted data 
Merged_call_data = pd.read_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_Zscore.dta')

#Import and create large bank entity code list 
with open('/Users/shivani/Documents/GitHub/deposit/folder_structure/code/largebhc.json','r') as user_file:
  bhclist=json.load(user_file) 

bhclist= pd.DataFrame(bhclist)

# Create an indicator for large banks - entity number which is the RSSD ID
bhc_entity= bhclist.entity.to_list()

#Add the dummy variable 
Merged_call_data  = add_large_bank_indicator(Merged_call_data,'bhcid',bhc_entity)

#Save file 
Merged_call_data.to_stata('/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_Zscore.dta')


# For adding large bank dummy to FRY9C data
from folder_structure.code.Convert_to_JSON import add_large_bank_indicator
import pandas as pd
import json

#Import FRY9C data (millions)
FRY9C = pd.read_stata('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/raw/FRY9C.dta')

#Import and create large bank entity code list 
with open('/Users/shivani/Documents/GitHub/deposit/folder_structure/code/largebhc.json','r') as user_file:
  bhclist=json.load(user_file) 

bhclist= pd.DataFrame(bhclist)

# Create an indicator for large banks - entity number which is the RSSD ID
bhc_entity= bhclist.entity.to_list()

#Add the dummy variable 
FRY9C  = add_large_bank_indicator(FRY9C,'rssdid',bhc_entity)

#Save file 
FRY9C.to_stata('/Users/shivani/Documents/GitHub/deposit/folder_structure/data/raw/FRY9C.dta')

