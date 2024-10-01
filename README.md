# WBE-AutomaticControlUnion
## 概要
Warm Bubble Experimentを用いた, 自動制御連合講演会用のシミュレーション(2024/09/30).

初期値介入による制御問題をBO, PSO, GA, RSの4手法を1度にsimulateできる（ユーザーはmain.pyを実行）.

t=0の時の(y, z) = (20, 0), (21, 0), (22, 0)グリッドの変数MOMYを制御する

## ファイル構造
- ~/scale-5.5.1/scale-rm/test/tutorial/ideal/WarmBubbleExperiment/WBE-AutomaticControlUnion
    - src/
        - main.py            #実行ファイル（メインロジック）
        - simulation.py     # シミュレーション関連の関数
        - optimization.py   # ベイズ最適化やランダムサーチ関連の関数
        - analysis.py       # 結果の集計や可視化関連の関数
        - config.py         # 設定値をまとめたファイル

    - data/                 # 入力データやシミュレーション結果
        - input_files/
        - output_files/

    - results/              # グラフや結果を保存
        - plots/
        - summaries/

    - logs/                 # 実行時のログやエラーメッセージ

## 可能な実験設定
- 制御変数の変更
    - MOMY  (-30~30)
    - RHOT  (-10~10)
    - QV    (-0.1~0.1)

- 制御グリッドの変更


- 制御目的の変更
    - 観測できる全範囲（y=0~39）の累積降水量の（最小化/最大化）
    - 最大累積降水量地点（y=y'）の累積降水量（最小化/最大化）

## ブラックボックス最適化手法の実装方法（講演会用の設定）
乱数種を10種類用意しシミュレーションを実行。

        np.random.seed(trial_i) 
        random.seed(trial_i) 
     

### ベイズ最適化
Scikit-Optimize ライブラリのgp minimize 関数

### 粒子群最適化
LDIWMを採用（w_max=0.9, w_min=0.4, c1=c2=2.0）

### 遺伝的アルゴリズム
実数値コーディングを採用

選択方式：トーナメント選択（トーナメントサイズ=3）

交叉方法：ブレンド交叉（交叉率=0.8，ブレンド係数α=0.5）

突然変異方法：ランダムな実数値への置き換え（突然変異率=0.05）

### ランダムサーチ
特になし



## 寄稿者

## 参照
