#!/bin/bash

# Pythonスクリプトの実行
python GS.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Pythonスクリプトが正常に完了しました。" | mail -s "スクリプト実行完了" b212693@hiroshima-u.ac.jp
else
    echo "Pythonスクリプトがエラーコード $EXIT_CODE で終了しました。" | mail -s "スクリプト実行エラー" b212693@hiroshima-u.ac.jp
fi