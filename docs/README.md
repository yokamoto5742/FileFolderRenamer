# FileFolderRenamer

Windowsシステムトレイアプリケーション。監視ディレクトリに作成・移動されたファイルのファイル名から特定のパターン（例：`_ABC123`サフィックス）を自動的に削除してリネームします。

## 概要

FileFolderRenamerは、指定されたディレクトリを監視し、ファイルの作成・移動イベントを検知して正規表現パターンに基づく自動リネーム機能を提供するWindowsアプリケーションです。システムトレイに常駐し、バックグラウンドで動作します。

**現在のバージョン**: 1.0.0
**最終更新日**: 2025年12月24日

### 主な特徴

- Windowsシステムトレイで常駐実行
- 複数の正規表現パターンに対応
- ファイル書き込み完了待ちの自動調整
- 既存ファイルとの名前衝突対策（自動連番付与）
- 詳細なログ記録と自動ローテーション
- デバッグモード対応

## 必要な環境

### 開発環境

- Python 3.13以上
- Windows 11

### 実行環境

- Windows 11
- Python 3.13以上（開発環境の場合）

### 依存パッケージ

主な依存パッケージ：
- `watchdog` (6.0.0): ファイルシステム監視
- `pystray` (0.19.5): Windowsシステムトレイ統合
- `pillow` (12.0.0): アイコン画像生成

詳細は `requirements.txt` を参照してください。

## インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/your-username/FileFolderRenamer.git
cd FileFolderRenamer
```

### 2. Python仮想環境を作成・有効化

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. 設定ファイルを編集

`utils/config.ini` を開き、監視対象フォルダと正規表現パターンを設定します：

```ini
[Paths]
src_dir = C:\Users\your-name\Desktop\target-folder

[Rename]
pattern1 = _test_[A-Za-z0-9]{6}$
pattern2 = _[A-Za-z0-9]{6}$

[App]
wait_time = 0.5

[LOGGING]
log_retention_days = 7
log_directory = logs
log_level = INFO
debug_mode = False
project_name = FileFolderRenamer
```

### 5. アプリケーションを実行

```bash
python main.py
```

## 使用方法

### 基本的な動作

1. アプリケーションを起動すると、Windowsのシステムトレイに青いファイルアイコンが表示されます。
2. 設定した監視フォルダにファイルが作成・移動されると、自動的にリネーム処理が行われます。
3. リネームの詳細はログファイル（`logs/FileFolderRenamer.log`）で確認できます。

### システムトレイメニュー

- **監視中: フォルダ名**: 現在の監視状態を表示
- **監視フォルダを開く**: エクスプローラーで監視フォルダを開く
- **終了**: アプリケーションを終了

### 設定例

#### 例1: 特定の接尾辞を削除

ファイル名から `_ABC123` を削除したい場合：

```ini
[Rename]
pattern1 = _[A-Za-z0-9]{6}$
```

リネーム例：
- `document_ABC123.pdf` → `document.pdf`
- `image_XYZ789.jpg` → `image.jpg`

#### 例2: 複数パターンを指定

複数の異なるパターンを適用する場合：

```ini
[Rename]
pattern1 = _magnate_[A-Za-z0-9]{6}$
pattern2 = \(copy\)$
```

リネーム例：
- `file_magnate_ABC123.txt` → `file.txt`
- `document (copy).pdf` → `document.pdf`

## プロジェクト構成

```
FileFolderRenamer/
├── main.py                          # エントリーポイント
├── build.py                         # PyInstallerビルドスクリプト
├── requirements.txt                 # 依存パッケージリスト
├── pyrightconfig.json               # 型チェッカー設定
├── CLAUDE.md                        # 開発ガイドライン
│
├── app/                             # アプリケーションコア
│   ├── __init__.py                  # バージョン情報
│   └── tray_app.py                  # TrayAppクラス（システムトレイ管理）
│
├── service/                         # ファイル処理サービス
│   └── file_rename_handler.py       # FileRenameHandlerクラス（リネーム処理）
│
├── utils/                           # ユーティリティモジュール
│   ├── config.ini                   # 設定ファイル
│   ├── config_manager.py            # 設定ファイル読み込み
│   └── log_rotation.py              # ログ管理・ローテーション
│
├── scripts/                         # ビルドスクリプト
│   └── version_manager.py           # バージョン管理
│
├── tests/                           # テストコード
│   ├── test_file_rename_handler.py  # FileRenameHandlerのテスト
│   └── test_tray_app.py             # TrayAppのテスト
│
├── docs/                            # ドキュメント
│   ├── README.md                    # このファイル
│   ├── CHANGELOG.md                 # 変更履歴
│   └── LICENSE                      # ライセンス
│
└── logs/                            # ログディレクトリ（自動作成）
    └── FileFolderRenamer.log        # アプリケーションログ
```

## 機能説明

### TrayApp クラス (`app/tray_app.py`)

Windowsシステムトレイの管理とファイル監視の開始・停止を担当します。

**主なメソッド**：
- `run()`: アプリケーション実行
- `start_watching()`: ファイル監視を開始
- `stop_watching()`: ファイル監視を停止
- `_create_icon_image()`: トレイアイコン画像を生成

```python
from app.tray_app import TrayApp

app = TrayApp()
app.run()  # メインスレッドをブロック
```

### FileRenameHandler クラス (`service/file_rename_handler.py`)

watchdogを用いてファイルシステムイベントを監視し、リネーム処理を実行します。

**主なメソッド**：
- `on_created(event)`: ファイル作成イベント処理
- `on_moved(event)`: ファイル移動イベント処理
- `should_rename(filename)`: リネーム対象判定
- `rename_file(file_path, filename, extension)`: リネーム実行

```python
from service.file_rename_handler import FileRenameHandler

handler = FileRenameHandler()
# 自動的にファイル作成・移動イベントを監視
```

### 設定管理 (`utils/config_manager.py`)

設定ファイルの読み込みと値の取得を行います。

**主な関数**：
- `get_src_dir()`: 監視フォルダパスを取得
- `get_rename_patterns()`: 正規表現パターンリストを取得
- `get_wait_time()`: ファイル書き込み待機時間を取得（秒）

```python
from utils.config_manager import get_src_dir, get_rename_patterns

src_dir = get_src_dir()
patterns = get_rename_patterns()
```

### ログ管理 (`utils/log_rotation.py`)

ロギング設定、ログファイルのローテーション、古いログの自動削除を担当します。

**主な関数**：
- `setup_logging()`: ロギングを初期化
- `cleanup_old_logs()`: 古いログファイルを削除
- `setup_debug_logging()`: デバッグモードを有効化

```python
from utils.log_rotation import setup_logging

setup_logging()  # ロギング初期化
```

## 開発

### テストの実行

```bash
python -m pytest tests/ -v
```

型チェック：
```bash
pyright
```

### 実行ファイルのビルド

```bash
python build.py
```

このコマンドは以下の処理を実行します：
1. `app/__init__.py` のバージョン番号をパッチ版として自動インクリメント
2. `docs/README.md` のバージョン情報を更新
3. PyInstallerを使用してWindows実行ファイル（`dist/FileFolderRenamer.exe`）を生成

## トラブルシューティング

### 監視フォルダが見つからない

```
Error: 監視フォルダが存在しません: C:\path\to\folder
```

**原因**: `utils/config.ini` に指定したパスが存在しません。

**解決方法**:
1. `utils/config.ini` を開く
2. `[Paths]` セクションの `src_dir` を正しいパスに修正
3. アプリケーションを再起動

### ファイルが自動リネームされない

**原因**: 正規表現パターンがファイル名と一致していません。

**解決方法**:
1. `utils/config.ini` の `[Rename]` セクションを確認
2. パターンが正しいか検証（`logs/FileFolderRenamer.log` でログを確認）
3. 必要に応じて正規表現パターンを修正

例：`_ABC123` を削除するなら、パターンは `_[A-Za-z0-9]{6}$` など

### ログファイルが見つからない

**原因**: ログディレクトリが作成されていません。

**解決方法**:
1. `utils/config.ini` で `log_directory` を確認
2. ディレクトリが存在しない場合は、初回実行時に自動作成されます
3. ディレクトリ作成権限がない場合は、パスを変更してください

### アプリケーションが起動しない

**原因**: 設定ファイルのエラーまたは依存パッケージが不足しています。

**解決方法**:
```bash
# 依存パッケージの再インストール
pip install -r requirements.txt

# アプリケーションをデバッグモードで実行
python main.py
```

## ライセンス

このプロジェクトのライセンス情報については、 [LICENSE](./LICENSE) を参照してください。

## 更新履歴

更新履歴は [CHANGELOG.md](./CHANGELOG.md) を参照
