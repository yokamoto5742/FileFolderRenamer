# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

FileFolderRenamer は、監視対象ディレクトリ内のファイルを、ファイル名から特定のパターン（例: `_ABC123` のような接尾辞）を除去して自動リネームする Windows 用システムトレイアプリケーション。`watchdog` でファイルシステムを監視し、`pystray` でシステムトレイ機能を提供する。

## アーキテクチャ

- `main.py` — エントリーポイント。ログ設定後に `TrayApp().run()` を呼ぶだけ。
- `app/tray_app.py` — `TrayApp`。pystray を使ったトレイアプリ本体で、`start_watching()` 内で `FileRenameHandler` を生成する。
- `service/file_rename_handler.py` — `FileRenameHandler`。watchdog のイベントハンドラで、設定されたパターンにマッチしたファイル/フォルダをリネームする。
- `utils/config_manager.py` — `utils/config.ini` から設定を読み込む。PyInstaller でフリーズされた実行環境（`sys._MEIPASS`）と開発環境の両方のパスに対応。

### config.ini の設定項目

- `[Watch1]`, `[Watch2]`, ... — 監視対象。連番セクションで複数指定でき、`get_watch_targets()` がセクション番号順に読み込む。単一の `Observer` にまとめて登録される
  - `src_dir` — 監視対象ディレクトリ。同じディレクトリが複数セクションに現れた場合、2つ目以降は警告ログを出してスキップされる
  - `pattern1, pattern2, ...` — 除去する正規表現パターン（末尾に `$` が無い場合は自動付与され、長いパターンから優先的にマッチする）。パターンはセクションごとに独立しており、そのディレクトリで検知したファイルにのみ適用される
- `[App] wait_time` — ファイル検知後の処理待機秒数（デフォルト 0.5、全監視対象で共通）
- `[LOGGING]` — `log_retention_days` / `log_directory` / `log_level` / `debug_mode` / `project_name`

起動時、各監視対象ディレクトリに既に存在するファイルは `FileRenameHandler.process_existing_files()` で処理される（`Observer` 開始後に実行し、取りこぼしを防ぐ）。

## コマンド

```bash
# アプリを起動
python main.py

# 実行可能ファイルをビルド（PyInstaller のみ実行。バージョン更新やREADME更新は行わない）
python build.py
```

パッケージ管理は `uv`（`uv.lock` あり）。README.md に記載の `pip install -r requirements.txt` は古い記述で、`requirements.txt` は存在しない。

## Lint / Format

`ruff` が唯一の実際に強制されているリンター/フォーマッター（`pyproject.toml` の `[tool.ruff]`）。`.py` ファイルの Write/Edit 後には `ruff format` が PostToolUse フックで自動実行される。

## 既知のドキュメント不整合

- バージョン番号が `pyproject.toml`（1.1.0）と README/CHANGELOG（1.0.0）で食い違っている。`app/__init__.py` は空でバージョン定数は存在しない。CLAUDE.md や新規コードで特定のバージョン番号を前提にしないこと。
- README.md のプロジェクト構成図は `scripts/version_manager.py` など既に削除されたファイルを記載しており古い。
