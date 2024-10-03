# src/analysis.py
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from config import Control, BlackBoxOptomize, Draw



def print_result(sum_co, sum_no, f, trial_i, exp_i):
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
    f.write(f"\nReduction ratio (after/before control): {reduction_ratio:.3f}%\n")
    
    # 標準出力に表示
    print(f"Trial {trial_num}, Experiment {exp_num}:")
    print(f"Sum of Precipitation Before Control: {total_sum_no}")
    print(f"Sum of Precipitation After Control: {total_sum_co}")
    print(f"Reduction ratio (after/before control): {reduction_ratio:.3f}%")
    return reduction_ratio




def save_box_plots(BO_ratio_matrix, RS_ratio_matrix, trial_i, exp_i, data_str, current_time):
    """
    シミュレーション結果を比較した箱ひげ図を保存
    結果：累積降水量・必要時間
    """
    for exp_i in range(len(max_iter_vec)):
        data = [BO_ratio_matrix[exp_i, :], RS_ratio_matrix[exp_i, :]]

        fig, ax = plt.subplots(figsize=(8,6))
        box = ax.boxplot(data, patch_artist=True,medianprops=dict(color='black', linewidth=linewidth_box))
        for patch, color in zip(box['boxes'], colors6):
            patch.set_facecolor(color)
        
        # カテゴリラベルの設定
        plt.xticks(ticks=range(1, len(Opt_vec) + 1), labels=Opt_vec, fontsize=fs-2)
        plt.yticks(fontsize=fs-2) ##このマジックナンバー何とかしたい
        # 箱ひげ図の描画
        plt.title(f'Func evaluation times = {max_iter_vec[exp_i]}')
        plt.xlabel('Optimization method', fontsize=fontsize)
        if data_str == "PREC":
            plt.ylabel('Accumulated precipitation (%)', fontsize=fontsize)
        elif data_str == "Time":
            plt.ylabel('Elapsed time (sec)', fontsize=fontsize)
        else:
            plt.ylabel('?????', fontsize=fontsize)

        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir_path, f"Boxplot_{data_str}_FET={max_iter_vec[exp_i]}_{current_time}.png", dpi = dpi)
        plt.close()



def save_line_plots(BO_ratio_matrix, RS_ratio_matrix, f, trial_i, exp_i, current_time):
    """
    シミュレーション結果を比較した折れ線グラフを保存
    比較対象: 累積降水量のAve, Median, Max, Min    
    """
    BO_vec = np.zeros(len(max_iter_vec)) 
    RS_vec = np.zeros(len(max_iter_vec)) 

    for Respect_i in range(LinePlots_RespectiveValue_vec):
        # データ処理
        if Respect_i == "Ave":
            for exp_i in range(len(max_iter_vec)):
                BO_vec[exp_i] = np.mean(BO_ratio_matrix[exp_i, :])
                RS_vec[exp_i] = np.mean(RS_ratio_matrix[exp_i, :])

        elif Respect_i == "Median":
            for exp_i in range(len(max_iter_vec)):
                BO_vec[exp_i] = np.median(BO_ratio_matrix[exp_i, :])
                RS_vec[exp_i] = np.median(RS_ratio_matrix[exp_i, :])
        
        elif Respect_i == "Min":
            for trial_i in range(trial_num):
                for exp_i in range(len(max_iter_vec)):
                    if trial_i == 0:
                        BO_vec[exp_i] = BO_ratio_matrix[exp_i, trial_i]
                        RS_vec[exp_i] = RS_ratio_matrix[exp_i, trial_i]

                    if BO_ratio_matrix[exp_i, trial_i] < BO_vec[exp_i]:
                        BO_vec[exp_i] = BO_ratio_matrix[exp_i, trial_i]
                    if RS_ratio_matrix[exp_i, trial_i] < RS_vec[exp_i]:
                        RS_vec[exp_i] = RS_ratio_matrix[exp_i, trial_i]
        
        else:
            for trial_i in range(trial_num):
                for exp_i in range(len(max_iter_vec)):
                    if trial_i == 0:
                        BO_vec[exp_i] = BO_ratio_matrix[exp_i, trial_i]
                        RS_vec[exp_i] = RS_ratio_matrix[exp_i, trial_i]

                    if BO_ratio_matrix[exp_i, trial_i] > BO_vec[exp_i]:
                        BO_vec[exp_i] = BO_ratio_matrix[exp_i, trial_i]
                    if RS_ratio_matrix[exp_i, trial_i] > RS_vec[exp_i]:
                        RS_vec[exp_i] = RS_ratio_matrix[exp_i, trial_i]

        # サマリー保存
        f.write(f"\n{Respect_i} accumulated precipitation (Function evaluation times={max_iter_vec})")
        f.write(f"\n{BO_vec}")
        f.write(f"\n{RS_vec}")

        plt.figure(figsize=(8, 6))
        # plot
        plt.plot(max_iter_vec, BO_vec, marker='o', label='BO', color=colors6[0], lw=lw, ms=ms)  # 丸
        plt.plot(max_iter_vec, RS_vec, marker='D', label='RS', color=colors6[3], lw=lw, ms=ms) 

        # ラベル付け
        plt.title(f'{Respect_i} Value of Trial = {trial_num}')
        plt.xlabel('Function evaluation times', fontsize=fontsize+2)
        plt.ylabel('Accumulated precipitation (%)', fontsize=fontsize+2)
        plt.xticks(cnt_vec, fontsize=fontsize)
        plt.yticks(fontsize=fontsize)

        # 調整して保存
        plt.tight_layout()
        plt.legend(fontsize=fontsize)
        plt.grid(True)
        plt.savefig(fig_dir_path,f"LinePlot_{Respect_i}_Value_{current_time}.png", dpi = dpi)
        plt.close()

