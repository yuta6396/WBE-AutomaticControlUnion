# src/main.py
# 標準ライブラリ
import os
import time
import numpy as np
from datetime import datetime

# srcよりimport
from simlation import sim
from analysis import print_result, save_plots
from config import (Opt_vec, bounds, input_var, max_iter_vec, num_input_grid,
                    trial_num)
from optimization import bayesian_optimization, random_search


def main():
    current_time = datetime.now().strftime("%m-%d %H:%M")
    # ログファイルを開く ユーザーネーム変更！
    log_dir = "/home/yuta/scale-5.5.1/scale-rm/test/tutorial/ideal/WarmBubbleExperiment/WBE-AutomaticControlUnion/logs"
    log_file_path = os.path.join(log_dir, f"{current_time}.txt")

    # 累積降水量減少(%)を格納するための配列の初期化
    BO_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))
    PSO_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))
    RS_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))
    GA_ratio_matrix = np.zeros((len(max_iter_vec), trial_num))


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
