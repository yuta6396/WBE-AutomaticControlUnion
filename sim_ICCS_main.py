import subprocess
import json
import sys
import os

# 時刻を計測するライブラリ
import time
import pytz
from datetime import datetime
from zoneinfo import ZoneInfo

trial_base = 0
trial_num = 1

def load_config(config_file='config.json'):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config

def run_script(script_name, config_file='config.json', base_dir):
    try:
        # コマンドライン引数として config_file を渡す
        result = subprocess.run(
            ['python', script_name, config_file, base_dir],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Output of {script_name}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {script_name}: {e.stderr}", file=sys.stderr)

def main():
    jst = pytz.timezone('Asia/Tokyo')# 日本時間のタイムゾーンを設定
    current_time = datetime.now(jst).strftime("%m-%d-%H-%M")
    base_dir = f"ICCS_result/{trial_base}-{trial_base+trial_num -1}_{current_time}/"

    # 実行したいスクリプトのリスト
    scripts = [
        'sim_ICCS_BO.py', 'plt_fig.py'
        # 他のスクリプトをここに追加
        # 'another_script.py',
        # 'yet_another_script.py',
    ]

    config_file = 'config.json'

    # スクリプトが存在するか確認
    for script in scripts:
        if not os.path.isfile(script):
            print(f"Script {script} does not exist.", file=sys.stderr)
            return

    # 各スクリプトを順番に実行
    for script in scripts:
        print(f"Running {script}...")
        run_script(script, config_file, base_dir)
        print(f"Finished running {script}.\n")

if __name__ == "__main__":
    main()
