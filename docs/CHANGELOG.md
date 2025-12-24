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

---

[Unreleased]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yokamoto5742/FileFolderRenamer/compare/v0.9.0...v1.0.0
