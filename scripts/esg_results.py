# -*- coding: utf-8 -*-
"""
@author: Pascal Winter
www.winter-aas.com

Provides simple visualisation of ESG output
Works with DB format ("flat") and Matrix formats

1.DESCRIBE: calculate mean, vol and percentiles
2. GRAPH
    2.0 Graph Selected Sims
    2.1 Graph Mean Returns
    2.2 Graph Percentiles and Mean
EXPORT: export result dashboard
     
    
"""



import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CWD = Path(__file__).resolve().parents[1] # Since we are in a sub-directory

import libpw.esglib as esglib




# ------------------------- Results to be loaded ------------------------------#
name_input = 'RW'
input_type = 'CSV' #  'DB'  'XLSX'    'CSV'
input_funds = ['4p5_9vol', '4p5_8vol', '5p5_9vol', '5p5_8vol', '3p5_9vol', '3p5_8vol'] # only used if type = 'CSV'
i_inputstep_length = 12 # 12: month, 1: year
rn_sim = False 


# ----------------------------- Graph Parameters ------------------------------#
plt_wd = 345 
pal_name = 'Blues_d'
pal = sns.color_palette(pal_name)
#pal = sns.color_palette('YlGnBu')
sns.set_palette(pal)




#%%#############################################################################
#BOOK############################## LOAD #######################################
################################################################################


# -----------------------------------------------------------------------------#
# ------------------------ Load Expected Returns ------------------------------#
# -----------------------------------------------------------------------------#

csv_loadfile_expret = name_input + '_exp_returns.csv' # for the expected returns by funds
dF_Stock_ExpRet = pd.read_csv(list(CWD.rglob(csv_loadfile_expret))[0], index_col = 0)


# -----------------------------------------------------------------------------#
# --------------------------- Load DB formats  --------------------------------#
# -----------------------------------------------------------------------------#

if input_type == 'DB':
    name_input_db =  name_input + '_results.csv' # for DB format
    dF_Stock_Ret = pd.read_csv(list(CWD.rglob(name_input_db))[0])


# -----------------------------------------------------------------------------#
# --------------------------- Load Matrix XLSX --------------------------------#
# -----------------------------------------------------------------------------#
    
if input_type == 'XLSX':
    # get excel file path and prepare map
    name_input_excel = name_input + '_results.xlsx'
    xcel_file = pd.ExcelFile(list(CWD.rglob(name_input_excel))[0])
    # predefine DF for output
    dF_Stock_Ret = pd.DataFrame(columns=['Year', 'Simulation', 'Return', 'Asset'])
    for sheets in xcel_file.sheet_names:
        # Read from excel
        dF_temp = pd.read_excel(xcel_file, sheets, index_col = 0)
        dF_temp['Year'] = dF_temp.index.values / i_inputstep_length # Calculate Year
        # Melt to get a DB format and map the type (ret or val) to get proper column name
        dF_temp = dF_temp.melt(id_vars = 'Year', var_name = 'Simulation', value_name = 'Return')
        dF_temp['Asset'] = sheets # Add Asset Name from sheet name
        # Append
        dF_Stock_Ret =  pd.concat([dF_Stock_Ret, dF_temp], axis=0)
    # Type correctly simulation
    dF_Stock_Ret['Simulation'] = dF_Stock_Ret['Simulation'].astype('int64')

# -----------------------------------------------------------------------------#
# --------------------------- Load Matrix CSV  --------------------------------#
# -----------------------------------------------------------------------------#
    
if input_type == 'CSV':
    # predefine DF for output
    dF_Stock_Ret = pd.DataFrame(columns=['Year', 'Simulation', 'Return', 'Asset'])
    # go through the sheets
    for asset in input_funds:
        name_input_csv = name_input + '_' + asset + '_results.csv'
        dF_temp = pd.read_csv(list(CWD.rglob(name_input_csv))[0], index_col = 0)
        # Calculate Year
        dF_temp['Year'] = dF_temp.index.values / i_inputstep_length
        # Melt to get a DB format and map the type (ret or val) to get proper column name
        dF_temp = dF_temp.melt(id_vars = 'Year', var_name = 'Simulation', value_name = 'Return')
        # Add Asset Name from sheet name
        dF_temp['Asset'] = asset
        # Append
        dF_Stock_Ret =  pd.concat([dF_Stock_Ret, dF_temp], axis=0)
    # Type correctly simulation
    dF_Stock_Ret['Simulation'] = dF_Stock_Ret['Simulation'].astype('int64')
    

# -----------------------------------------------------------------------------#
# --------------------------- Wrangle Data for analysis -----------------------#
# -----------------------------------------------------------------------------#

# -------------------- Calculate Stock Prices ---------------------------------#
dF_Stock_Val = dF_Stock_Ret.copy()
dF_Stock_Val['Return'] = dF_Stock_Val['Return'] + 1
dF_Stock_Val['Return']  = dF_Stock_Val.groupby(['Asset','Simulation']).cumprod()['Return']
dF_Stock_Val = dF_Stock_Val.rename(columns={'Return':'Price'})

# ------------------- Calculate Expected Prices
# Calculate step (ie second lowest year)
i_step = min(dF_Stock_ExpRet['Year'][min(dF_Stock_ExpRet['Year']) != dF_Stock_ExpRet['Year']])
dF_Stock_ExpVal = dF_Stock_ExpRet.copy()
dF_Stock_ExpVal['ExpRet'] = np.power(dF_Stock_ExpVal['ExpRet'] + 1, i_step)
dF_Stock_ExpVal['ExpRet'] = dF_Stock_ExpVal.groupby(['StockName']).cumprod()['ExpRet']
dF_Stock_ExpVal = dF_Stock_ExpVal.rename(columns={'ExpRet':'ExpPrice'})





#%%#############################################################################
#BOOK########################### 1.DESCRIBE ####################################
################################################################################

# -----------------------------------------------------------------------------#
# ---------------- Caluclate Mean, Vol and Percentiles  -----------------------#
# -----------------------------------------------------------------------------#

# ------------------- Define Percentiles --------------------------------------#
l_quantile=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
            0.75, 0.9, 0.95, 0.975, 0.99, 0.995, 0.999]
l_quantile=[0.005, 0.01, 0.05, 0.1, 0.25, 0.50, 0.75, 0.9, 0.95, 0.99, 0.995]

# ------------------- Calculate Global - RETURNS ------------------------------#
# Percentile returns
dF_Global_StockRet = esglib.calculate_percentile(dF_Stock_Ret, ['Asset'], 'Return', l_quantile)
# Mean returns
dF_temp = esglib.calculate_mean(dF_Stock_Ret, ['Asset'], 'Return', l_quantile)
dF_Global_StockRet = dF_Global_StockRet.append(dF_temp)
# Vol returns
dF_temp = esglib.calculate_vol(dF_Stock_Ret, ['Asset'], 'Return', l_quantile, i_inputstep_length)
dF_Global_StockRet = dF_Global_StockRet.append(dF_temp)


# ------------------- Calculate Year - RETURNS --------------------------------#
# Percentile returns
dF_Period_StockRet = esglib.calculate_percentile(dF_Stock_Ret, ['Asset','Year'], 'Return', l_quantile)
# Mean returns
dF_temp = esglib.calculate_mean(dF_Stock_Ret, ['Asset','Year'], 'Return', l_quantile)
dF_Period_StockRet = dF_Period_StockRet.append(dF_temp)
# Annualize Returns
# dF_Period_StockRet['Return'] = np.power(1 + dF_Period_StockRet['Return'], 12 / i_outpoutstep_length) - 1
# Vol returns
dF_temp = esglib.calculate_vol(dF_Stock_Ret, ['Asset','Year'], 'Return', l_quantile, i_inputstep_length)
dF_Period_StockRet = dF_Period_StockRet.append(dF_temp)



# ------------------- Calculate Year - VALUE ----------------------------------#
# Percentile returns
dF_Period_StockVal = esglib.calculate_percentile(dF_Stock_Val, ['Asset','Year'], 'Price', l_quantile)
# Mean returns
dF_temp = esglib.calculate_mean(dF_Stock_Val, ['Asset','Year'], 'Price', l_quantile)
dF_Period_StockVal = dF_Period_StockVal.append(dF_temp)







#%%#############################################################################
#BOOK############################## 2.GRAPH ####################################
################################################################################

# -----------------------------------------------------------------------------#
# -------------------- 2.0 Graph Selected Sims  -------------------------------#
# -----------------------------------------------------------------------------#

# ----------------------------- Settings --------------------------------------#
lassets = list(dF_Stock_Ret['Asset'].unique())
nassets = len(lassets)
num_sim_shown = 10

fig, axes = plt.subplots(nassets, 1, figsize=esglib.set_size(plt_wd, nassets, 1),
                         sharex=True, sharey = 'col')

# Select Mean by Asset and Year
dF_temp = dF_Stock_Val.loc[dF_Stock_Val['Simulation'] < num_sim_shown]
pal_temp = sns.diverging_palette(240, 240, n=num_sim_shown)

for i, asset in enumerate(lassets):
    dF_temp2 = dF_temp.loc[dF_temp['Asset'] == asset]
    sns.lineplot(data=dF_temp2, x='Year', y='Price', hue='Simulation',
                     ax=axes[i], palette = pal_temp, legend = False)

# ----------------------------- Graph Cosmetics -------------------------------#
# Remove the border
sns.despine()
# Adjust space inbetween columns
fig.subplots_adjust(wspace = 0.3)

# Add the Y Axis titles
for i, asset in enumerate(lassets):
    axes[i].set_ylabel(asset)
    axes[i].set_yscale('log')

spath = list(CWD.rglob(csv_loadfile_expret))[0].parent.as_posix() + "/" + name_input + '_1.png'
fig.savefig(spath)




#%% ---------------------------------------------------------------------------#
# -------------------- 2.1 Graph Mean Returns vs Expected ---------------------#
# -----------------------------------------------------------------------------#

# ----------------------------- Settings --------------------------------------#
lassets = list(dF_Stock_Ret['Asset'].unique())
nassets = len(lassets)
fig, axes = plt.subplots(nassets, 2, figsize=esglib.set_size(plt_wd, nassets, 2),
                         sharex=True)


# --------------------------- 1st Row: Mean Return ----------------------------#
# Select Mean by Asset and Year
dF_temp = dF_Period_StockRet.reset_index()
cond = dF_temp['Indicator'] == 'Mean'
dF_temp = dF_temp.loc[cond] # Select mean
# Annualise mean for consistent comparison
dF_temp['Return'] = np.power(1 + dF_temp['Return'], i_inputstep_length) - 1

for i, asset in enumerate(lassets):
    dF_temp2 = dF_temp.loc[dF_temp['Asset'] == asset]
    dF_temp3 = dF_Stock_ExpRet.loc[dF_Stock_ExpRet['StockName'] == asset]
    sns.lineplot(data=dF_temp2, x='Year', y='Return', ax=axes[i, 0], color=pal[0])
    sns.lineplot(data=dF_temp3, x='Year', y='ExpRet', ax=axes[i, 0], color=pal[5])


# --------------------------- 2nd Row: Mean Values ----------------------------#
# Select Mean by Asset and Year
dF_temp = dF_Period_StockVal.reset_index()
cond = dF_temp['Indicator'] == 'Mean'
dF_temp = dF_temp.loc[cond] # Select mean

for i, asset in enumerate(lassets):
    dF_temp2 = dF_temp.loc[dF_temp['Asset'] == asset]
    dF_temp3 = dF_Stock_ExpVal.loc[dF_Stock_ExpVal['StockName'] == asset]
    sns.lineplot(data=dF_temp2, x='Year', y='Price', ax=axes[i, 1], color=pal[0])
    sns.lineplot(data=dF_temp3, x='Year', y='ExpPrice', ax=axes[i, 1], color=pal[5])


# ----------------------------- Graph Cosmetics -------------------------------#
# Remove the border
sns.despine()
# Adjust space inbetween columns
fig.subplots_adjust(wspace = 0.3)

# Add the Y Axis titles
for i, asset in enumerate(lassets):
    axes[i,0].set_ylabel(asset)
    # Set percentage for returns
    axes[i,0].yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))


spath = list(CWD.rglob(csv_loadfile_expret))[0].parent.as_posix() + "/" + name_input + '_2.png'
fig.savefig(spath)


#%% ---------------------------------------------------------------------------#
# -------------------- 2.2 Graph Percentiles and Mean  ------------------------#
# -----------------------------------------------------------------------------#

# ----------------------------- Settings --------------------------------------#
lassets = list(dF_Stock_Ret['Asset'].unique())
nassets = len(lassets)
pal_temp = sns.diverging_palette(240, 240, n=len(l_quantile))
fig, axes = plt.subplots(nassets, 3, figsize=esglib.set_size(plt_wd, nassets, 3),
                         sharex=True, sharey='col')

# ---------------- 1st  Column: Price overview ----------
# Calculate quantiles by Asset and Year
dF_temp = dF_Period_StockVal.reset_index()
cond_1 = dF_temp['Indicator'] != 'Mean'
cond_2 = dF_temp['Indicator'] == 'Mean'
dF_temp1 = dF_temp.loc[cond_1] # Select percentile
dF_temp2 = dF_temp.loc[cond_2] # Select mean
# Graphing
for i, asset in enumerate(lassets):
    dF_temp3 = dF_temp1.loc[dF_temp['Asset'] == asset]
    dF_temp4 = dF_temp2.loc[dF_temp2['Asset'] == asset]
    sns.lineplot(data=dF_temp3, x='Year', y='Price',hue='Indicator', ax=axes[i,0],
              palette=pal_temp, legend=False)
    sns.lineplot(data=dF_temp4, x='Year', y='Price', ax=axes[i,0], color=pal[0])
    # Styling curves
    #for j, curves in enumerate(l_quantile):
    #    axes[i,0].lines[j].set_linestyle("--")

# ---------------- 2nd  Column: Return overview ----------
# Calculate quantiles by Asset and Year
dF_temp = dF_Period_StockRet.reset_index()
cond_1 = dF_temp['Indicator'] != 'Mean'
cond_1b = dF_temp['Indicator'] != 'Vol'
cond_2 = dF_temp['Indicator'] == 'Mean'
dF_temp1 = dF_temp.loc[cond_1 & cond_1b] # Select percentile
dF_temp2 = dF_temp.loc[cond_2] # Select mean
# Graphing
for i, asset in enumerate(lassets):
    dF_temp3 = dF_temp1.loc[dF_temp1['Asset'] == asset]
    dF_temp4 = dF_temp2.loc[dF_temp2['Asset'] == asset]
    sns.lineplot(data=dF_temp3, x='Year', y='Return',hue='Indicator', ax=axes[i,1],
              palette=pal_temp, legend=False)
    sns.lineplot(data=dF_temp4, x='Year', y='Return', ax=axes[i,1], color=pal[0])
    # Styling curves
    #for j, curves in enumerate(l_quantile):
    #axes[i,1].lines[j].set_linestyle("--")


# ---------------- 3rd  Column: Volatility ----------
# Calculate quantiles by Asset and Year
dF_temp = dF_Period_StockRet.reset_index()
cond_1 = dF_temp['Indicator'] == 'Vol'
dF_temp1 = dF_temp.loc[cond_1] # Select vol
# Graphing
for i, asset in enumerate(lassets):
    dF_temp2 = dF_temp1.loc[dF_temp['Asset'] == asset]
    sns.lineplot(data=dF_temp2, x='Year', y='Return', ax=axes[i,2], color=pal[0])


# ----------------------------- Graph Cosmetics -------------------------------#
# Remove the border
sns.despine()
# Adjust space inbetween columns
fig.subplots_adjust(wspace = 0.3)

# Add the Y Axis titles
for i, asset in enumerate(lassets):
    axes[i,0].set_ylabel(asset)
    axes[i,1].set_ylabel("")
    axes[i,2].set_ylabel("")
    # Set logscale for Values
    axes[i,0].set_yscale('log')
    # Set percentage for returns
    axes[i,1].yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
    axes[i,2].yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))

axes[0,0].set_title('Asset Price')
axes[0,1].set_title('Asset Return')
axes[0,2].set_title('Asset Volatility')
  
spath = list(CWD.rglob(csv_loadfile_expret))[0].parent.as_posix() + "/" + name_input + '_3.png'
fig.savefig(spath)



#%%#############################################################################
############################## EXPORT  #########################################
################################################################################


#--------------------------  Output the results -------------------------------#
spath = list(CWD.rglob(csv_loadfile_expret))[0].parent.as_posix() + "/" + name_input + '_analysis.xlsx'


print('Exporting Results to Excel...')
# Setup excel writer
writer = pd.ExcelWriter(spath, engine='xlsxwriter') 
# Write Files - Single Simulation
dF_Global_StockRet.to_excel(writer, sheet_name='Global_Stock', freeze_panes=(1,1))
dF_Period_StockVal.unstack(level="Year").to_excel(writer, sheet_name='Year_Stock_Val', freeze_panes=(1,1))
dF_Period_StockRet.unstack(level="Year").to_excel(writer, sheet_name='Year_Stock_Ret', freeze_panes=(1,1))
# Close writer
writer.save()

