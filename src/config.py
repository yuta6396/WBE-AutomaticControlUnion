import os
from skopt.space import Real
# simulation setting
input_var = "MOMY"
max_input = 30
num_input_grid = 3
Opt_vec = ["BO", "RS"]
Opt_purpose = "MinSum"
trial_num = 10
bounds = [Real(-max_input, max_input, name=f'{input_var}_Y{i+20}') for i in range(num_input_grid)]

# BO Parameters
initial_design_numdata_vec = [3]
max_iter_vec = [10, 30]

# PSO_LDWIM Parameters
w_max = 0.9
w_min = 0.4
c1 = 2.0
c2 = 2.0

# GA Parameters
gene_length = num_input_grid  # Number of genes per individual 制御入力grid数
crossover_rate = 0.8  # Crossover rate
mutation_rate = 0.05  # Mutation rate
lower_bound = -max_input  # Lower bound of gene values
upper_bound = max_input  # Upper bound of gene values
alpha = 0.5  # BLX-alpha parameter
tournament_size = 3 #選択数なので population以下にする必要あり


# SCALE-RM param
nofpe = 2
fny = 2
fnx = 1
run_time = 20
init_file = "init_00000101-000000.000.pe######.nc"
org_file = "init_00000101-000000.000.pe######.org.nc"
history_file = "history.pe######.nc"

orgfile = 'no-control.pe######.nc'
file_path = os.path.dirname(os.path.abspath(__file__))
gpyoptfile=f"gpyopt.pe######.nc"