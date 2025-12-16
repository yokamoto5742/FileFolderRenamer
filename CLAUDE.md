# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Project Overview

FileFolderRenamer is a Windows system tray application that automatically renames files in a watched directory by removing specific patterns from filenames (e.g., removing `_ABC123` suffixes). Built with Python using watchdog for file system monitoring and pystray for system tray functionality.

## Commands

### Run the application
```bash
python main.py
```

### Run tests
```bash
python -m pytest tests/ -v
```

### Build executable
```bash
python build.py
```
This increments the version in `app/__init__.py`, updates `docs/README.md`, and builds a Windows executable using PyInstaller.

## Architecture

```
FileFolderRenamer/
├── main.py              # Entry point - TrayApp and FileRenameHandler classes
├── build.py             # PyInstaller build script with version management
├── app/
│   └── __init__.py      # Version (__version__, __date__)
├── utils/
│   ├── config_manager.py  # Configuration loading from config.ini
│   └── config.ini         # User settings (watch path, rename pattern, wait_time)
├── scripts/
│   └── version_manager.py # Automatic version increment on build
└── tests/
```

### Key Components

- **FileRenameHandler** (`main.py`): Watchdog event handler that processes file create/move events and renames files matching the configured regex pattern
- **TrayApp** (`main.py`): System tray application using pystray with menu for opening watch folder and quitting
- **config_manager** (`utils/config_manager.py`): Loads settings from `utils/config.ini` using configparser

### Configuration

Settings in `utils/config.ini`:
- `[Paths].src_dir`: Directory to monitor for file changes
- `[Rename].pattern`: Regex pattern to remove from filenames (default: `_[A-Za-z0-9]{6}$`)
- `[App].wait_time`: Delay before processing files (default: 0.5 seconds)

## Language

This project uses Japanese for comments, docstrings, and user-facing messages.
