# src/main.py
import os
import time
import numpy as np
from simlation import sim

from analysis import print_result, save_plots
from config import (Opt_vec, bounds, input_var, max_iter_vec, num_input_grid,
                    trial_num)
from optimization import bayesian_optimization, random_search


def main():
    # 結果を格納するための配列やメトリクスの初期化
    BO_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))
    RS_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))
    # ログファイルを開く
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "experiment_log.txt")
    with open(log_file_path, 'a') as f:
        for trial_i in range(trial_num):
            for exp_i in range(len(max_iter_vec)):
                # ベイズ最適化
                min_input, time_diff = bayesian_optimization(trial_i, exp_i)
                sum_BO_MOMY = sim(min_input)
                print_result(sum_no, sum_co, f, trial_num, exp_num)

                # ランダムサーチ
                best_params, time_diff = random_search(trial_i, exp_i)
                sum_RS_MOMY = sim(best_params)
                print_result(sum_no, sum_co, f, trial_num, exp_num)

                # 結果の保存と可視化
                save_plots(BO_ratio_matrix, RS_ratio_matrix, trial_i, exp_i)

if __name__ == "__main__":
    main()
