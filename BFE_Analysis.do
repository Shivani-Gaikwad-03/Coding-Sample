//Bank Fixed Effects Analysis

cd

//Step 1: Import FE data
import delimited "/Users/shivani/Documents/GitHub/deposit/data/estimates/result_data_bhc.csv", clear

// Reduce the dataset to two columns with rssdhcr and rssdhcr_fe and remove any duplicates.

keep rssdhcr rssdhcr_fe 
sort rssdhcr
quietly by rssdhcr: gen dup = cond(_N==1,0,_n)
drop if dup>1
drop dup
save BFE_data.dta, replace


//Step 2: Import call data (WRDS)
use"/Users/shivani/Documents/GitHub/deposit/data/raw/callreports_1976_2020_WRDS.dta",clear 

 
// Keep selected variables only 
keep bhcid date name assets agloans subordinateddebt equity demanddep transdep ciloans loans loansnet tradingassets securities liabilities deposits nonintbeardep intbeardep tradingliabilities timesavdep timedep timedepuninsured totsavdep numemployees grosstrading netinc intincnet salaries tradingrevenue domdepservicecharges year 

drop if bhcid==0

// Collapse the dataset (mean for BS items, sum for P&L items)
collapse (mean) assets agloans subordinateddebt equity demanddep transdep ciloans loans loansnet tradingassets securities liabilities deposits nonintbeardep intbeardep tradingliabilities timesavdep timedep timedepuninsured totsavdep numemployees  (sum) grosstrading netinc intincnet salaries tradingrevenue domdepservicecharges, by (bhcid year)

//Ratios calculation 
gen log_assets = log(assets)
gen assets_equity_ratio=assets/equity
gen tradingassets_assets_ratio=tradingassets/assets 
gen tradingliab_assets_ratio=tradingliabilities/assets 
gen dep_assets_ratio=deposits/assets 
gen agloans_assets_ratio = agloans/assets
gen ciloans_assets_ratio=ciloans/assets 

gen savings_totaldep_ratio=totsavdep/deposits
gen time_totaldep_ratio=timedep/deposits
gen uninsuredtime_timedep_ratio=timedepuninsured/timedep
// Capital ratio and Leverage ratio pending 


//Plot of banks/year 2001-2019 (DO NOT run next 25 lines till line 70 for the main regression)
keep if year > 2000 & year <= 2019
rename  bhcid rssdhcr
graph bar (count) rssdhcr, over(year)
merge m:m rssdhcr using "/Users/shivani/BFE_data.dta"
// Dropping observations which are missing 
drop if _merge==1
drop if _merge==2 
//Save data 
rename rssdhcr bhcid 
save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_2.dta", replace

// Add dummy for being large bank 
// Run BFE_analysis.py for adding dummy and import file with dummy added
use"/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_2.dta",clear 

drop index 

save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_2.dta", replace

// regression (bank-year level)
// Multivariate regressions: ratios 
eststo: regress rssdhcr_fe log_assets tradingassets_assets_ratio tradingliab_assets_ratio dep_assets_ratio agloans_assets_ratio ciloans_assets_ratio savings_totaldep_ratio time_totaldep_ratio uninsuredtime_timedep_ratio Large_Bank 

// esttab using BFE_Analysis_bankyear.tex, replace title("Bank Fixed Effects Regression")



// Average across time 
collapse (mean) assets agloans subordinateddebt equity demanddep transdep ciloans loans loansnet tradingassets securities liabilities deposits nonintbeardep intbeardep tradingliabilities timesavdep timedep timedepuninsured totsavdep numemployees grosstrading netinc intincnet salaries tradingrevenue domdepservicecharges log_assets assets_equity_ratio tradingassets_assets_ratio tradingliab_assets_ratio dep_assets_ratio agloans_assets_ratio ciloans_assets_ratio savings_totaldep_ratio time_totaldep_ratio uninsuredtime_timedep_ratio, by (bhcid)


save "/Users/shivani/Documents/GitHub/deposit/data/raw/Call_data_subset.dta", replace


//Step 3: Import cleaned branch level data (2001 to 2019)
import delimited "/Users/shivani/Documents/GitHub/deposit/data/clean/call.csv", clear

// Average number of branches per rssdhcr (as per uninumbr)
drop if uninumbr == .
collapse (count) uninumbr , by (rssdhcr year)
collapse (mean) uninumbr, by (rssdhcr)

// Rename column
rename rssdhcr bhcid 
rename uninumbr branch_num

// Merge with Call_data_subset 
merge 1:1 bhcid using "/Users/shivani/Documents/GitHub/deposit/data/raw/Call_data_subset.dta"
// mismatch possibly due to WRDS dataset being from 1976 (more observations)


// Dropping observations to keep data from 2001-2019 
drop if _merge==1
drop if _merge==2 

// number of employees per branch (again yearly average)
gen avg_employees_perbranch = numemployees/branch_num


save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data.dta", replace

// Add dummy for being large bank 
// Run BFE_analysis.py for adding dummy and import file with dummy added
use"/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data.dta",clear 

drop index 

save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data.dta", replace


// Step 4: Merge the dataset with BFE
// Rename column
rename  bhcid rssdhcr
drop _merge 

//Merge the dataset with BFE
merge 1:1 rssdhcr using "/Users/shivani/BFE_data.dta"
// Drop missing observations 
drop if _merge==1
drop if _merge==2




// Step 5: Run regressions 
// Multivariate regressions: ratios 
eststo: regress rssdhcr_fe log_assets tradingassets_assets_ratio tradingliab_assets_ratio dep_assets_ratio agloans_assets_ratio ciloans_assets_ratio savings_totaldep_ratio time_totaldep_ratio uninsuredtime_timedep_ratio Large_Bank


esttab using BFE_Analysis.tex, replace title("Bank Fixed Effects Regression")



// Extra
// Multivariate regressions 
regress rssdhcr_fe branch_num log_assets agloans equity demanddep transdep deposits ciloans loans tradingassets liabilities tradingliabilities Large_Bank avg_employees_perbranch

// Univariate regressions 
ds
local vars `r(varlist)'

foreach var of local vars {
    regress rssdhcr_fe `var'
     
}


