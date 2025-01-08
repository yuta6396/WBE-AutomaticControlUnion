import os
import netCDF4
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import matplotlib
import subprocess
from skopt import gp_minimize
from skopt.space import Integer
import pandas as pd
import seaborn as sns
# 時刻を計測するライブラリ
import time
import pytz
from datetime import datetime
from zoneinfo import ZoneInfo

from optimize import random_search
from analysis import *
from make_directory import make_directory
from config import time_interval_sec, bound
from calc_object_val import calculate_objective_func_val

import requests
import json
matplotlib.use('Agg')

"""
BORSのシミュレーション
"""

#### User 設定変数 ##############

input_var = "MOMY" # MOMY, RHOT, QVから選択
input_value = 10
Zgrid_bottom = 0
Zgrid_width = 20
Alg_vec = ["GS"]
num_input_grid = 1 # ある2つの地点を制御
Opt_purpose = "MinSum" #MinSum, MinMax, MaxSum, MaxMinから選択

dpi = 75 # 画像の解像度　スクリーンのみなら75以上　印刷用なら300以上
colors6  = ['#4c72b0', '#f28e2b', '#55a868', '#c44e52'] # 論文用の色
###############################
jst = pytz.timezone('Asia/Tokyo')# 日本時間のタイムゾーンを設定
current_time = datetime.now(jst).strftime("%m-%d-%H-%M")

"""
gp_minimize で獲得関数を指定: acq_func。
gp_minimize の呼び出しにおける主要なオプションは次の通りです。
"EI": Expected Improvement
"PI": Probability of Improvement
"LCB": Lower Confidence Bound
"gp_hedge": これらの獲得関数をランダムに選択し、探索を行う

EI は、探索と活用のバランスを取りたい場合に多く使用されます。
PI は、最速で最良の解を見つけたい場合に適していますが、早期に探索が止まるリスクがあります。
LCB は、解の探索空間が不確実である場合に有効で、保守的に最適化を進める場合に使用されます
"""




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


### SCALE-RM関連関数
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

def update_netcdf(init: str, output: str, pe: int, Ygrid, Zgrid):
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
                if pe == 0:
                    if Ygrid < 20:
                        var[Ygrid, 0, Zgrid] += input_value  # (y, x, z)
                elif pe == 1:
                    if Ygrid >= 20:
                        var[Ygrid-20, 0, Zgrid] += input_value
                dst[name][:] = var
            else:
                dst[name][:] = src[name][:]

    # outputをinitにコピー
    subprocess.run(["cp", output, init])
    return init

def sim(Ygrid, Zgrid):
    """
    制御入力決定後に実際にその入力値でシミュレーションする
    """
    #control_input = [0, 0, 0] # 制御なしを見たいとき
    for pe in range(nofpe):
        init, output = prepare_files(pe)
        init = update_netcdf(init, output, pe, Ygrid, Zgrid)

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

    sum_co=np.zeros(40) #制御後の累積降水量
    sum_no=np.zeros(40) #制御前の累積降水量
    for y_i in range(40):
        for t_j in range(nt):
            if t_j > 0:
                sum_co[y_i] += dat[t_j,0,y_i,0]*time_interval_sec
                sum_no[y_i] += odat[t_j,0,y_i,0]*time_interval_sec

    objective_val = calculate_objective_func_val(sum_co, Opt_purpose)
    return objective_val


def grid_search(objective_function, f, dirname):
    best_score = float('inf')
    best_params = None
    results = np.zeros((Zgrid_width, 40))

    for z_i in range(Zgrid_bottom, Zgrid_bottom+Zgrid_width):
        for y_i in range(0, 40):
            print(f"z={z_i},y={y_i}")
            score = objective_function(y_i, z_i)
            print(score)
            results[z_i][y_i] = score
            if score < best_score:
                best_score = score
                best_params = [z_i, y_i]
                f.write(f"\n{best_params=}: best_score={best_score}")

    # カラーマップを取得
    cmap = get_cmap("viridis")  # 好きなカラーマップ（例: 'viridis'）
    colors = cmap(np.linspace(0, 1, Zgrid_width))  # Zgrid_width種類の色を生成
    plt.figure(figsize=(8, 6))
    for z_i in range(Zgrid_width):
        plt.plot(range(0, 40), results[z_i], marker='o',label=f"Z={z_i+Zgrid_bottom}", color=colors[z_i], lw=2, ms=6)
    plt.xlabel('Y grid', fontsize=20)
    plt.ylabel('Accumulated precipitation (%)', fontsize=20)
    plt.title(f"{input_var}+={input_value} Z={Zgrid_bottom}-{Zgrid_bottom+Zgrid_width-1}", fontsize=20)
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{dirname}/LineGraph.png", dpi = 300)

    return best_params, best_score, results


def main():
    ###実行
    dirname = f"test_result/GS_1grid/{Opt_purpose}_{input_var}+={input_value}_Z={Zgrid_bottom}-{Zgrid_bottom+Zgrid_width-1}_{current_time}"
    os.makedirs(dirname, exist_ok=True)
    output_file_path = os.path.join(dirname, f'summary.txt')
    f = open(output_file_path, 'w')

    # グリッドサーチの実行
    best_params, best_score, results = grid_search(sim, f, dirname)

    f.write(f"\nBest parameters: {best_params}\n")
    print(f"Best score: {best_score}")
    with open(f"{dirname}/GS_data.json", 'w') as f:
        json.dump(results.tolist(), f, indent= 4)
    f.close()


def notify_slack(webhook_url, message, channel=None, username=None, icon_emoji=None):
    """
    Slackに通知を送信する関数。

    :param webhook_url: SlackのWebhook URL
    :param message: 送信するメッセージ
    :param channel: メッセージを送信するチャンネル（オプション）
    :param username: メッセージを送信するユーザー名（オプション）
    :param icon_emoji: メッセージに表示する絵文字（オプション）
    """
    payload = {
        "text": message
    }

    # オプションのパラメータを追加
    if channel:
        payload["channel"] = channel
    if username:
        payload["username"] = username
    if icon_emoji:
        payload["icon_emoji"] = icon_emoji

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()  # エラーがあれば例外を発生させる
        print("Slackへの通知が送信されました。")
    except requests.exceptions.RequestException as e:
        print(f"Slackへの通知に失敗しました: {e}")

def get_script_name():
    return os.path.basename(__file__)

if __name__ == "__main__":
    main()
    # ここに取得したWebhook URLを設定
    webhook_url =os.getenv("SLACK_WEBHOOK_URL") # export SLACK_WEBHOOK_URL="OOOO"したらOK

    # 送信するメッセージを設定
    message = f"✅ {get_script_name()}の処理が完了しました。"

    # オプションでチャンネルやユーザー名、アイコン絵文字を設定
    # 例:
    # channel = "#general"
    # username = "Notifier"
    # icon_emoji = ":robot_face:"
    # notify_slack(webhook_url, message, channel, username, icon_emoji)

    # オプションを使用しない場合は以下のようにシンプルに呼び出せます
    notify_slack(webhook_url, message, channel="webhook")