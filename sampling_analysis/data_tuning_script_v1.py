import sys
import os
import copy
import traceback
import numpy as np
import matplotlib.pyplot as plt

sys.path.append('../qslam')
sys.path.append('../paduaq')
from pdinter_MM import pd_interpolant, calc_padua_cgl
from true_functions import true_function, generate_data_qubits_coords

########################
# Find qslam modules
########################

from singlerun import SingleRunAnalysis
from riskanalysis import EngineeredTruth
from qslamdesignparams import GLOBALDICT


########################
# Taking in bash parameters
########################
padua_order = int(sys.argv[1]) # Padua order. 1, 2, 3, 4, 5,...
idx_job_array = int(sys.argv[2]) # job array starts from 1. Used for tuning
data_qubit_num = 25
data_qubit_flag ='uniform'

########################
# Save to path 
########################

path = '/scratch/QCL_RG/qslam_padua_paper/' # on Artemis './data/'
true_function_type = 'cheb2fun'

########################
# Generate Padua Points
########################

total_qubits = calc_padua_cgl(padua_order)[0]

########################
# Set Data Points
########################

GLOBALDICT["DATA_QUBITS"] = generate_data_qubits_coords(data_qubit_num,
                                                        flag=data_qubit_flag)

########################
# Set hardware and true map
########################

if GLOBALDICT["DATA_QUBITS"] is not None:
    total_qubits = total_qubits + GLOBALDICT["DATA_QUBITS"]
num_of_nodes = len(total_qubits)

true_map = []
GLOBALDICT["GRIDDICT"] = {}
for idx_posy in range(num_of_nodes):
    
    point = total_qubits[idx_posy]
    true_map.append(true_function(point[0], point[1], d=true_function_type))

    if idx_posy < 10 :

        GLOBALDICT["GRIDDICT"]["QUBIT_0" + str(idx_posy)] = (point[0], point[1])

    if idx_posy >= 10 :

        GLOBALDICT["GRIDDICT"]["QUBIT_" + str(idx_posy)] =  (point[0], point[1])
        
true_map_ = np.asarray(true_map)

########################
# Set Defaults
########################

GLOBALDICT["MODELDESIGN"]["MSMTS_PER_NODE"] = 1
GLOBALDICT["MODELDESIGN"]["MULTIPLER_R_MAX"] = 4.

repts = 50
particleconfigs = [ [3,2], [9,6], [15,10], [21,14], [30, 20]]

prefix = '_padua_ord_'+str(padua_order)+'_'
lambda_paris_2 = np.load('lambda_pairs_2.npz')
random_variances = np.load('random_variances.npz')

IDX1_SHP = len(random_variances['g1var'])
IDX2_SHP = 30 # len(lambda_paris_2['lambda_1']) not doing all 250
IDX3_SHP = len(particleconfigs)

####################################
# Tuning Script (Data Generation)
####################################


idx_1, idx_2 = np.unravel_index(idx_job_array - 1 , (IDX1_SHP, IDX2_SHP) )

GLOBALDICT["NOISEPARAMS"]["SIGMOID_APPROX_ERROR"]["SIGMA"] = random_variances['g2var'][idx_1]
GLOBALDICT["NOISEPARAMS"]["QUANTISATION_UNCERTY"]["SIGMA"] = random_variances['g1var'][idx_1]
GLOBALDICT["MODELDESIGN"]["LAMBDA_1"] = lambda_paris_2['lambda_1'][idx_2]
GLOBALDICT["MODELDESIGN"]["LAMBDA_2"] = lambda_paris_2['lambda_2'][idx_2]

fname_likelihood = 'rand_'+str(idx_1)+'_'+str(idx_2)+'_'

max_iterations = num_of_nodes * 3
GLOBALDICT["MODELDESIGN"]["MAX_NUM_ITERATIONS"] = max_iterations

for idx_3 in range(IDX3_SHP):

    GLOBALDICT["MODELDESIGN"]["P_ALPHA"] = particleconfigs[idx_3][0]
    GLOBALDICT["MODELDESIGN"]["P_BETA"] = particleconfigs[idx_3][1]

    SAMPLE_GLOBAL_MODEL = copy.deepcopy(GLOBALDICT)

    uniform_r_expt = SingleRunAnalysis(SAMPLE_GLOBAL_MODEL, true_map_, repts, beta_expansion_mode=False, beta_skew_adjust=False)
    uniform_r_expt.run_analysis(path+'Uni_R'+prefix+fname_likelihood+str(idx_3))

    trunc_r_expt = SingleRunAnalysis(SAMPLE_GLOBAL_MODEL, true_map_, repts, beta_expansion_mode=True, beta_skew_adjust=False)
    trunc_r_expt.run_analysis(path+'Trunc_R'+prefix+fname_likelihood+str(idx_3))
