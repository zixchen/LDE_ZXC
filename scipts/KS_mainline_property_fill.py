# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 17:14:21 2025

@author: Zixiang.Chen
"""
import numpy as np
import sps_interface
import pandas as pd
from pipeline_simulation import Advection
from memory_profiler import profile
from line_profiler import LineProfiler
from multiprocessing import Process

def get_HRDSY_painted_properties(path_to_PI_data):
    # Read data
    df = pd.read_pickle(path_to_PI_data)
    
    return(df.loc[:, ['Q', 'rho_painted', 'mu_painted', 'Tref_painted']])
    
def get_pipe_geometry(path_to_model, from_loc, to_loc, dx):
    
    # Read model    
    KS = sps_interface.model(path_to_model)
    L = KS.get_path_length(from_loc, to_loc)*1000
    nx = int(L // dx)
    x = np.linspace(0,L,nx)
    dx = x[1] - x[0]
    path_dia_array = KS.get_path_diameter_as_array(from_loc, to_loc, x/1000)
    IA = {}
    IA['IA'] = (path_dia_array/1000)**2*np.pi/4
    IA['IA_x'] = x
    return(L,dx,IA)
    
def build_advection_velocity(df_Q, L):
    Q_dict = {}
    df_Q[df_Q<0] = 0
    t = np.array(df_Q.index.to_pydatetime(), dtype=np.datetime64)
    for idx, ti in enumerate(range(len(t))):
        Q_dict[t[ti]] =  {'Q':np.array([df_Q[t[ti]]/3600, df_Q[t[ti]]/3600]), 'Q_x':np.array([0, L])}
    return(Q_dict)
    
    
def start_instance(instance, **kwargs):
    instance.solve(**kwargs)
    
if __name__ == '__main__':
    print('Get HRDSY properties')
    df = get_HRDSY_painted_properties('../output/df_HRDSY.pkl')
    
    print('Get pipe geometry')
    L, dx, IA = get_pipe_geometry(r'C:\Users\Zixiang.Chen\development\sps_interface\sample_model', 'TAKE_HRDSY_REC', 'HF_STLCT', 100)

    print(np.min(IA['IA']))
    
    print('Preparing for simulation')
    Q_dict =  build_advection_velocity(df.loc[:, 'Q'], L)
    
    t = np.array(df.index.to_pydatetime(), dtype=np.datetime64)
    
    instances = [
        Advection(L,dx,IA),
        Advection(L,dx,IA),
        Advection(L,dx,IA)
    ]
    
    kwargs_list = [
        {'Q_dict':Q_dict, 'a_x0_t':df.loc[:, 'rho_painted'].bfill().values, 't':t, 'initialize':True, 'a_t0':999, 'a_t0_x':None, 't0':t[0], 'method':'flux limiter', 'limiter_function':'generalized_minmod', 'print_msgs':['ERROR', 'WARNING'], 'write_result':True, 'case_name':'rho', 'data_file_size':1e9},
        {'Q_dict':Q_dict, 'a_x0_t':df.loc[:, 'mu_painted'].bfill().values,  't':t, 'initialize':True, 'a_t0':999, 'a_t0_x':None, 't0':t[0], 'method':'flux limiter', 'limiter_function':'generalized_minmod', 'print_msgs':['ERROR', 'WARNING'], 'write_result':True, 'case_name':'mu', 'data_file_size':1e9},
        {'Q_dict':Q_dict, 'a_x0_t':df.loc[:, 'Tref_painted'].bfill().values,  't':t, 'initialize':True, 'a_t0':999, 'a_t0_x':None, 't0':t[0], 'method':'flux limiter', 'limiter_function':'generalized_minmod', 'print_msgs':['ERROR', 'WARNING'], 'write_result':True, 'case_name':'Tref', 'data_file_size':1e9},
    ]
    
    processes = []
    for instance, kwargs in zip(instances, kwargs_list):
        p = Process(target=start_instance, args=(instance,), kwargs=kwargs)
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
