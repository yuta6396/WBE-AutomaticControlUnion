import os
import netCDF4
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import subprocess
# 時刻を計測するライブラリ
import time
import pytz
from datetime import datetime
from zoneinfo import ZoneInfo

from config import time_interval_sec, w_max, w_min, gene_length, crossover_rate, mutation_rate, lower_bound, upper_bound, alpha, tournament_size
from optimize import *
from analysis import *
from make_directory import make_directory

matplotlib.use('Agg')

"""
PSOGAのシミュレーション
"""

#### User 設定変数 ##############

input_var = "MOMY" # MOMY, RHOT, QVから選択
max_input = 30 #20240830現在ではMOMY=30, RHOT=10, QV=0.1にしている
Alg_vec = ["PSO", "GA"]
num_input_grid = 3 #y=20~20+num_input_grid-1まで制御
Opt_purpose = "MinSum" #MinSum, MinMax, MaxSum, MaxMinから選択

particles_vec = [3]           # 粒子数
iterations_vec = [2]        # 繰り返し回数
pop_size_vec = particles_vec  # Population size
num_generations_vec = iterations_vec  # Number of generations

# PSO LDWIM
c1 = 2.0
c2 = 2.0

trial_num = 2  # 乱数種の数

dpi = 75 # 画像の解像度　スクリーンのみなら75以上　印刷用なら300以上
colors6  = ['#4c72b0', '#f28e2b', '#55a868', '#c44e52'] # 論文用の色
###############################
jst = pytz.timezone('Asia/Tokyo')# 日本時間のタイムゾーンを設定
current_time = datetime.now(jst).strftime("%m-%d-%H-%M")
base_dir = f"result/PSOGA/{current_time}/"
cnt_vec = np.zeros(len(particles_vec))
for i in range(len(particles_vec)):
     cnt_vec[i] = int(particles_vec[i])*int(iterations_vec[i])


nofpe = 2
fny = 2
fnx = 1
run_time = 20


varname = 'PREC'

init_file = "init_00000101-000000.000.pe######.nc"
org_file = "init_00000101-000000.000.pe######.org.nc"
history_file = "history.pe######.nc"

orgfile = f'no-control_{str(time_interval_sec)}.pe######.nc'
file_path = os.path.dirname(os.path.abspath(__file__))
gpyoptfile=f"gpyopt.pe######.nc"


def prepare_files(pe: int):
    """ファイルの準備と初期化を行う"""
    output_file = f"out-{input_var}.pe######.nc"
    # input file
    init = init_file.replace('######', str(pe).zfill(6))
    org = org_file.replace('######', str(pe).zfill(6))
    history = history_file.replace('######', str(pe).zfill(6))
    output = output_file.replace('######', str(pe).zfill(6))
    history_path = file_path+'/'+history
    if (os.path.isfile(history_path)):
        subprocess.run(["rm", history])
    subprocess.run(["cp", org, init])  # 初期化

    return init, output

def update_netcdf(init: str, output: str, pe: int, input_values):
    """NetCDFファイルの変数を更新する"""
    with netCDF4.Dataset(init) as src, netCDF4.Dataset(output, "w") as dst:
        # グローバル属性のコピー
        dst.setncatts(src.__dict__)
        # 次元のコピー
        for name, dimension in src.dimensions.items():
            dst.createDimension(
                name, (len(dimension) if not dimension.isunlimited() else None))
        # 変数のコピーと更新
        for name, variable in src.variables.items():
            x = dst.createVariable(
                name, variable.datatype, variable.dimensions)
            dst[name].setncatts(src[name].__dict__)
            if name == input_var:
                var = src[name][:]
                if pe == 1:
                    for Ygrid_i in range(num_input_grid):
                        var[Ygrid_i, 0, 0] += input_values[Ygrid_i]  # (y, x, z)
                dst[name][:] = var
            else:
                dst[name][:] = src[name][:]

    # outputをinitにコピー
    subprocess.run(["cp", output, init])
    return init

def sim(control_input):
    """
    制御入力決定後に実際にその入力値でシミュレーションする
    """
    for pe in range(nofpe):
        init, output = prepare_files(pe)
        init = update_netcdf(init, output, pe, control_input)

    subprocess.run(["mpirun", "-n", "2", "./scale-rm", "run_R20kmDX500m.conf"])

    for pe in range(nofpe):
        gpyopt = gpyoptfile.replace('######', str(pe).zfill(6))
        history = history_file.replace('######', str(pe).zfill(6))
        subprocess.run(["cp", history,gpyopt])
    for pe in range(nofpe):  # history処理
        fiy, fix = np.unravel_index(pe, (fny, fnx))
        nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
        onc = netCDF4.Dataset(orgfile.replace('######', str(pe).zfill(6)))
        nt = nc.dimensions['time'].size
        nx = nc.dimensions['x'].size
        ny = nc.dimensions['y'].size
        nz = nc.dimensions['z'].size
        gx1 = nx * fix
        gx2 = nx * (fix + 1)
        gy1 = ny * fiy
        gy2 = ny * (fiy + 1)
        if pe == 0:
            dat = np.zeros((nt, nz, fny*ny, fnx*nx))
            odat = np.zeros((nt, nz, fny*ny, fnx*nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[varname][:]
        odat[:, 0, gy1:gy2, gx1:gx2] = onc[varname][:]

    # 各時刻までの平均累積降水量をplot 
    # 小数第2位までフォーマットして文字列化
    formatted_control_input = "_".join([f"{val:.2f}" for val in control_input]) 
    dir_name = f"{base_dir}/Time_lapse/"
    os.makedirs(dir_name, exist_ok=True)
    for i in range(1,nt):
        l1, l2 = 'no-control', 'under-control'
        c1, c2 = 'blue', 'green'
        xl = 'y'
        yl = 'PREC'
        plt.plot(odat[i, 0, :, 0], color=c1, label=l1)
        plt.plot(dat[i, 0, :, 0], color=c2, label=l2)
        plt.xlabel(xl)
        plt.ylabel(yl)
        plt.title(f"t={(i-1)*time_interval_sec}-{i*time_interval_sec}")
        plt.legend()
        filename = dir_name + \
            f'input={formatted_control_input}_t={i}.png'
        #plt.ylim(0, 0.005)
        plt.savefig(filename)
        plt.close()
        
    sum_co=np.zeros(40) #制御後の累積降水量
    sum_no=np.zeros(40) #制御前の累積降水量
    for y_i in range(40):
        for t_j in range(nt):
            if t_j > 0:
                sum_co[y_i] += dat[t_j,0,y_i,0]*time_interval_sec
                sum_no[y_i] += odat[t_j,0,y_i,0]*time_interval_sec
    return sum_co, sum_no

def calculate_objective_func_val(sum_co):
    """
    得られた各地点の累積降水量予測値(各Y-grid)から目的関数の値を導出する
    """
    represent_prec = 0
    if Opt_purpose == "MinSum" or Opt_purpose == "MaxSum":
        represent_prec = np.sum(sum_co)
        print(represent_prec)

    elif Opt_purpose == "MinMax" or Opt_purpose == "MaxMax":
        represent_prec = 0
        for j in range(40):  
            if sum_co[j] > represent_prec:
                represent_prec = sum_co[j] # 最大の累積降水量地点
    else:
        raise ValueError(f"予期しないOpt_purposeの値: {Opt_purpose}")

    if Opt_purpose == "MaxSum" or Opt_purpose == "MaxMax":
        represent_prec = -represent_prec # 目的関数の最小化問題に統一   
    return represent_prec

def black_box_function(control_input):
    """
    制御入力値列を入れると、制御結果となる目的関数値を返す
    """
    for pe in range(nofpe):
        init, output = prepare_files(pe)
        init = update_netcdf(init, output, pe, control_input)

    subprocess.run(["mpirun", "-n", "2", "./scale-rm", "run_R20kmDX500m.conf"])

    for pe in range(nofpe):
        gpyopt = gpyoptfile.replace('######', str(pe).zfill(6))
        history = history_file.replace('######', str(pe).zfill(6))
        subprocess.run(["cp", history,gpyopt])
    for pe in range(nofpe):  # history処理
        fiy, fix = np.unravel_index(pe, (fny, fnx))
        nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
        nt = nc.dimensions['time'].size
        nx = nc.dimensions['x'].size
        ny = nc.dimensions['y'].size
        nz = nc.dimensions['z'].size
        gx1 = nx * fix
        gx2 = nx * (fix + 1)
        gy1 = ny * fiy
        gy2 = ny * (fiy + 1)
        if pe == 0:
            dat = np.zeros((nt, nz, fny*ny, fnx*nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[varname][:]

        sum_co=np.zeros(40) #制御後の累積降水量
        for y_i in range(40):
            for t_j in range(nt):
                if t_j > 0: #なぜかt_j=0に　-1*10^30くらいの小さな値が入っているため除外　
                    sum_co[y_i] += dat[t_j,0,y_i,0]*time_interval_sec
    objective_val = calculate_objective_func_val(sum_co)

    return objective_val


###実行
make_directory(base_dir)

filename = f"config.txt"
config_file_path = os.path.join(base_dir, filename)  # 修正ポイント
f = open(config_file_path, 'w')
###設定メモ###
f.write(f"\ninput_var ={input_var}")
f.write(f"\nmax_input ={max_input}")
f.write(f"\nAlg_vec ={Alg_vec}")
f.write(f"\nnum_input_grid ={num_input_grid}")
f.write(f"\nOpt_purpose ={Opt_purpose}")
f.write(f"\nparticles_vec = {particles_vec}")
f.write(f"\niterations_vec = {iterations_vec}")
f.write(f"\npop_size_vec = {pop_size_vec}")
f.write(f"\nnum_generations_vec = {num_generations_vec}")
f.write(f"\ncnt_vec = {cnt_vec}")
f.write(f"\ntrial_num = {trial_num}\n")
f.write(f"w_max={w_max}\n")
f.write(f"w_min={w_min}\n")
f.write(f"c1={c1}\n")
f.write(f"c2={c2}\n")
f.write(f"gene_length={gene_length}\n")
f.write(f"crossover_rate={crossover_rate}\n")
f.write(f"mutation_rate={mutation_rate}\n")
f.write(f"lower_bound={lower_bound}\n")
f.write(f"upper_bound={upper_bound}\n")
f.write(f"alpha={alpha}\n")
f.write(f"tournament_size={tournament_size}\n")
f.write(f"trial_num={trial_num}\n")
f.write(f"{dpi=}")
f.write(f"\n{time_interval_sec=}")
################
f.close()

PSO_ratio_matrix = np.zeros((len(particles_vec), trial_num))
GA_ratio_matrix = np.zeros((len(particles_vec), trial_num))
PSO_time_matrix = np.zeros((len(particles_vec), trial_num))
GA_time_matrix = np.zeros((len(particles_vec), trial_num))

PSO_file = os.path.join(base_dir, "summary", f"{Alg_vec[0]}.txt")
GA_file = os.path.join(base_dir, "summary", f"{Alg_vec[1]}.txt")

with open(PSO_file, 'w') as f_PSO, open(GA_file, 'w') as f_GA:
    for trial_i in range(trial_num):
        cnt_base = 0
        for exp_i in range(len(particles_vec)):
            if exp_i > 0:
                cnt_base  = cnt_vec[exp_i - 1]


            ###PSO
            random_reset(trial_i)
            # 入力次元と最小値・最大値の定義
            bounds_MOMY = [(-max_input, max_input)]*num_input_grid  # 探索範囲

            start = time.time()  # 現在時刻（処理開始前）を取得
            best_position, result_value  = PSO(black_box_function, bounds_MOMY, particles_vec[exp_i], iterations_vec[exp_i], f_PSO)
            end = time.time()  # 現在時刻（処理完了後）を取得
            time_diff = end - start
            f_PSO.write(f"\n最小値:{result_value[iterations_vec[exp_i]-1]}")
            f_PSO.write(f"\n入力値:{best_position}")
            f_PSO.write(f"\n経過時間:{time_diff}sec")
            f_PSO.write(f"\nnum_evaluation of BBF = {cnt_vec[exp_i]}")

            sum_co, sum_no = sim(best_position)
            calculate_PREC_rate(sum_co, sum_no)
            PSO_ratio_matrix[exp_i, trial_i] = calculate_PREC_rate(sum_co, sum_no)
            PSO_time_matrix[exp_i, trial_i] = time_diff


            ###GA
            random_reset(trial_i)
            # パラメータの設定
            start = time.time()  # 現在時刻（処理開始前）を取得
            # Run GA with the black_box_function as the fitness function
            best_fitness, best_individual = genetic_algorithm(black_box_function,
                pop_size_vec[exp_i], gene_length, num_generations_vec[exp_i],
                crossover_rate, mutation_rate, lower_bound, upper_bound,
                alpha, tournament_size, f_GA)
            end = time.time()  # 現在時刻（処理完了後）を取得
            time_diff = end - start

            f_GA.write(f"\n最小値:{best_fitness}")
            f_GA.write(f"\n入力値:{best_individual}")
            f_GA.write(f"\n経過時間:{time_diff}sec")
            f_GA.write(f"\nnum_evaluation of BBF = {cnt_vec[exp_i]}")

            sum_co, sum_no = sim(best_individual)
            GA_ratio_matrix[exp_i, trial_i] = calculate_PREC_rate(sum_co, sum_no)
            GA_time_matrix[exp_i, trial_i] = time_diff


#シミュレーション結果の可視化
filename = f"summary.txt"
config_file_path = os.path.join(base_dir, "summary", filename)  
f = open(config_file_path, 'w')

vizualize_simulation(PSO_ratio_matrix, GA_ratio_matrix, PSO_time_matrix, GA_time_matrix, particles_vec,
         f, base_dir, dpi, Alg_vec, colors6, trial_num, cnt_vec)

f.close()