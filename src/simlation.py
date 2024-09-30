# src/simulation.py
import os
import subprocess

import netCDF4
import numpy as np

from config import (fnx, fny, history_file, init_file, input_var, nofpe,
                    org_file)


def sim(input):
    """
    シミュレーションを実行し、結果を返す
    """
    sum_co = np.zeros(40)
    sum_no = np.zeros(40)
    
    for pe in range(nofpe):
        initialize_nc_file(pe, input)
    run_simulation()

    sum_co, sum_no = process_history_files()
    return sum_co, sum_no

def initialize_nc_file(pe, input):
    """
    netCDFファイルの初期化と変更
    """
    init = init_file.replace('######', str(pe).zfill(6))
    org = org_file.replace('######', str(pe).zfill(6))
    output = f"out-{input_var}.pe######.nc".replace('######', str(pe).zfill(6))

    subprocess.run(["cp", org, init])  # 初期化
    with netCDF4.Dataset(init) as src, netCDF4.Dataset(output, "w") as dst:
        dst.setncatts(src.__dict__)  # グローバル属性のコピー
        for name, dimension in src.dimensions.items():
            dst.createDimension(name, len(dimension))
        for name, variable in src.variables.items():
            x = dst.createVariable(name, variable.datatype, variable.dimensions)
            dst[name].setncatts(variable.__dict__)
            if name == input_var:
                var = src[name][:]
                var[0:input.size, 0, 0] += input  # 入力に基づき変更
                dst[name][:] = var
            else:
                dst[name][:] = src[name][:]

def run_simulation():
    """
    シミュレーションを実行する関数
    """
    subprocess.run(["mpirun", "-n", "2", "./scale-rm", "run_R20kmDX500m.conf"])

def process_history_files():
    """
    シミュレーション後のhistoryファイルを処理
    """
    sum_co = np.zeros(40)
    sum_no = np.zeros(40)
    
    for pe in range(nofpe):
        nc = netCDF4.Dataset(history_file.replace('######', str(pe).zfill(6)))
        onc = netCDF4.Dataset(org_file.replace('######', str(pe).zfill(6)))
        for i in range(40):
            sum_co[i] += nc['PREC'][1, 0, i, 0] * 3600
            sum_no[i] += onc['PREC'][1, 0, i, 0] * 3600
    return sum_co, sum_no


def black_box_function(input):
    """
    ベイズ最適化やランダムサーチで使用されるコスト関数。
    シミュレーションを実行し、その結果を評価。
    """
    sum_co, sum_no = sim(input)
    
    result = 0
    if Opt_purpose == "MinSum" or Opt_purpose == "MaxSum":
        result = np.sum(sum_co)
    elif Opt_purpose == "L1":
        result = np.sum(np.abs(input)) + 50 * np.sum(sum_co)
    elif Opt_purpose == "L2":
        result = np.sum(input ** 2) + 50 * np.sum(sum_co)
    
    return result