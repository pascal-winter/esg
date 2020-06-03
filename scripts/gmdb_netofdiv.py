# -*- coding: utf-8 -*-
"""
@author: Pascal Winter
Apply the dividend scheme and fees to a stoichastic scenario file
Stochastic scenario format: CSV (Month * Simulation), Returns
    
"""

import pandas as pd
import numpy as np
from pathlib import Path


CWD = Path(__file__).resolve().parents[1] # Since we are in a sub-directory




#%%#############################################################################
########################## 0. FUNCTION #########################################
################################################################################



def calc_ret_netofdiv(name_input, name_output , filename_parameter_xlsx, NAVStart):

    # ---------------------  INITIALISATION -----------------------------------#
    # --------------------------- Load Matrix CSV
    csv_address = list(CWD.rglob(name_input))[0]
    nA_Scenario = np.loadtxt(csv_address, delimiter=',',
                             skiprows = 1)
    nA_Scenario = nA_Scenario[:,1:] # Drop the 1st column
    # --------------------- Load Dividends & Fees
    file_parameter_xlsx = pd.ExcelFile(list(CWD.rglob(filename_parameter_xlsx))[0])
    dF_PolParamY = pd.read_excel(file_parameter_xlsx, 'PolYearParam')
    dF_Dividend = pd.read_excel(file_parameter_xlsx, 'Dividend')
    # --------------------- Align Fees with time frame 
    index_yearint = (np.arange(0, nA_Scenario.shape[0] ) / 12).astype('int32')
    nA_DMP_Fees = np.interp(index_yearint, dF_PolParamY['Year'], dF_PolParamY['DMPFee'])
    

    # ------------------- CALC DIVIDENDS   -----------------------------------# 
    # ------------------- Calculate Net NAV
    nA_NAVBop = np.zeros(nA_Scenario.shape, dtype = 'float64')
    nA_NAVMop = np.zeros(nA_Scenario.shape, dtype = 'float64')
    nA_NAVEop = np.zeros(nA_Scenario.shape, dtype = 'float64')
    # Initialise
    nA_NAVBop[0,:] = NAVStart
    for i in range(0, nA_Scenario.shape[0]): # Loop on Time
        # Calculate NAV after retrun and fee
        nA_NAVMop[i,:] = nA_NAVBop[i,:] * (1 + nA_Scenario[i,:] ) * (1 - nA_DMP_Fees[i] / 12 )
        # Calculate dividend rate (get index location then apply)
        nA_temp = np.interp(nA_NAVMop[i,:], dF_Dividend['NAVmin'], dF_Dividend.index).astype('int32')
        nA_temp = np.interp(nA_temp, dF_Dividend.index, dF_Dividend['DivRate'])
        nA_NAVEop[i,:]  = nA_NAVMop[i,:] * (1 - nA_temp / 12)
        # Next Step
        if i < nA_Scenario.shape[0] - 1: 
            nA_NAVBop[i + 1,:] =  nA_NAVEop[i,:] 
    # Get net returns
    nA_NetReturns = nA_NAVEop / nA_NAVBop - 1
    
    # ------------------- EXPORT RESULTS  -------------------------------------# 
    
    spath = csv_address.parent.as_posix() + "/" + name_output
    #np.savetxt(spath, , delimiter=',')
    pd.DataFrame(nA_NetReturns).to_csv(spath)
    return nA_NetReturns
    
#%%#############################################################################
########################## 1. APPLY FUNCTION ###################################
################################################################################

# ---------------------- Single use

# nA_NetReturns = calc_ret_netofdiv('RN_201912_9vol_results.csv',
#                                   'RN_201912_9pct.csv' , 
#                                   'GMdB_Parameters_1.xlsx',
#                                   10)



# ---------------------- Batch
file_parameter_xlsx = pd.ExcelFile(list(CWD.rglob('PricingRuns.xlsx'))[0])
dF_ESG_Specs = pd.read_excel(file_parameter_xlsx, 'ESG')

for index, row in dF_ESG_Specs.iterrows():
    nA_NetReturns = calc_ret_netofdiv(dF_ESG_Specs.loc[index]['RAW_ResultFile'],
                                      dF_ESG_Specs.loc[index]['Result_Name'], 
                                      dF_ESG_Specs.loc[index]['Parameter_File'],
                                      dF_ESG_Specs.loc[index]['NAV_start'])
    
