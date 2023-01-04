# coias-back-app

```
.
├── API
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

**src[0-9]\_.\***
バックエンドのコア部分。[解説：docs/core-program.md](docs/core-program.md)

## 環境構築

[docs/Docker手動環境構築手順.md](docs/Docker手動環境構築手順.md)

## コードフォーマッタとlint

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[PyCQA/flake8](https://github.com/PyCQA/flake8)

### flake8
エラーを無視する場合は該当の行に追加  
エラー全般を無視する場合には、エラーを指定しない。

```python
# noqa:E501
```