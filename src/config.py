import os
from skopt.space import Real
from zoneinfo import ZoneInfo

# simulation setting
class Control:
    target_var = "PREC"
    input_var = "MOMY"
    max_input = 30
    num_input_grid = 3
    Opt_vec = ["BO", "RS"]
    Opt_purpose = "MinSum"
    trial_num = 2

    bounds = []
    for i in range(num_input_grid):
        bounds.append(Real(-max_input, max_input, name=f'{input_var}_Y{i+20}'))


# drawing parameters
class Draw:
    LinePlots_RespectiveValue_vec = ["Ave", "Median", "Max", "Min"]
    fontsize = 18
    linewidth = 2
    linewidth_box = 1
    markersize = 8
    colors6  = ['#4c72b0', '#f28e2b', '#55a868', '#c44e52']
    dpi = 300 #画質設定

# save directry
# top_dir_pathを ユーザーネーム変更！
class Save:
    top_dir_path = "/home/yuta/scale-5.5.1/scale-rm/test/tutorial/ideal/WarmBubbleExperiment/WBE-AutomaticControlUnion"
    log_dir_path = f"{top_dir_path}/logs"
    fig_dir_path = f"{top_dir_path}/results/plots"
    summary_dir_path = f"{top_dir_path}/results/summaries"
    # 日本時間のタイムゾーンを設定
    jst = ZoneInfo("Asia/Tokyo")

## Black box Optimization Parameters
class BlackBoxOptomize:
    # BO Parameters
    initial_design_numdata_vec = [3]
    max_iter_vec = [10, 20]

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


# SCALE-RM parameters
class SCALE
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