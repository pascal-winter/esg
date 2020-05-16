# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np





#%%#############################################################################
################## 1. TRANSFORM NUMPY SQUARE in PD LONG  #######################
################################################################################







#%%#############################################################################
############################# 2. RESULT ANALYSIS  ##############################
################################################################################



def calculate_percentile(dF_data, list_agg, col_res, list_percentile):
    '''
    Calculate the mean and percentile on a flat ESG file
    ----------
    dF_data : Dataframe - ESG flat DB result file
    list_agg : List of variable to be aggregated 
    col_res : column which contains the value to be analysed
    list_percentile : list of percentiles
    '''
    # -------- Percentile
    dF_Result = dF_data.groupby(list_agg).quantile(list_percentile)[col_res]
    index_name ='level_' + str(len(list_agg)) # recreate index name to rename properly
    dF_Result = dF_Result.reset_index().rename(columns={index_name :'Indicator'})
    # ------- Set Index
    list_index = list_agg + ['Indicator']
    dF_Result = dF_Result.set_index(list_index)
    # dF_Result = dF_Result.reset_index()
    return dF_Result


def calculate_mean(dF_data, list_agg, col_res, list_percentile):
    '''
    Calculate the mean on a flat ESG file - see percentile function
    '''
    # -------- Mean
    dF_Result =  dF_data.groupby(list_agg).mean()[col_res].reset_index()
    dF_Result['Indicator'] = 'Mean'
    dF_Result.reset_index()
    # ------- Set Index
    list_index = list_agg + ['Indicator']
    dF_Result = dF_Result.set_index(list_index)
    # dF_Result = dF_Result.reset_index()
    return dF_Result


def calculate_vol(dF_data, list_agg, col_res, list_percentile, i_step):
    '''
    Calculate the mean on a flat ESG file - see percentile function
    ----------
    i_step: setp length for vol adjustem
    '''
    # -------- Vol
    dF_Result =  dF_data.groupby(list_agg).std()[col_res].reset_index()
    dF_Result[col_res] =  dF_Result[col_res] * np.sqrt( i_step )
    dF_Result['Indicator'] = 'Vol'
    dF_Result.reset_index()
    # ------- Set Index
    list_index = list_agg + ['Indicator']
    dF_Result = dF_Result.set_index(list_index)
    # dF_Result = dF_Result.reset_index()
    return dF_Result


#%%#############################################################################
####################################  OTHER  ###################################
################################################################################



def set_size(width, norow, nocol, fraction=1):
    """ Set aesthetic figure dimensions to avoid scaling in latex.
    -------- Parameters:
        width: float / Width in pts (345)
        norow: int / # row in subblot
        fraction: float / Fraction of the width which you wish the figure to occupy
    -------- Returns:
    fig_dim: tuple
            Dimensions of figure in inches
    """
    # Width of figure
    fig_width_pt = width * fraction
    # Convert from pt to inches
    inches_per_pt = 1 / 72.27
    # Golden ratio to set aesthetic figure height
    golden_ratio = (5**.5 - 1) / 2
    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    fig_height_in = fig_width_in * golden_ratio
    fig_dim = (fig_width_in * nocol, fig_height_in * norow)
    return fig_dim


