# coias-back-app

```
.
├── API
│   ├── __init__.py      # 
│   ├── main.py          # mainの関数　e.g. import API.main
│   ├── dependencies.py  # token処理まとめ e.g. import API.dependencies
│   ├── config.py        # 環境変数をpythonで使用可能にする、使用の場合はここから右のようにimport e.g. import API.config
│   ├── utils.py         # 共通して使うことのできる関数 e.g. import API.utils
│   └── routers          # routeごとに管理
│   │   ├── __init__.py  # 
│   │   ├── files.py     # ファイル操作の処理 e.g. import API.routers.files
│   │   ├── processes.py # 解析系の処理 e.g. import API.routers.processes
│   │   ├── tests.py     # テスト用のファイル e.g. import API.routers.tests
│   │   └── ws.py        # websocketの処理 e.g. import API.routers.ws
│   └── internal         # front向けAPIとは別の開発者向けAPI
│       ├── __init__.py  # 
│       └── admin.py     # admin userのみの処理をまめたもの e.g. import API.internal.admin 
├── Docker
├── SubaruHSC
├── data
├── docs
├── env
└── findOrb
```

__API__    
frontAppに情報を送信するためのAPI

__Docker__  
実行用・開発用のDockerfile

__SubaruHSC__  
imageの保管フォルダ。変更の可能性あり。

__data__  
~/.coiasを保存

__docs__  
ドキュメント

__env__  
condaのパッケージを保管

__findOrb__  
天体処理に関するCプログラム群

## コードフォーマッタとlint

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[PyCQA/flake8](https://github.com/PyCQA/flake8)

### flake8
エラーを無視する場合は該当の行に追加  
エラー全般を無視する場合には、エラーを指定しない。

```python
# noqa:E501
```