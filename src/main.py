# src/main.py
# 標準ライブラリ
import os
import time
import numpy as np
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

# srcよりimport
from simlation import sim
from analysis import print_result, save_box_plots, save_line_plots
from config import control_instance, save_instance, blackboxoptimize_instance
from optimization import bayesian_optimization, random_search


def main():
    current_time = save_instance.current_time
    log_file = os.path.join(save_instance.log_dir_path, f"log-{current_time}.txt")
    summary_file = os.path.join(save_instance.summary_dir_path, f"summary-{current_time}.txt")

    # 累積降水量減少(%)を格納する配列の初期化
    max_iter_vec_len = len(blackboxoptimize_instance.max_iter_vec)
    trial_num = control_instance.trial_num

    BO_ratio_matrix = np.zeros((max_iter_vec_len, trial_num))
    PSO_ratio_matrix = np.zeros((max_iter_vec_len, trial_num))
    RS_ratio_matrix = np.zeros((max_iter_vec_len, trial_num))
    GA_ratio_matrix = np.zeros((max_iter_vec_len, trial_num))

    # 必要時間を格納する配列の初期化
    BO_time_matrix = np.zeros((max_iter_vec_len, trial_num))
    PSO_time_matrix = np.zeros((max_iter_vec_len, trial_num))
    RS_time_matrix = np.zeros((max_iter_vec_len, trial_num))
    GA_time_matrix = np.zeros((max_iter_vec_len, trial_num))

    with open(log_file, 'a') as f_log, open(summary_file, 'a') as f_summary:
        for trial_i in range(trial_num):
            initial_x_iters, initial_y_iters = None, None
            for exp_i in range(max_iter_vec_len):
                # ベイズ最適化
                min_input, time_diff, initial_x_iters, initial_y_iters = bayesian_optimization(trial_i, exp_i, initial_x_iters, initial_y_iters)
                sum_co, sum_no = sim(min_input)
                BO_ratio_matrix[exp_i, trial_i] = print_result(sum_co, sum_no, f_log, trial_i, exp_i)
                BO_time_matrix[exp_i, trial_i] = time_diff

                # ランダムサーチ
                best_params, best_score, time_diff = random_search(trial_i, exp_i, previous_best=(best_params, best_score))
                sum_co, sum_no = sim(best_params)
                RS_ratio_matrix[exp_i, trial_i] = print_result(sum_co, sum_no, f_log, trial_i, exp_i)
                RS_time_matrix[exp_i, trial_i] = time_diff

                # 結果の保存と可視化
                save_box_plots(BO_ratio_matrix, RS_ratio_matrix, trial_i, exp_i, "PREC", current_time)
                save_box_plots(BO_time_matrix, RS_time_matrix, trial_i, exp_i, "Time", current_time)
                save_line_plots(BO_ratio_matrix, RS_ratio_matrix, f_summary, trial_i, exp_i,  current_time)


if __name__ == "__main__":
    main()
