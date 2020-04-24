import datetime
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from dateutil.relativedelta import relativedelta
import seaborn as sns
from wishpy.dataworker import DataWorker
dw = DataWorker(google_secret='../../../wishpy/client_secret.json')

import math
from scipy import stats
from scipy.stats import chi2_contingency
import statsmodels.stats.api as sms


def check_balance(df,group_name,metrics_name,expected_pop):
    mean = expected_pop
    var = expected_pop*(1-expected_pop)
    z95 = 1.96

    N = df[metrics_name].sum()

    mask = df.new_groups==group_name
    n = df.loc[mask,metrics_name].sum()

    p_hat = n/N

    sd = np.sqrt(var/N)
    margin = z95*sd

    upper = expected_pop + margin
    lower = expected_pop - margin

    if (upper>=p_hat) & (lower<=p_hat):
        print('Bucket of {} is Balanced'.format(group_name))
        print('Because the theoretical 95% CI of group population should be [{},{}], and the empirical group population is {}'.format(lower,upper,p_hat))
    else:
        print('Bucket of {} is NOT really Balanced'.format(group_name)) 
        print('Because the theoretical 95% CI of group population should be [{},{}], BUT the empirical group population is {}'.format(lower,upper,p_hat))
    print(100*'-')
    

    
def simple_power_sample_size(row,beta=0.8):
    var = row[0]*(1-row[0])
    effect_size = row[1]
    
    if effect_size != 0: 
        if beta == 0.8:
            n = math.ceil(16*var/(effect_size*effect_size))
        elif beta == 0.9:
            n = math.ceil(21*var/(effect_size*effect_size))
        else:
            n= np.nan
            print('beta need to be either 0.8 or 0.9, and 0.8 is the default value')
    elif effect_size == 0:
        n= np.nan
        print('effect size can NOT be 0 !')
    return n



def chi_2_test(df,treatment_name,control_name,imp,clk):
    treatment_clk = df.loc[df['new_groups']==treatment_name,clk].sum()
    treatment_noclk = df.loc[df['new_groups']==treatment_name,imp].sum() - df.loc[df['new_groups']==treatment_name,clk].sum()
    
    control_clk = df.loc[df['new_groups']==control_name,clk].sum()
    control_noclk = df.loc[df['new_groups']==control_name,imp].sum() - df.loc[df['new_groups']==control_name,clk].sum()
    
    contingency_table = np.array([[control_clk, control_noclk], [treatment_clk, treatment_noclk]])
    
    chi2, p, dof, expected = chi2_contingency(contingency_table, correction=False)
    
    return chi2,p;



def t_test_welchs(df,treatment_name,control_name,imp,clk):
    
    n_a = df.loc[df.new_groups==control_name,imp].sum() 
    n_b = df.loc[df.new_groups==treatment_name,imp].sum() 
    
    mean_a = df.loc[df.new_groups==control_name,clk].sum() / df.loc[df.new_groups==control_name,imp].sum()
    mean_b = df.loc[df.new_groups==treatment_name,clk].sum() / df.loc[df.new_groups==treatment_name,imp].sum()
    
    var_a = mean_a*(1-mean_a)
    var_b = mean_b*(1-mean_b)
    
    t = (mean_a - mean_b) / np.sqrt(var_a/n_a + var_b/n_b)

    nu_a = n_a - 1
    nu_b = n_b - 1
    
    df = ((var_a / n_a + var_b / n_b)**2) / ( (var_a/n_a)**2 /(nu_a) + (var_b/n_b)**2 /(nu_b) )
    
    p = (1 - stats.t.cdf(np.abs(t), df=df))*2

    return p,mean_a,mean_b



def t_test_classic(df,treatment_name,control_name,imp,clk):
    
    mean_a = df.loc[df.new_groups==control_name,clk].sum() / df.loc[df.new_groups==control_name,imp].sum()
    mean_b = df.loc[df.new_groups==treatment_name,clk].sum() / df.loc[df.new_groups==treatment_name,imp].sum()
    
    var_a = mean_a*(1-mean_a)
    var_b = mean_b*(1-mean_b)
    
    n_a = df.loc[df.new_groups==control_name,imp].sum() 
    n_b = df.loc[df.new_groups==treatment_name,imp].sum() 
    N = n_a + n_b
    df = N - 2
    
    s = np.sqrt( ((n_a-1)*var_a+(n_b-1)*var_b)/df )
    
    t = (mean_b - mean_a) / (s * np.sqrt(1.0/n_a + 1.0/n_b))
    
    # one-tailed p value need to *2
    p = (1 - stats.t.cdf(np.abs(t), df=df))*2 
    
    return p,mean_a,mean_b
    
    
    
def t_test_classic_uid(df,treatment_name,control_name,mean,std,n_name):
    
    mean_a = df.loc[df.new_groups==control_name,mean].mean()
    mean_b = df.loc[df.new_groups==treatment_name,mean].mean()
    
    std_a = df.loc[df.new_groups==control_name,std].mean()
    std_b = df.loc[df.new_groups==treatment_name,std].mean()
    
    var_a =std_a*std_a
    var_b = std_b*std_b
    
    n_a = df.loc[df.new_groups==control_name,n_name].sum() 
    n_b = df.loc[df.new_groups==treatment_name,n_name].sum() 
    N = n_a + n_b
    df = N - 2
    
    s = np.sqrt( ((n_a-1)*var_a+(n_b-1)*var_b)/df )
    
    t = (mean_b - mean_a) / (s * np.sqrt(1.0/n_a + 1.0/n_b))
    
    # one-tailed p value need to *2
    p = (1 - stats.t.cdf(np.abs(t), df=df))*2 
    
    return p,mean_a,mean_b