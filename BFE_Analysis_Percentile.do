// BFE regression: Quarter level percentile ranks 


//Import call data (WRDS)
use"/Users/shivani/Documents/GitHub/deposit/data/raw/callreports_1976_2020_WRDS.dta",clear 

 
// Keep selected variables only 
keep bhcid date name assets agloans subordinateddebt equity demanddep transdep ciloans loans loansnet tradingassets securities liabilities deposits nonintbeardep intbeardep tradingliabilities timesavdep timedep timedepuninsured totsavdep numemployees grosstrading netinc intincnet salaries tradingrevenue domdepservicecharges year 

//Ratios calculation 
gen log_assets = log(assets)
gen assets_equity_ratio=assets/equity
gen tradasset_asset_ratio=tradingassets/assets 
gen tradliab_asset_ratio=tradingliabilities/assets 
gen dep_assets_ratio=deposits/assets 
gen agloans_assets_ratio = agloans/assets
gen ciloans_assets_ratio=ciloans/assets 

gen savings_totaldep_ratio=totsavdep/deposits
gen time_totaldep_ratio=timedep/deposits
gen uninstime_timedep_ratio=timedepuninsured/timedep


//Dropping observations to keep time frame consistent with FE data
keep if year > 2000 & year <= 2019
rename  bhcid rssdhcr
merge m:m rssdhcr using "/Users/shivani/BFE_data.dta"
// Dropping observations which are missing 
drop if _merge==1
drop if _merge==2 
drop if rssdhcr==0  

drop dup
drop _merge 


// Percentile rank generation within each quarter, normalisation across years for variable 

ds, has(type numeric)
local vars `r(varlist)'


foreach var of local vars {
    egen `var'_rank = rank(`var'), by(date)
    egen `var'_count = count(`var'), by(date)
    gen `var'_pcrank = 100 * (`var'_rank - 0.5) / `var'_count
    egen `var'_z = std(`var'_pcrank)

}

rename rssdhcr bhcid 

save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_Zscore.dta", replace 

// Add dummy for being large bank 
// Run BFE_analysis.py for adding dummy and import file with dummy added
use"/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_Zscore.dta",clear 

drop index 

save "/Users/shivani/Documents/GitHub/deposit/data/raw/Merged_call_data_Zscore.dta", replace


// Regression 
eststo:  regress  rssdhcr_fe log_assets_z tradasset_asset_ratio_z tradliab_asset_ratio_z dep_assets_ratio_z agloans_assets_ratio_z ciloans_assets_ratio_z savings_totaldep_ratio_z time_totaldep_ratio_z uninstime_timedep_ratio_z Large_Bank, robust 


// esttab using BFE_Analysis_Zscore.tex, replace title("Bank Fixed Effects Regression - Z Score ")
