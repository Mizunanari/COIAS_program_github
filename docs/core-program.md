# コア部分処理の説明

- 2023/01/04 Kenichi Ito

## src1_preprocess

### `preprocess`

- 事前準備を行うシェルスクリプト
- 実行内容
  1. ディレクトリ、ログファイルの準備
  2. `make_default_parameter_files.py`の実行
  3. （MPCORB.DAT がないとき）`getMPCORB_and_mpc2edb` の実行

### `make_default_parameter_files.py`

- SExtractor と findOrb で使用するパラメータファイルの初期値を生成するスクリプト
- 実行内容
  1. `make_default_conv()` 畳み込みマスクの設定を生成する
  2. `make_default_sex(ETECT_MINAREA: int)` SExtractor で用いる設定を生成する
  3. `make_default2_param()` `default2.param`を生成する
  4. `make_ObsCodes_htm()` 天文台コードのリストを生成する
  5. `make_options_txt()` `options.txt`を生成する
  6. `make_rovers_txt()` Roving observer に関するテキストファイルを生成する
  7. `make_xdesig_txt()` 名称の異なる天体に関するテキストファイルを生成する

### `getMPCORB_and_mpc2edb`

- `minorplanetcenter.net`から最新の小惑星データを取得し、edb 形式に変換するシェルスクリプト

### `getMPCORB_and_mpc2edb_for_button`

- `minorplanetcenter.net`から最新の小惑星データを取得し、edb 形式に変換するシェルスクリプト
- 手動で小惑星データ更新ボタンを押した場合に実行される

## src2_startsearch2R

### `startsearch2R`

- ビニング・マスク・光源検出などを統括するシェルスクリプト
- 実行内容
  1. `binning.py` ビニングを行う
  2. `subm2.py` マスクをかける
  3. `findsource_auto_thresh_correct.py` 光源検出を行う
  4. `search_precise_orbit_directories.py` 精密軌道情報がすでにあるかどうかチェック

### `binning.py`

- 元画像の **ビニング（複数ピクセルの結合）** を行い、処理済みの画像ファイルに変換する
- 実行内容
  1. FITS 画像ファイルを検索して順番に読み込み（[astropy.io.fits](https://docs.astropy.org/en/stable/io/fits/index.html)による）
  2. 2x2（または 4x4）の範囲で平均を取り、新しい画像を生成する
  3. 新しい画像にヘッダ情報を書き込み、保存する

### `subm2.py`

- ビニングされた画像データに対して恒星をマスク（隠す）処理し、FITS・PNG ファイルとして保存する
- 実行内容
  1. FITS 画像ファイルを検索して順番に読み込み（[astropy.io.fits](https://docs.astropy.org/en/stable/io/fits/index.html)による）
  2. 全ファイルのマスクデータを取得し、中央値（`median_maskdata`）を計算する
  3. 中央値が 0 の部分を 1、1 より大きい部分を 1 としたマスクデータを生成する
  4. マスクした部分を埋めるための背景画像（`image_sky`）を生成する
  5. マスクを乗算し、新規画像を保存する。また、PNG 画像（マスクあり・なし）も同時に保存する

### `findsource_auto_thresh_correct.py`

- `findsource`シェルスクリプトを実行し、SExtractor を用いた光源検出を行う。検出数が適切になるように閾値を調節する
- 実行内容
  1. 検出閾値（`detect_thresh`）を 1.2 として初回の処理を行う
  2. 検出数が定数`SOURCE_NUMBER`の 0.75 倍～ 1.25 倍の間になるまで閾値を二分探索する
  3. 探索を達成したら終了

### `search_precise_orbit_directories.py`

- 解析対象画像の位置から、取得済みの視野内の既知天体の精密軌道情報があるかどうか検索する
- 実行内容
  1. FITS 画像ファイルを検索して順番に読み込み、赤経（RA）・赤緯（DEC）・ユリウス日（JD）を取得する
  2. 精密軌道情報のファイルがあれば読み込み、なければディレクトリを作成する

## src3_prempsearchC-before

### `prempsearchC-before`

- 視野内にある既知天体をリスト化し、精密位置を取得するシェルスクリプト（前半）
- 実行内容
  1. `have_all_precise_orbits.txt`を参照し、取得済みの位置データがない場合のみ取得操作を行う
  2. `searchB.py` 暗い既知天体を探索する
  3. `searchB_AstMPC.py` 明るい既知天体を探索する
  4. 結果を`cand.txt`にまとめ、整形する
  5. 確定番号付き小惑星の一覧を`cand3.txt`に、仮符号小惑星の一覧を`cand4.txt`に書き出す
  6. `make_asteroid_name_list_in_the_field.py` 既知小惑星の一覧を保存する
  7. `getinfo_numbered2D.py` 確定番号付き小惑星の詳細位置を取得して保存する

### `searchB.py`

- `~/.coias/param/AstMPC_dim.edb`に記載の**暗い**既知小惑星の一覧から、視野内にあるものを抽出す
- 実行内容
  1. FITS 画像ファイルを検索して順番に読み込み、赤経（RA）・赤緯（DEC）・ユリウス日（JD）を取得する
  2. 並列処理で、視野内（中心から ±1.8 度以内）の小惑星を`search()`関数で探索する
  - `search()`は、すばる望遠鏡の地点から天体の視方向を算出し、それが視野の範囲にあれば天体情報を返す
  - 計算には天体位置計算ライブラリ[PyEphem](https://rhodesmill.org/pyephem/index.html)を利用している
  3. 結果を`cand_dim.txt`に保存する

### `searchB_AstMPC.py`

- `~/.coias/param/AstMPC.edb`に記載の**明るい**既知小惑星の一覧から、視野内にあるものを抽出する
- 実行内容
  1. （`searchB.py`と同じ流れ）
  2. 天体名のみのリストを`bright_asteroid_raw_names_in_the_field.txt`に保存する

### `make_asteroid_name_list_in_the_field.py`

`

- 報告が不要な明るい小惑星を除外するためのリスト、および視野内の既知天体の名前のリストを作成する
- 実行内容
  1. `bright_asteroid_raw_names_in_the_field.txt`を整形して天体名を取り出す
  2. 天体名を MPC フォーマットのものに変換し、`brightAsteroidsMPCNames`配列に並べ、`bright_asteroid_MPC_names_in_the_field.txt`に保存する
  3. 全ての既知天体に対して、フルネーム、ショートネーム、MPC フォーマットの名前を配列に並べ、`name_conversion_list_in_the_field.txt`に保存する

### `getinfo_numbered2D.py`

- `cand3.txt`に記載された確定番号付き小惑星の精密位置を JPL に問い合わせる
- 実行内容
  1. `have_all_precise_orbits.txt`を参照し、取得済みの位置データがない場合のみ取得操作を行う
  2. `precise_orbit_directories`、FITS 画像、`cand3.txt`の読み込み
  3. 並列処理で、天体ごとに JPL への問い合わせを実行する（[astroquery.jplhorizons](https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html)を使用）
  4. エラーで取得できなかった天体に関して再度 JPL へ問い合わせる
  5. 取得できた位置情報を`/numbered_new2B.txt`に保存する

## src4_prempsearchC-after

### `prempsearchC-after`

- 視野内にある既知天体をリスト化し、精密位置を取得するシェルスクリプト（後半）
- 実行内容
  1. `getinfo_karifugo2D.py` 仮符号小惑星の詳細位置を取得して保存する
  2. `make_search_astB_in_each_directory.py` 既知天体の位置情報のファイルを整形し、`search_astB.txt`に出力する

### `getinfo_karifugo2D.py`

- `cand4.txt`に記載された仮符号小惑星の精密位置を JPL に問い合わせる
- 実行内容
  1. （`getinfo_numbered2D.py`と同じ流れ）
  2. 取得できた位置情報を`/karifugo_new2B.txt`に保存する
  3. 視野の中心と問い合わせ時刻を`ra_dec_jd_time.txt`に保存する

### `make_search_astB_in_each_directory.py`

- 既知天体の位置情報のファイルを整形し、`search_astB.txt`に出力する
- 実行内容
  1. `karifugo_new2B.txt`と`numbered_new2B.txt`を cat コマンドで結合する
  2. 整形したものを`search_astB.txt`に保存する

## src5_astsearch_new

### `astsearch_new`

## src6_between_COIAS_and_ReCOIAS

### `AstsearchR_between_COIAS_and_ReCOIAS`

## src7_AstsearchR_afterReCOIAS

### `AstsearchR_afterReCOIAS`

## src8_astsearch_manual

### `AstsearchR_after_manual`
