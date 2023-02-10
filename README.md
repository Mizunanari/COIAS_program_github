# coias-back-app

```
.
├── API
│   ├── __init__.py      # "API"をパッケージにするファイル
│   ├── main.py          # "main"モジュール, e.g. import API.main
│   ├── dependencies.py  # "dependencies"モジュール, e.g. import API.dependencies
│   ├── config.py        # "config"モジュール, e.g. import API.config
│   ├── utils.py         # "utils"モジュール, e.g. import API.utils
│   └── routers          # "routers" はサブパッケージ
│   │   ├── __init__.py  # "routers" をサブパッケージにするファイル
│   │   ├── files.py     # "files"はサブモジュール, e.g. import API.routers.files
│   │   ├── processes.py # "processes"はサブモジュール, e.g. import API.routers.processes
│   │   ├── tests.py     # "tests"はサブモジュール, e.g. import API.routers.tests
│   │   └── ws.py        # "ws"はサブモジュール, e.g. import API.routers.ws
│   └── internal         # "internal"はサブパッケージ
│       ├── __init__.py  # makes "internal" a "Python subpackage"
│       └── admin.py     # "admin" はサブモジュール, e.g. import API.internal.admin
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