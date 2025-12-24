# チェンジログ

このプロジェクトの主な変更は、このファイルに記録されています。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/lang/ja/) に従っています。

## [Unreleased]

## [1.0.0] - 2025-12-24

### 追加

- ファイルパスの型ヒント（`bytes | str`）を追加
- エッジケースのテストケースを追加
- ログ設定とクリーンアップ機能の型ヒントを追加

### 変更

- ファイルパスの型ヒント（`bytes | str`）に変更
- 設定値取得時にNoneチェックを明示的に実施
- ログローテーション設定値取得時にNoneチェックとデフォルト値を明確化

### 修正

- 設定値取得時のNoneチェック処理を追加

## [0.9.0] - 2025-12-24

### 変更

- タスクトレイアイコンの名称とタイトルを更新
- ライセンスの著作権年を更新

## [0.8.0] - 2025-12-22

### 追加

- 複数のリネームパターンを取得・適用する機能を追加
- 設定値取得ヘルパー関数を追加
- ログ出力機能を追加

### 変更

- ファイル名パターン取得キーを 'pattern' から 'pattern1' に変更
- パターン1とパターン2の順序を入れ替え
- 既存ファイル名に連番を付与するロジック

## [0.7.0] - 2025-12-22

### 追加

- ログ設定とファイル名パターン設定を追加
- ログローテーションとクリーンアップ機能を追加

### 変更

- 環境変数読み込みを廃止し、設定ファイル読み込みを実装
- ログ設定関連関数を追加

## [0.6.0] - 2025-12-17

### 変更

- ファイル監視ロジックを抽出し、タスクトレイアプリとして再構成

## [0.5.0] - 2025-12-16

### 削除

- ファイル監視とタスクトレイ機能を削除（リアーキテクチャ用）

### 変更

- バージョンと日付を更新

## [0.4.0] - 2025-12-16

### 追加

- ファイル監視とタスクトレイ機能を追加

## [0.3.0] - 2025-12-16

### 変更

- 設定ファイル内のパス名を変更

## [0.2.0] - 2025-12-16

### 削除

- ログローテーション関連のコードを削除

## [0.1.0] - 2025-12-16

### 追加

- 初期リリース

---

[Unreleased]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yokamoto5742/FileFolderRenamer/releases/tag/v0.1.0
