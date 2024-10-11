# src/simulation.py
import os
import subprocess
import netCDF4
import numpy as np
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from config import control_instance, scale_instance, save_instance


# def sim(input):
#     """
#     シミュレーションを実行し、結果を返す
#     """
#     sum_co = np.zeros(40)
#     sum_no = np.zeros(40)
    
#     for pe in range(scale_instance.nofpe):
#         initialize_nc_file(pe, input)
#     run_simulation()

#     sum_co, sum_no = process_history_files()
#     return sum_co, sum_no

# def initialize_nc_file(pe, input):
#     """
#     netCDFファイルの初期化と変更
#     """
#     input_var = control_instance.input_var
#     init_file = scale_instance.init_file
#     org_file = scale_instance.org_file

#     init = init_file.replace('######', str(pe).zfill(6))
#     org = org_file.replace('######', str(pe).zfill(6))
#     output = f"{save_instance.output_dir_path}/out-{save_instance.current_time}.pe######.nc".replace('######', str(pe).zfill(6))

#     subprocess.run(["cp", org, init])  # 初期化
#     with netCDF4.Dataset(init) as src, netCDF4.Dataset(output, "w") as dst:
#         dst.setncatts(src.__dict__)  # グローバル属性のコピー
#         for name, dimension in src.dimensions.items():
#             dst.createDimension(name, len(dimension))
#         for name, variable in src.variables.items():
#             x = dst.createVariable(name, variable.datatype, variable.dimensions)
#             dst[name].setncatts(variable.__dict__)
#             if name == input_var:
#                 var = src[name][:]
#                 if pe == 1:  # ここで制御グリッド変えられる
#                     for Ygrid_i in range(control_instance.num_input_grid):                        
#                         var[Ygrid_i, 0, 0] += input[Ygrid_i]  # (y,x,z)
#                 dst[name][:] = var
#             else:
#                 dst[name][:] = src[name][:]

# def run_simulation():
#     """
#     シミュレーションを実行する関数
#     """
#     subprocess.run(["mpirun", "-n", "2", "../scale-rm", f"{save_instance.init_dir_path}/run_R20kmDX500m.conf"])

# def process_history_files():
#     """
#     シミュレーション後のhistoryファイルを処理
#     """
#     history_file = scale_instance.history_file
#     org_file = scale_instance.org_file
#     target_var = control_instance.target_var

#     sum_co = np.zeros(40)
#     sum_no = np.zeros(40)
    
#     for pe in range(scale_instance.nofpe):
#         nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
#         onc = netCDF4.Dataset(org_file.replace('######', str(pe).zfill(6)))
#         for i in range(40):
#             sum_co[i] += nc[target_var][1, 0, i, 0] * 3600 # (time,z,y,x)
#             sum_no[i] += onc[target_var][1, 0, i, 0] * 3600
#     return sum_co, sum_no

def prepare_files(config, pe: int, input_values):
    """ファイルの準備と初期化を行う"""
    output_file = f"out-{control_instance.input_var}.pe######.nc"
    output_file = os.path.join(save_instance.output_dir_path, output_file)
    # ファイル名の生成
    init = config.init_file.replace('######', str(pe).zfill(6))
    #print(init)
    org = config.org_file.replace('######', str(pe).zfill(6))
    #print(org)
    history = config.history_file.replace('######', str(pe).zfill(6))
    #print(history)
    output = output_file.replace('######', str(pe).zfill(6))
    #print(output)
    history_path = os.path.join(save_instance.init_dir_path, history)

    # 既存のhistoryファイルを削除
    if os.path.isfile(history_path):
        subprocess.run(["rm", history])

    # orgをinitにコピーして初期化
    subprocess.run(["cp", org, init])

    return init, output

def update_netcdf(config, init: str, output: str, pe: int, input_values):
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
            if name == control_instance.input_var:
                var = src[name][:]
                if pe == 1:
                    for Ygrid_i in range(control_instance.num_input_grid):
                        var[Ygrid_i, 0, 0] += input_values[Ygrid_i]  # (y, x, z)
                dst[name][:] = var
            else:
                dst[name][:] = src[name][:]

    # outputをinitにコピー
    subprocess.run(["cp", output, init])

def run_simulation(config):
    """シミュレーションを実行する"""
    result = subprocess.run(
        ["mpirun", "-n", str(config.nofpe), "../scale-rm", f"{save_instance.init_dir_path}/run_R20kmDX500m.conf"],
        capture_output=True  # 標準出力と標準エラーをキャプチャする場合
    )

    if result.returncode != 0:
        print(f"Simulation failed with return code {result.returncode}")
        print("Error output:", result.stderr)

def process_history_files(config):
    """シミュレーション結果を集計する"""
    # gpyoptファイルの準備
    for pe in range(config.nofpe):
        gpyopt = save_instance.gpyoptfile.replace('######', str(pe).zfill(6))
        history = config.history_file.replace('######', str(pe).zfill(6))
        print(f"Processing PE {pe}: history file = {history}, gpyopt file = {gpyopt}")
        if not os.path.exists(history):
            print(f"Error: History file {history} does not exist.")
            return
        subprocess.run(["cp", history, gpyopt])

    # 結果の集計
    for pe in range(config.nofpe):
        fiy, fix = np.unravel_index(pe, (config.fny, config.fnx))
        # nc = netCDF4.Dataset(config.history_file.replace('######', str(pe).zfill(6)))
        nc = netCDF4.Dataset(config.history_file.replace('######', str(pe).zfill(6)))
        # onc = netCDF4.Dataset(config.org_file.replace('######', str(pe).zfill(6)))
        # # ファイル内の変数一覧を表示
        # print("Variables in file:", onc.variables.keys())
        nt = nc.dimensions['time'].size
        nx = nc.dimensions['x'].size
        ny = nc.dimensions['y'].size
        nz = nc.dimensions['z'].size
        gx1 = nx * fix
        gx2 = nx * (fix + 1)
        gy1 = ny * fiy
        gy2 = ny * (fiy + 1)
    #     if pe == 0:
    #         dat = np.zeros((nt, nz, config.fny * ny, config.fnx * nx))
    #         odat = np.zeros((nt, nz, config.fny * ny, config.fnx * nx))
    #     dat[:, 0, gy1:gy2, gx1:gx2] = nc[control_instance.target_var][:]
    #     odat[:, 0, gy1:gy2, gx1:gx2] = onc[control_instance.target_var][:]
    # # 結果の加算
    # sum_co=np.zeros(40) #制御後の累積降水量
    # sum_no=np.zeros(40) #制御前の累積降水量
    # for i in range(40):
    #     sum_co[i] += dat[1, 0, i, 0] * 3600
    #     sum_no[i] += odat[1, 0, i, 0] * 3600

        if pe == 0:
            dat = np.zeros((nt, nz, config.fny * ny, config.fnx * nx))
        dat[:, 0, gy1:gy2, gx1:gx2] = nc[control_instance.target_var][:]
        sum_co=np.zeros(40) #制御後の累積降水量
        for i in range(40):
            sum_co[i] += dat[1, 0, i, 0] * 3600
        return sum_co    

def sim(input_values):
    """シミュレーション全体を実行するメイン関数"""
    # 各プロセスについて処理を実行
    for pe in range(scale_instance.nofpe):
        # ファイルの準備
        init, output = prepare_files(scale_instance, pe, input_values)
        # NetCDFファイルの更新
        update_netcdf(scale_instance, init, output, pe, input_values)
    # シミュレーションの実行
    run_simulation(scale_instance)
    # 結果の集計
    sum_co = process_history_files(scale_instance)
    return sum_co


def black_box_function(input):
    """
    最適化問題の目的関数。
    制御入力を加えた初期値からシミュレーションを行い、その結果を評価。
    """
    Opt_purpose = control_instance.Opt_purpose
    sum_co = sim(input)
    
    represent_prec = 0
    if Opt_purpose == "MinSum" or Opt_purpose == "MaxSum":
        represent_prec = np.sum(sum_co)
        print(represent_prec)

    elif Opt_purpose == "MinMax" or Opt_purpose == "MaxMax":
        represent_prec = 0
        for j in range(40):  
            if sum_co[j] > represent_prec:
                represent_prec = sum_co[j] # 最大の累積降水量地点

    if Opt_purpose == "MaxSum" or Opt_purpose == "MaxMax":
        represent_prec = -represent_prec # 目的関数の最小化問題に統一   
    return represent_prec