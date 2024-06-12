#PSID DATA

#Initialising 
rm(list = ls())
options(scipen=99, digits=5)

#Libraries 
library(tidyverse)
library(haven)
library(moments)
library(stargazer)

#Set working directory 
setwd( "/Users/shivani/Documents/SSE Courses/4330 - Macroeconomics and Finance/
       Reserach project references/Data/4330-Research-Project")

#Importing data
Data<-read_dta('1. Input/PSIDSHELF_1968_2019_LONG.dta')

#Reduced columns data
Data_subset_2=Data %>% select(ID:HHID,INCFAMN:INCFAMFR,TOTASSN:TOTASS3FR,
                              WLTHFUNDTOTN:WLTHFUNDIRAFR)
write_csv(Data_subset_2,"Data_subset_2.csv")


#Importing data subset created above
Data_subset_2<-read.csv('1. Input/Data_subset_2.csv')
summary(Data_subset_2)
sum(is.na(Data_subset_2))

#Remove missing values of FID
Data_subset_3<-remove_missing(Data_subset_2,na.rm=TRUE,vars = "FID")
ggplot(Data_subset_3,mapping = aes(x=YEAR))+geom_bar(na.rm = TRUE)+theme_minimal()

ggplot(Data_subset_3,mapping = aes(x=YEAR,y=INCFAMFR))+
  geom_area(na.rm = TRUE)+theme_minimal()


#Remove missing values of Total assets 
Data_subset_4<-remove_missing(Data_subset_2,na.rm=TRUE,vars = c("TOTASSFR","FID"))
ggplot(Data_subset_4,mapping = aes(x=YEAR))+geom_bar(na.rm = TRUE)++theme_minimal()
#Too few observations

#Data grouped by year and FID
Grouped_Income<-Data_subset_3%>%    dplyr::group_by(YEAR,FID)%>%
  summarise(ID=ID, INCFAMFR=mean(INCFAMFR,na.rm = TRUE), INCFAMFN=mean(INCFAMFN, na.rm=TRUE),
            INCFAMN=mean(INCFAMN, na.rm=TRUE),INCFAMR=mean(INCFAMR, na.rm=TRUE))
#Maintaining "ID" of reference person as the unique ID
Grouped_Income <-Grouped_Income %>% dplyr::group_by(YEAR,FID) %>% 
  filter(row_number()==1)
summary(Grouped_Income)

#Removing all missing values and zeros
Grouped_Income<-remove_missing(Grouped_Income,na.rm=TRUE,vars = c("INCFAMFR","INCFAMFN",
                                                                  "INCFAMN","INCFAMR"))
Grouped_Income <- filter_if(Grouped_Income, is.numeric, all_vars((.) != 0))

sum(is.na(Grouped_Income))

#Visualising data
ggplot(Grouped_Income,mapping = aes(x=YEAR,y=INCFAMFR))+geom_point(na.rm = TRUE)+theme_minimal()

#Writing file 
write_csv(Grouped_Income,"Grouped_Income.csv")

## Growth rate, Log income,ln growth rate ##
Grouped_Income<-read.csv("1. Input/Grouped_Income.csv")
#Consecutive value check 
Grouped_Income<-Grouped_Income%>%group_by(ID)%>%
  mutate(deltaLag1 = YEAR - dplyr::lag(YEAR, 1))
Grouped_Income<-Grouped_Income%>%group_by(ID)%>%filter(deltaLag1<3 |is.na(deltaLag1)==TRUE)

#Calculating variables for each year and ID
Grouped_Income<-Grouped_Income%>% group_by(ID)%>%
  mutate(INCFAMFR_log=log(INCFAMFR), #Log variables
         INCFAMFR_FDlog=INCFAMFR_log-dplyr::lag(INCFAMFR_log,1), #ln household income growth
         
         INCFAMFR_lag=dplyr::lag(INCFAMFR,1),    #Non-log variables
         INCFAMFR_delta=INCFAMFR-INCFAMFR_lag,
         INCFAMFR_growth=INCFAMFR_delta/INCFAMFR_lag #Household income growth
  )

#Annualise growth rates of lag = 2 (CAGR)
Grouped_Income$Income_CAGR = (Grouped_Income$INCFAMFR_growth^(1/Grouped_Income$deltaLag1))

#Removing NAs and NaNs (produced due to negative values)
Grouped_Income2<-remove_missing(Grouped_Income,na.rm=TRUE,vars = c("INCFAMFR_log",
                                                                   "INCFAMFR_FDlog","INCFAMFR_lag","INCFAMFR_delta","INCFAMFR_growth","Income_CAGR"))

sum(is.na(Grouped_Income2))

Grouped_Income2<- Grouped_Income2 %>% mutate(ntile = ntile(INCFAMFR, 10))



## Mean, variance, skewness of income growth for each household i at time t ##
Summary_stats<-Grouped_Income2%>% group_by(YEAR)%>%
  summarise(mean=mean(Income_CAGR),sd=sd(Income_CAGR),var=var(Income_CAGR),skewness=
              skewness(Income_CAGR),
            log_mean=mean(INCFAMFR_FDlog),log_SD=sd(INCFAMFR_FDlog),
            log_var=var(INCFAMFR_FDlog),log_skewness= skewness(INCFAMFR_FDlog))

summary(Summary_stats)


## Function for SDF..eqn (1) ##
#Inputs: beta, alpha(RRA), cross-secn mean(g_t),cross-secn variance,cross-secn skewness

SDF<-function(beta,alpha,CS_mean,CS_var,CS_skew){
  
  m<-(beta*(CS_mean^-alpha))*(1+(0.5*alpha*(1+alpha)*CS_var)-
                                (1/6*alpha*(1+alpha)*(2+alpha)*CS_skew))
  return(m)
}

# Create an empty data frame to store results
results_df <- data.frame(alpha = integer(), t = integer(), result = numeric())


for (alpha in 1:10) {
  for(t in 1:40){
  # Call the SDF function and store the result in the df
    result <-SDF(beta=1,alpha=alpha,CS_mean=Summary_stats[t,2],CS_var = Summary_stats[t,4],
                                CS_skew = Summary_stats[t,5]) #non-log data 
    # Append the result to the data frame
    results_df <- rbind(results_df, data.frame(alpha = alpha, t = t, result = result))
    }}

# Access results of m_t
wide_results <- pivot_wider(data = results_df, names_from = t, values_from = mean)



## Returns data ##
library(readxl)
returns_data<-read_xlsx("1. Input/Returns_data.xlsx")

returns_data$Date <- as.Date(paste(returns_data$Date, "01", sep = "."), format = "%Y.%m.%d")
risk_free_rate <- returns_data$monthly_risk_free_rate
monthly_return <- returns_data$monthly_simple_return
gross_return=monthly_return+1
returns_data$Year <- format(returns_data$Date, "%Y")

# Compute the mean risk-free rate for each year
mean_risk_free_rate <- aggregate(risk_free_rate ~ Year, data = returns_data, FUN = mean)

# Compute the variance of 'monthly_return' for each year
compunded_yearly_return <- aggregate(gross_return ~ Year, data = returns_data, FUN = prod)
mean_risk_free_rate$mean_risk_free_rate = 1+ mean_risk_free_rate$risk_free_rate/100

#Compute the equity premium
equity_premium = compunded_yearly_return$gross_return - mean_risk_free_rate$mean_risk_free_rate

#One data set with equity premium and risk free rate
returns_data = data.frame(cbind(mean_risk_free_rate$mean_risk_free_rate,equity_premium))
returns_data$year=1967:2023
returns_data=filter(returns_data,year>=1968 & year<=2019 )
#After 1997, next is 1999 and so on from there (reduce from 52 to 40 obs to be consistent with SDFs)
returns_data1<- filter(returns_data,year>1997)
returns_data1<-filter(returns_data1,year%%2==1)
returns_data2<-filter(returns_data,year<1998)
returns_data2<-rbind(returns_data2,returns_data1)
returns_data2<-filter(returns_data2,year>1968)
#Tag years as 1 to 40 (t)
returns_data2$t<-1:40


## Vector of m*excess returns ## 
# Create an empty data frame to store results
num_rows <- 40 * 10  # Number of iterations
Moment_cond <- data.frame(alpha = numeric(num_rows),
                          t = numeric(num_rows),
                          result = numeric(num_rows))

# Counter variable for row indexing
counter <- 1

# Perform the iterations
for (t in 1:40) {
  for (alpha in 1:10) {
    Moment_condn <- wide_results[alpha, t + 1] * returns_data2[t, 2]
    # Fill the result in the corresponding row of Moment_cond
    Moment_cond[counter, ] <- c(alpha = alpha, t = t, result = Moment_condn)
    # Increment the counter
    counter <- counter + 1
  }
}


## Unexplained premium -  u statistic ## 
#Inputs: T, m_t, Excess returns_t

u_stat<-function(alpha,T,t,R_e){
    u = (wide_results[alpha,t+1]*R_e)/T 
    return(u)
}

# Create an empty data frame to store results
main_results <- data.frame(alpha = integer(), result = numeric())

#Call function and store in data frame
for(t in 1:40){
  for(alpha in 1:10){
main_result<-u_stat(alpha=alpha,T=40,t=t,R_e=returns_data2[t,2])
# Append the result to the data frame
main_results <- rbind(main_results, data.frame(alpha = alpha, result = main_result))
}}


## T test ##
#Define null as u = 0, alternative is non-zero (two-sided test)

#Tests for alphas from 1 to 10 
x=filter(Moment_cond,alpha==1)
test1<-t.test(x,y=NULL,mu=0)

x2=filter(Moment_cond,alpha==2)
test2<-t.test(x2,y=NULL,mu=0)

x3=filter(Moment_cond,alpha==3)
test3<-t.test(x3,y=NULL,mu=0)

x4=filter(Moment_cond,alpha==4)
test4<-t.test(x4,y=NULL,mu=0)

x5=filter(Moment_cond,alpha==5)
test5<-t.test(x5,y=NULL,mu=0)

x6=filter(Moment_cond,alpha==6)
test6<-t.test(x6,y=NULL,mu=0)

x7=filter(Moment_cond,alpha==7)
test7<-t.test(x7,y=NULL,mu=0)

x8=filter(Moment_cond,alpha==8)
test8<-t.test(x8,y=NULL,mu=0)

x9=filter(Moment_cond,alpha==9)
test9<-t.test(x9,y=NULL,mu=0)

x10=filter(Moment_cond,alpha==10)
test10<-t.test(x10,y=NULL,mu=0)

Results_table<-data.frame(alpha = numeric(),
                          statistic = numeric(),
                          p_value = numeric(),
                          stringsAsFactors = FALSE)
#Appending results in one data frame
Results_table<-bind_rows(Results_table, data.frame(
  alpha=1,statistic=test1$statistic,p_value=test1$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=2,statistic=test2$statistic,p_value=test2$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=3,statistic=test3$statistic,p_value=test3$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=4,statistic=test4$statistic,p_value=test4$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=5,statistic=test5$statistic,p_value=test5$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=6,statistic=test6$statistic,p_value=test6$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=7,statistic=test7$statistic,p_value=test7$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=8,statistic=test8$statistic,p_value=test8$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=9,statistic=test9$statistic,p_value=test9$p.value))
Results_table<-bind_rows(Results_table, data.frame(
  alpha=10,statistic=test10$statistic,p_value=test10$p.value))

#Adding unexplained premium to above df and arranging columns
Results_table<-Results_table%>% left_join(main_results,by="alpha")
colnames(Results_table) <- c("Alpha", "t-statistic", "p-value of t-stat","Unexplained premium")
Results_table<- Results_table[, c(4, 1, 2, 3)]



## Latex output ## 
library(knitr)
kable(Results_table, "latex", booktabs = TRUE) 

## Recession regression ##
#NBER monthly recession indicator 
Bus_cycle<-read.csv("1. Input/USREC.csv")
Bus_cycle<-subset(Bus_cycle,DATE>1960)
Bus_cycle$YEAR<-year(Bus_cycle$DATE)

Bus_cycle<-Bus_cycle%>%group_by(YEAR)%>%summarise(tag=ifelse(any(USREC==1),1, 0))
# Merge the two dataframes by the common "Year" column
Bus_cycle <- merge(Bus_cycle, Summary_stats, by = "YEAR")

#Output
lm1<-lm(stand_var~tag,Bus_cycle)
summary(lm1)
stargazer(lm1)

## Recession graph ## 
recessions.df = read.table(textConnection(
  "Peak, Trough
1857-06-01, 1858-12-01
1860-10-01, 1861-06-01
1865-04-01, 1867-12-01
1869-06-01, 1870-12-01
1873-10-01, 1879-03-01
1882-03-01, 1885-05-01
1887-03-01, 1888-04-01
1890-07-01, 1891-05-01
1893-01-01, 1894-06-01
1895-12-01, 1897-06-01
1899-06-01, 1900-12-01
1902-09-01, 1904-08-01
1907-05-01, 1908-06-01
1910-01-01, 1912-01-01
1913-01-01, 1914-12-01
1918-08-01, 1919-03-01
1920-01-01, 1921-07-01
1923-05-01, 1924-07-01
1926-10-01, 1927-11-01
1929-08-01, 1933-03-01
1937-05-01, 1938-06-01
1945-02-01, 1945-10-01
1948-11-01, 1949-10-01
1953-07-01, 1954-05-01
1957-08-01, 1958-04-01
1960-04-01, 1961-02-01
1969-12-01, 1970-11-01
1973-11-01, 1975-03-01
1980-01-01, 1980-07-01
1981-07-01, 1982-11-01
1990-07-01, 1991-03-01
2001-03-01, 2001-11-01
2007-12-01, 2009-06-01
2020-02-01, 2020-04-01"), sep=',',
  colClasses=c('Date', 'Date'), header=TRUE)

recessions.trim = subset(recessions.df, Peak >= min(Bus_cycle$YEAR) )
recessions.trim$Peak=year(recessions.trim$Peak)
recessions.trim$Trough=year(recessions.trim$Trough)
#Generating data on an annual level
recessions.trim$Trough= ifelse(recessions.trim$Trough==recessions.trim$Peak,recessions.trim$Trough+1,recessions.trim$Trough)


#Creating standardised variables
Bus_cycle$stand_var<-(Bus_cycle$var-Bus_cycle$mean)/Bus_cycle$sd

g = ggplot(Bus_cycle) + geom_line(aes(x=YEAR, y=stand_var)) + theme_bw()
g = g+ geom_rect(data=recessions.trim, aes(xmin=Peak, xmax=Trough, 
                              ymin=-Inf, ymax=+Inf), fill='darkgrey', alpha=0.2)+
  labs(x="Year",y="Variance (standardised)",title=" Variance of Household Income Growth in Recessions")+
  theme(text = element_text(family = "Times New Roman"))

print(g)







