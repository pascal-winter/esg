
# -*- coding: utf-8 -*-
"""
@author: Pascal Winter
www.winter-aas.com
"""

import pandas as pd
import numpy as np

import libpw.esglib as esglib

from pathlib import Path
CWD = Path(__file__).parent

'''
--------------------------- Further work to be done ---------------------------
Interest model
Optimisation on append + Numpyfication for speed


----------------------------------- Content -----------------------------------
0. PARAMETERS / INITITIALISATION
1. RANDOM NUMBER GENERATION
2. STOCK MODEL - B&S
3. INTEREST RATE MODEL - CIR 

----------------------------------- Inputs ------------------------------------
Correlation starts with stocks then rates



----------------------------------- Outputs -----------------------------------
Stock Model: 
    => output_type
        - 'DB': Return a csv files in a DB format with fields ['Asset', 'Simulation', 'Year', Return]
        - 'XLSX': Return a xlsx files with several sheets (one per Asset) and format [Time * Simulation]
        - 'CSV': Return several CSV file (one per asset ) and format [Time * Simulation]
    => output_field
    
    
'''
# -----------------------------------------------------------------------------#
# ------------------------------- Options -------------------------------------#
# -----------------------------------------------------------------------------#

# --------------------- Simulation Parameters ---------------------------------#
i_num_sim = 5000 #10000
i_num_steps = 55 + 5 + 5 # projection year
i_step_length = 48 # Step Per years (in calculation)
d_deltaT = 1 / i_step_length
# ------ Ouptut
i_outpoutstep_length = 12 # 12: month, 1: year
output_type = 'CSV' #   'DB'   'XLSX'   'CSV'


# --------------------- Random Generation -------------------------------------#
seed_rand = True
seed_val = 453624

# --------------------- Technical ---------------------------------------------#
rn_sim = False # if True, asset return will be the yield curve minus div yield

# ---------------------- Files Path -------------------------------------------#
# Input
excel_parameters = 'RW_param.xlsx' 
# Outputs
name_output = 'RW'






#%%#############################################################################
########################## 0. PARAMETERS / INITI ###############################
################################################################################
 

# --------------------- Load tables Parameters --------------------------------#
xcel_file = pd.ExcelFile(list(CWD.rglob(excel_parameters))[0])
dF_StockParam = pd.read_excel(xcel_file, 'Stock_Param', index_col = 0)
dF_IntParam = pd.read_excel(xcel_file, 'Int_Param', index_col = 0)
dF_YieldCurve = pd.read_excel(xcel_file, 'Yield_Curve', index_col = 0)
nA_Correlation = pd.read_excel(xcel_file, 'Correlation', header = None)
nA_Correlation = nA_Correlation.to_numpy()


# Check consistency
dF_Test = pd.DataFrame(columns = ['Name','Val1','Val2'])
i_num_assets = dF_StockParam.shape[0] + dF_IntParam.shape[0]
dF_Test.loc[dF_Test.shape[0]] = ['Import - Correl Matrix Size', nA_Correlation.shape[0],
            dF_StockParam.shape[0] + dF_IntParam.shape[0]]


# --------------------------- Global variables --------------------------------#
# Define Indexes to be used throughout the simulation
l_asset = list(dF_StockParam.index) + list(dF_IntParam.index)
l_stocks = list(dF_StockParam.index)
l_simulation = list(np.arange(0, i_num_sim))
# Define time steps to be used
i_step_modulo = i_step_length // i_outpoutstep_length # modulo for extraction output
l_step_out = list(np.arange(0, i_step_length * i_num_steps + 1, i_step_modulo)) # selected steps for extraction
# Steps for indexes
l_step_year = list(np.arange(0, i_step_length * i_num_steps, i_step_modulo) * d_deltaT ) # selected steps for extraction
l_step_year2 = list(np.arange(0, i_step_length * i_num_steps + 1, i_step_modulo) * d_deltaT ) # selected steps for extraction


# Define Stock Indexes
Stock_index = pd.MultiIndex.from_product([l_simulation, l_step_year, l_stocks],
                                         names=[ 'Simulation', 'Year', 'Asset'])
Stock_index2 = pd.MultiIndex.from_product([l_simulation, l_step_year2, l_stocks],
                                         names=[ 'Simulation', 'Year', 'Asset'])


# ------------------------ Get fowrards from spot rate ------------------------#
# Prepare: reset index and get step length
dF_YieldCurve = dF_YieldCurve.reset_index()
dF_YieldCurve['Step'] = dF_YieldCurve['Year'].diff(1).fillna(0)
# Get the Total Return and divide it by the previous step
dF_temp2 = np.power(1 +  dF_YieldCurve['Spot'], dF_YieldCurve['Year'])
dF_temp2 = dF_temp2 / dF_temp2.shift(1)
# Re-adjust with the step and take off one
dF_YieldCurve['Forward'] = np.power(dF_temp2, 1 / dF_YieldCurve['Step'] ) - 1
dF_YieldCurve['Forward']  = dF_YieldCurve['Forward'].fillna(method = 'bfill')
# Restore Index
dF_YieldCurve = dF_YieldCurve.set_index('Year')


# --------------------- Align Yield Curve on time frame -----------------------#
# with interpolation
tindex = np.linspace(0,  dF_YieldCurve.index.max(), int(i_step_length * dF_YieldCurve.index.max() + 1))
dF_YC_Aligned =  dF_YieldCurve.reindex(tindex)
dF_YC_Aligned = dF_YC_Aligned.interpolate(method = 'linear' )
dF_YC_Aligned = dF_YC_Aligned[:i_num_steps].iloc[:-1] # trim to get same size
dF_YC_Aligned = dF_YC_Aligned.reset_index()




#%%#############################################################################
####################### 1. RANDOM NUMBER GENERATION  ###########################
################################################################################
# Creates a nA of size Sim * Time * Asset

# -----------------------------------------------------------------------------#
# ----------------Create the random numbers with a normal distribution --------#
# -----------------------------------------------------------------------------#

# Initialise mean and covariance
mean = [0] * i_num_assets 
cov = nA_Correlation
# Seed the random number generator
if seed_rand == True: np.random.seed(seed_val)
# Generate the Random multivariate vector (size: ( Time * Sim) * Asset)
nA_Multvar = np.random.multivariate_normal(mean, cov, 
                        size=(i_step_length * i_num_steps  *i_num_sim))
# Reshape as an Sim * Time * Asset array
nA_Multvar = nA_Multvar.reshape(i_num_sim, i_step_length * i_num_steps, i_num_assets)





#%%#############################################################################
############################# 2. STOCK MODEL - B&S  ############################
################################################################################

# -----------------------------------------------------------------------------#
# ------------------ Initialise for the stock calculation  --------------------#
# -----------------------------------------------------------------------------#

l_stocks = list(dF_StockParam.index) 
n_stocks = len(l_stocks)
nA_Multvar2 = nA_Multvar[:, :, 0:n_stocks] # Slice the Multvar for further calculation

nA_StockBS = np.zeros( shape = nA_Multvar2.shape, dtype = 'float32')


# -----------------------------------------------------------------------------#
# ------------------ Calculate the B/S returns --------------------------------#
# -----------------------------------------------------------------------------#

# ------------------------ Calculate the 1st BS Term --------------------------#
# Apply the forward curves if this is RN, assumed returns if RW
if rn_sim == True: 
    nA_StockBS = np.add(nA_StockBS, dF_YC_Aligned['Forward'][None, :, None])
else:
    nA_StockBS = np.add(nA_StockBS, dF_StockParam['Return'][None, None, :])
# Apply the dividends
nA_StockBS = np.subtract(nA_StockBS, dF_StockParam['Dividend'][None, None, :])
# Lognormalise
nA_StockBS = np.log(1 + nA_StockBS)
# Substract the volatility term
nA_temp = np.square(dF_StockParam['Volatility']) / 2
nA_StockBS = np.subtract(nA_StockBS, nA_temp[None, None, :])
# Multiply by DeltaT
nA_StockBS = nA_StockBS * d_deltaT

# ------------------------ Calculate the 2nd BS Term --------------------------#
# Multiply the multivariate term with the vol
nA_Multvar2 = np.multiply(nA_Multvar2, dF_StockParam['Volatility'][None, None, :])
# Scale by Sqrt of DeltaT
nA_Multvar2 = nA_Multvar2 * np.sqrt(d_deltaT)
# Add 1st and 2nd term
nA_StockBS = nA_StockBS + nA_Multvar2
# Exponentialise
nA_StockBS = np.exp(nA_StockBS)



# -----------------------------------------------------------------------------#
# ------------------------ Wrangle the data for output ------------------------#
# -----------------------------------------------------------------------------#

# -------- Calculate Value and extract Value and Returns at output step  ------#
# Insert first value and add 1 to all returns
nA_StockBS_Val = np.insert(nA_StockBS, 0, 1.0, axis = 1)
# Cumulative Product to get Value
nA_StockBS_Val = nA_StockBS_Val.cumprod(axis=1)
# Select only the output steps
nA_StockBS_Val_Out = nA_StockBS_Val[:, l_step_out, :]
# Calculate the Output Steps returns
nA_StockBS_Ret_Out = nA_StockBS_Val_Out[:, 1:, :] / nA_StockBS_Val_Out[:, :-1, :] - 1



# ------------------------- Reshape on a DB format for output -----------------#
# flatten numpy as 1 dimension and pass it as a dataframe
dF_StockBS_Val_Out = pd.DataFrame(nA_StockBS_Val_Out.flatten(), 
                                  index = Stock_index2, columns = ['Price'])


dF_StockBS_Ret_Out = pd.DataFrame(nA_StockBS_Ret_Out.flatten(), 
                                  index = Stock_index, columns = ['Return'])






#%%#############################################################################
########################## 2. INTEREST RATE MODEL ##############################
################################################################################

# TO BE DEVELOPPED







#%%#############################################################################
################################  TEST  ########################################
################################################################################

#----------------------- Print the test dF ------------------------------------#
dF_Test['Diff'] = dF_Test['Val1'] - dF_Test['Val2']
dF_Test['Result'] = abs(dF_Test['Diff']) > 0.00000001
print(dF_Test)




################################################################################
######################### EXPORT & TEST ########################################
################################################################################



# -----------------------------------------------------------------------------#
#---------------------  Export results - DB -----------------------------------#
# -----------------------------------------------------------------------------#


if output_type == 'DB':
    print('Exporting DB to csv...')
    # Export Returns
    spath = list(CWD.rglob(excel_parameters))[0].parent.as_posix() + "/" + name_output + '_results.csv'
    dF_StockBS_Ret_Out.to_csv(spath)


# -----------------------------------------------------------------------------#
#---------------------  Export results - Matrix - XLSX ------------------------#
# -----------------------------------------------------------------------------#
# Format Time * Simulation

if output_type == 'XLSX':
    print('Exporting Results to Excel...')
    # Setup excel writer
    spath = list(CWD.rglob(excel_parameters))[0].parent.as_posix() + "/" + name_output + '_results.xlsx'
    writer = pd.ExcelWriter(spath, engine='xlsxwriter') 
    # Write Files - Single Simulation
    for i, stock in enumerate(l_stocks):
        dF_temp = pd.DataFrame(nA_StockBS_Ret_Out[:, :, i])
        dF_temp.T.to_excel(writer, sheet_name=stock, freeze_panes=(1,1))    
    # Close writer
    writer.save()
    writer.close()


# -----------------------------------------------------------------------------#
#---------------------  Export results - Matrix - CSV -------------------------#
# -----------------------------------------------------------------------------#
# Format Time * Simulation

if output_type == 'CSV':
    print('Exporting Results to Csv...')
    spath = list(CWD.rglob(excel_parameters))[0].parent.as_posix()
    # Write Files - Single Simulation
    for i, stock in enumerate(l_stocks):
        name_file = spath + "/" + name_output + "_" + stock + '_results.csv'
        pd.DataFrame(nA_StockBS_Ret_Out[:, :, i]).T.to_csv(name_file)  




# -----------------------------------------------------------------------------#
#---------------------  Export Expected Returns -------------------------------#
# -----------------------------------------------------------------------------#

spath = list(CWD.rglob(excel_parameters))[0].parent.as_posix() + "/" + name_output + '_exp_returns.csv'
# ------------------------ Calculate the expected returns
dF_temp = dF_YC_Aligned  # add YC only for Risk neutral cases
# Develop the dataframe with the stock indexes
dF_temp = dF_temp.assign(key=1).merge(dF_StockParam.reset_index().assign(key=1), on='key').drop('key', 1)
# Calculate the expected return (annualised)
if rn_sim == True:
    dF_temp['ExpRet'] = dF_temp['Forward']
else:
    dF_temp['ExpRet'] = dF_temp['Return']
# Take out the dividends
dF_temp['ExpRet'] = dF_temp['ExpRet']  - dF_temp['Dividend']
dF_temp = dF_temp[['Year', 'StockName', 'ExpRet']]
dF_temp.to_csv(spath)
