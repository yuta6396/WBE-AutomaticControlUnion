import os
from skopt.space import Real
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo
from datetime import datetime

# simulation setting
@dataclass
class Control:
    target_var: str = "PREC"
    input_var: str = "MOMY"
    max_input: int = 30
    num_input_grid: int = 3
    Opt_vec: list = field(default_factory=lambda: ["BO", "RS"])
    Opt_purpose: str = "MinSum"
    trial_num: int = 2
    bounds: list = field(init=False)

    def __post_init__(self):
        self.bounds = [Real(-self.max_input, self.max_input, name=f'{self.input_var}_Y{i+20}')
                       for i in range(self.num_input_grid)]

control_instance = Control()
# drawing parameters
@dataclass
class Draw:
    LinePlots_RespectiveValue_vec: list = field(default_factory=lambda: ["Ave", "Median", "Max", "Min"])
    fontsize: int = 18
    linewidth: int = 2
    linewidth_box: int = 1
    markersize: int = 8
    colors6: list = field(default_factory=lambda: ['#4c72b0', '#f28e2b', '#55a868', '#c44e52'])
    dpi: int = 300  # 画質設定

draw_instance = Draw()

# save directry
# top_dir_pathを ユーザーネーム変更！
@dataclass
class Save:
    top_dir_path: str = "/home/yuta/scale-5.5.1/scale-rm/test/tutorial/ideal/WarmBubbleExperiment/WBE-AutomaticControlUnion"
    log_dir_path: str = field(init=False)
    fig_dir_path: str = field(init=False)
    summary_dir_path: str = field(init=False)
    init_dir_path: str = field(init=False)
    output_dir_path: str = field(init=False)
    current_time: str = field(init=False)
    jst: ZoneInfo = field(default_factory=lambda: ZoneInfo("Asia/Tokyo"))  # 日本時間のタイムゾーンを設定

    def __post_init__(self):
        self.current_time = datetime.now(self.jst).strftime("%m-%d-%H:%M")
        self.log_dir_path = f"{self.top_dir_path}/logs"
        self.fig_dir_path = f"{self.top_dir_path}/results/plots"
        self.summary_dir_path = f"{self.top_dir_path}/results/summaries"
        self.init_dir_path = f"{self.top_dir_path}/data/input_files"
        self.output_dir_path = f"{self.top_dir_path}/data/output_files"

save_instance = Save()

## Black box Optimization Parameters
@dataclass
class BlackBoxOptimize:
    control: Control = field(default_factory=Control, repr=False, compare=False)
    # BO Parameters
    initial_design_numdata_vec: list = field(default_factory=lambda: [3])
    max_iter_vec: list = field(default_factory=lambda: [10, 20])

    # PSO_LDWIM Parameters
    w_max: float = 0.9
    w_min: float = 0.4
    c1: float = 2.0
    c2: float = 2.0

    # GA Parameters
    gene_length: int = field(init=False)  # Number of genes per individual 制御入力grid数
    crossover_rate: float = 0.8  
    mutation_rate: float = 0.05  
    lower_bound: float = field(init=False)  # Lower bound of gene values
    upper_bound: float = field(init=False)  # Upper bound of gene values
    alpha: float = 0.5  # BLX-alpha parameter
    tournament_size: int = 3  # 選択数なので population以下にする必要あり

    def __post_init__(self):
        # Control クラスの属性を使用して初期化
        self.gene_length = self.control.num_input_grid
        self.lower_bound = -self.control.max_input
        self.upper_bound = self.control.max_input

blackboxoptimize_instance = BlackBoxOptimize()

# SCALE-RM parameters
@dataclass
class SCALE:
    save: Save = field(default_factory=Save, repr=False, compare=False)
    nofpe: int = 2
    fny: int = 2
    fnx: int = 1
    run_time: int = 20
    init_file: str = field(init=False)
    org_file: str = field(init=False)
    history_file: str = field(init=False)

    orgfile: str = 'no-control.pe######.nc'
    gpyoptfile: str = "gpyopt.pe######.nc"

    def __post_init__(self):
        self.init_file = f"{self.save.init_dir_path}/init_00000101-000000.000.pe######.nc"
        self.org_file = f"{self.save.init_dir_path}/init_00000101-000000.000.pe######.org.nc"
        self.history_file = f"{self.save.output_dir_path}/history.pe######.nc"

scale_instance = SCALE()