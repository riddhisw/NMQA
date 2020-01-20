import sys
import os
import copy
import traceback
import numpy as np

########################
# Find qslam modules
########################
sys.path.append('../qslam')

from qslamdesignparams import GLOBALDICT
from exptrisk import EmpiricalRisk
from visualiserisk import DataCube, cm2inch
from experimentaldata import DataKeys

########################
# Taking in bash parameters /
########################
datakey = int(sys.argv[1]) # data key
num_qubits = DataKeys[str(datakey)]['parameters']['N']
    



########################
# Save to path 
########################

savetopath = './' # local

########################
# Set 1D Hardware  to Ion Trap
########################

change_gridconfig = True

# assume equi-distant linear array

if change_gridconfig is True:

    GLOBALDICT["GRIDDICT"] = {}
    
    for idx_posy in range(num_qubits):
        if idx_posy < 10 :
            GLOBALDICT["GRIDDICT"]["QUBIT_0" + str(idx_posy)] = (0.0, float(idx_posy))
        if idx_posy >= 10 :
            GLOBALDICT["GRIDDICT"]["QUBIT_" + str(idx_posy)] = (0.0, float(idx_posy))

########################
# Set Defaults
########################

change_MAX_NUM_ITERATIONS = 100
change_MSMTS_PER_NODE = 1
change_SIGMOID_APPROX_ERROR = 10.0**(-6)
change_QUANTISATION_UNCERTY = 10.0**(-4)
change_P_ALPHA = 15 
change_P_BETA = 10 
change_LAMBDA_1 = 0.820
change_LAMBDA_2 = 0.968

GLOBALDICT["MODELDESIGN"]["MAX_NUM_ITERATIONS"] = change_MAX_NUM_ITERATIONS
GLOBALDICT["MODELDESIGN"]["MSMTS_PER_NODE"] = change_MSMTS_PER_NODE
GLOBALDICT["NOISEPARAMS"]["SIGMOID_APPROX_ERROR"]["SIGMA"] = change_SIGMOID_APPROX_ERROR
GLOBALDICT["NOISEPARAMS"]["QUANTISATION_UNCERTY"]["SIGMA"] = change_QUANTISATION_UNCERTY
GLOBALDICT["MODELDESIGN"]["P_ALPHA"] = change_P_ALPHA
GLOBALDICT["MODELDESIGN"]["P_BETA"] = change_P_BETA
GLOBALDICT["MODELDESIGN"]["LAMBDA_1"] = change_LAMBDA_1
GLOBALDICT["MODELDESIGN"]["LAMBDA_2"] = change_LAMBDA_2

########################
# Set All Loop Parameters
########################


# ------------------------------------------------------------------------------
# TURN OFF PARAMETER SCANS
# ------------------------------------------------------------------------------

# Fix msmt scan - and turn it off!
msmt_per_qubit_scan = [1] # [1, 2, 4, 5, 6, 8, 10, 15, 20, 25, 50]

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# NEW PARAMETER SCANS
# ------------------------------------------------------------------------------

# BUGFIX
# Need to adjust total iterations for a gridsize of 6 ions. 
# If we keep the same ratios of sys size to msmts, then: [int(idx_x) for idx_x in np.floor(6.0 * np.asarray([ 5, 10, 15, 20, 25, 50, 75, 100, 125, 250]) / 25.)]
#   gives us [1, 2, 3, 4, 6, 12, 18, 24, 30, 60] iteratons.
# If we keep consistency with previous data but eliminate 0 msmts, then: 6.0*np.floor(np.asarray([ 5, 10, 15, 20, 25, 50, 75, 100, 125, 250])/ 6)[1:] 
#   we get [   6.,   12.,   18.,   24.,   48.,   72.,   96.,  120.,  246.] iterations 
# The code below combines both:

meta_max_iter_scan =[ 1, 2, 3, 4, 6, 12, 18, 24, 30, 60, 72, 96, 120, 246]


lambda_databse = np.load('./lambda_pairs_2.npz')
lambda1 = list(lambda_databse['lambda_1']) 
lambda2 = list(lambda_databse['lambda_2']) 

lambda_scan = zip(lambda1, lambda2)

LOOPS_DICT = {"meta_max_iter_scan":meta_max_iter_scan, 
              "lambda_scan":lambda_scan,
              "msmt_per_qubit_scan": msmt_per_qubit_scan}
              

########################
# Run Script
########################

ParamUpdater = DataCube(LOOPS_DICT)
meta_ssim_pairs_1 = []
meta_empr_pairs_1 = []

for idx_l in range(len(ParamUpdater.lambda_scan)):
    
    SAMPLE_GLOBAL_MODEL = copy.deepcopy(GLOBALDICT)
    SAMPLE_GLOBAL_MODEL["MODELDESIGN"]["LAMBDA_1"] = ParamUpdater.lambda_scan[idx_l][0]
    SAMPLE_GLOBAL_MODEL["MODELDESIGN"]["LAMBDA_2"] = ParamUpdater.lambda_scan[idx_l][1]

    ssim_qslam = []
    err_qslam = []
    err_naive = []
    ssim_naive =[]
    
    for idx_msmt_iter in range(len(ParamUpdater.meta_max_iter_scan)):
    
        SAMPLE_GLOBAL_MODEL["MODELDESIGN"]["MAX_NUM_ITERATIONS"] = ParamUpdater.meta_max_iter_scan[idx_msmt_iter]
        
        expt = EmpiricalRisk(SAMPLE_GLOBAL_MODEL, datakey)
        err, ssim = expt.calculate_risk(number_of_trials=50)[0:2]
        
        ssim_qslam.append(ssim[0])
        err_qslam.append(err[0])
        ssim_naive.append(ssim[1])
        err_naive.append(err[1])

    meta_ssim_pairs_1.append([ssim_qslam, ssim_naive])
    meta_empr_pairs_1.append([err_qslam, err_naive])
    
    np.savez('2019_Jun_qslam_exptdata_'+str(datakey), 
             ParamUpdater=ParamUpdater, 
             meta_ssim_pairs=meta_ssim_pairs_1, 
             meta_empr_pairs=meta_empr_pairs_1)

