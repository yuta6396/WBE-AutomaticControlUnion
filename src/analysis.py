# src/analysis.py
import os

import matplotlib.pyplot as plt
import numpy as np

from config import Opt_vec


def save_plots(BO_ratio_matrix, RS_ratio_matrix, trial_i, exp_i):
    """
    結果のプロットと保存を行う
    """
    plt.figure(figsize=(10, 5))
    plt.plot(BO_ratio_matrix[exp_i, :], label='BO')
    plt.plot(RS_ratio_matrix[exp_i, :], label='RS')
    plt.xlabel('Y-grid')
    plt.ylabel('Accumulated Precipitation')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"results/plots/result_{trial_i}_{exp_i}.png")
    plt.close()


def print_result(sum_no, sum_co, f, trial_num, exp_num):
    """
    累積降水量の結果を計算し、ログファイルおよび標準出力に書き出す。
    
    Args:
        sum_no (ndarray): 制御前の累積降水量データ
        sum_co (ndarray): 制御後の累積降水量データ
        f (file object): ログファイルのファイルオブジェクト
        trial_num (int): 試行回数
        exp_num (int): 実験番号
    """
    total_sum_no = np.sum(sum_no)
    total_sum_co = np.sum(sum_co)
    
    # 比率を計算する
    if total_sum_no != 0:
        reduction_ratio = 100 * total_sum_co / total_sum_no
    else:
        reduction_ratio = 0.0
    
    # ログファイルに書き出し
    f.write(f"\nTrial {trial_num}, Experiment {exp_num}:")
    f.write(f"\nSum of Precipitation Before Control: {total_sum_no}")
    f.write(f"\nSum of Precipitation After Control: {total_sum_co}")
    f.write(f"\nReduction ratio (after/before control): {reduction_ratio:.2f}%\n")
    
    # 標準出力に表示
    print(f"Trial {trial_num}, Experiment {exp_num}:")
    print(f"Sum of Precipitation Before Control: {total_sum_no}")
    print(f"Sum of Precipitation After Control: {total_sum_co}")
    print(f"Reduction ratio (after/before control): {reduction_ratio:.2f}%")




def save_plots(BO_ratio_matrix, RS_ratio_matrix, trial_i, exp_i):
    """
    ベイズ最適化とランダムサーチの結果を比較したグラフを保存
    """
    plt.figure(figsize=(10, 5))
    plt.plot(BO_ratio_matrix[exp_i, :], label='BO', marker='o')
    plt.plot(RS_ratio_matrix[exp_i, :], label='RS', marker='o')
    plt.xlabel('Y-grid')
    plt.ylabel('Accumulated Precipitation')
    plt.title(f'Results for Trial {trial_i}, Exp {exp_i}')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"results/plots/result_{trial_i}_{exp_i}.png")
    plt.close()

