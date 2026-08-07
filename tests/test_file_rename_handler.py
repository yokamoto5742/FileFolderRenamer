import logging
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from watchdog.events import FileCreatedEvent, FileMovedEvent

from service.file_rename_handler import FileRenameHandler


@pytest.fixture
def handler():
    """FileRenameHandlerのインスタンスを提供"""
    return FileRenameHandler([re.compile(r"_[A-Za-z0-9]{6}$")], 0.1)


class TestFileRenameHandlerInit:
    """FileRenameHandlerの初期化テスト"""

    def test_init_stores_patterns_and_wait_time(self):
        """初期化時にパターンと待機時間を保持する"""
        handler = FileRenameHandler([re.compile(r"_[A-Za-z0-9]{6}$")], 0.1)
        assert len(handler.patterns) == 1
        assert handler.wait_time == 0.1

    def test_init_with_multiple_patterns(self):
        """複数パターンの初期化"""
        handler = FileRenameHandler([re.compile(r"_[A-Za-z0-9]{6}$"), re.compile(r"_tmp$")], 0.5)
        assert len(handler.patterns) == 2
        assert handler.wait_time == 0.5


class TestFileRenameHandlerEventHandling:
    """イベント処理のテスト"""

    def test_on_created_ignores_directory(self, handler):
        """ディレクトリ作成イベントは無視される"""
        event = FileCreatedEvent(r"C:\test\folder")
        event.is_directory = True

        with patch.object(handler, "_process_file") as mock_process:
            handler.on_created(event)
            mock_process.assert_not_called()

    def test_on_created_processes_file(self, handler):
        """ファイル作成イベントを処理する"""
        event = FileCreatedEvent(r"C:\test\file_ABC123.txt")
        event.is_directory = False

        with patch.object(handler, "_process_file") as mock_process:
            handler.on_created(event)
            mock_process.assert_called_once_with(r"C:\test\file_ABC123.txt")

    def test_on_moved_ignores_directory(self, handler):
        """ディレクトリ移動イベントは無視される"""
        event = FileMovedEvent(r"C:\old\folder", r"C:\test\folder")
        event.is_directory = True

        with patch.object(handler, "_process_file") as mock_process:
            handler.on_moved(event)
            mock_process.assert_not_called()

    def test_on_moved_processes_file(self, handler):
        """ファイル移動イベントを処理する"""
        event = FileMovedEvent(r"C:\old\file.txt", r"C:\test\file_ABC123.txt")
        event.is_directory = False

        with patch.object(handler, "_process_file") as mock_process:
            handler.on_moved(event)
            mock_process.assert_called_once_with(r"C:\test\file_ABC123.txt")


class TestFileRenameHandlerProcessFile:
    """ファイル処理のテスト"""

    def test_process_file_waits_before_processing(self, handler):
        """ファイル処理前に待機する"""
        with patch("time.sleep") as mock_sleep, patch("pathlib.Path.exists", return_value=False):
            handler._process_file(r"C:\test\file.txt")
            mock_sleep.assert_called_once_with(0.1)

    def test_process_file_returns_if_file_not_exists(self, handler):
        """ファイルが存在しない場合は処理をスキップ"""
        with patch("time.sleep"), patch.object(handler, "should_rename") as mock_should_rename:
            handler._process_file(r"C:\test\nonexistent.txt")
            mock_should_rename.assert_not_called()

    def test_process_file_renames_when_should_rename_true(self, handler):
        """リネーム対象の場合はリネームを実行"""
        test_path_str = r"C:\test\file_ABC123.txt"

        with (
            patch("time.sleep"),
            patch("pathlib.Path.exists", return_value=True),
            patch.object(handler, "should_rename", return_value=True),
            patch.object(handler, "rename_file") as mock_rename,
        ):
            handler._process_file(test_path_str)
            mock_rename.assert_called_once()

    def test_process_file_skips_when_should_rename_false(self, handler):
        """リネーム対象でない場合はスキップ"""
        test_path_str = r"C:\test\normalfile.txt"

        with (
            patch("time.sleep"),
            patch("pathlib.Path.exists", return_value=True),
            patch.object(handler, "should_rename", return_value=False),
            patch.object(handler, "rename_file") as mock_rename,
        ):
            handler._process_file(test_path_str)
            mock_rename.assert_not_called()


class TestFileRenameHandlerShouldRename:
    """リネーム判定のテスト"""

    def test_should_rename_matches_single_pattern(self, handler):
        """単一パターンにマッチする場合はTrue"""
        assert handler.should_rename("file_ABC123") is True

    def test_should_rename_does_not_match(self, handler):
        """パターンにマッチしない場合はFalse"""
        assert handler.should_rename("normalfile") is False

    def test_should_rename_with_multiple_patterns(self):
        """複数パターンのいずれかにマッチする場合はTrue"""
        handler = FileRenameHandler([re.compile(r"_[A-Za-z0-9]{6}$"), re.compile(r"_tmp$")], 0.1)

        assert handler.should_rename("file_ABC123") is True
        assert handler.should_rename("file_tmp") is True
        assert handler.should_rename("normalfile") is False

    def test_should_rename_pattern_at_end(self, handler):
        """パターンが末尾にある場合のみマッチ"""
        # パターンは末尾マッチなので_ABC123が末尾にある場合はマッチ
        assert handler.should_rename("file_ABC123") is True
        # _suffixも6文字なのでパターンにマッチ（末尾が_+英数6文字）
        assert handler.should_rename("file_ABC123_suffix") is True
        # prefixがあってもパターンが末尾にあればマッチ
        assert handler.should_rename("prefix_file_ABC123") is True
        # 末尾が5文字以下の場合はマッチしない
        assert handler.should_rename("file_ABC12") is False
        # 末尾に_がない場合はマッチしない
        assert handler.should_rename("fileABC123") is False


class TestFileRenameHandlerRenameFile:
    """ファイルリネームのテスト"""

    def test_rename_file_removes_pattern(self, handler, caplog):
        """パターンを削除してリネーム"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"

        with patch("pathlib.Path.exists", return_value=False), caplog.at_level(logging.INFO):
            handler.rename_file(mock_path, "file_ABC123", ".txt")
            mock_path.rename.assert_called_once()
            assert "リネーム完了" in caplog.text

    def test_rename_file_handles_duplicate_with_counter(self, handler):
        """重複ファイル名の場合は連番を付与"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"

        # 最初の2つは存在するが、3つ目は存在しない
        exists_results = [True, True, False]
        with patch("pathlib.Path.exists", side_effect=exists_results):
            handler.rename_file(mock_path, "file_ABC123", ".txt")

            # file (2).txtにリネームされる
            expected_path = Path(r"C:\test\file (2).txt")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_rename_file_handles_permission_error(self, handler, caplog):
        """PermissionErrorを適切に処理"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"
        mock_path.rename.side_effect = PermissionError

        with patch("pathlib.Path.exists", return_value=False), caplog.at_level(logging.ERROR):
            handler.rename_file(mock_path, "file_ABC123", ".txt")
            assert "ファイルにアクセスできません" in caplog.text

    def test_rename_file_handles_os_error(self, handler, caplog):
        """OSErrorを適切に処理"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"
        mock_path.rename.side_effect = OSError("Test error")

        with patch("pathlib.Path.exists", return_value=False), caplog.at_level(logging.ERROR):
            handler.rename_file(mock_path, "file_ABC123", ".txt")
            assert "リネーム失敗" in caplog.text

    def test_rename_file_with_multiple_patterns(self):
        """複数パターンを削除してリネーム"""
        handler = FileRenameHandler([re.compile(r"_tmp$"), re.compile(r"_[A-Za-z0-9]{6}$")], 0.1)

        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123_tmp.txt"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "file_ABC123_tmp", ".txt")

            # 両方のパターンが削除される
            expected_path = Path(r"C:\test\file.txt")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_rename_file_preserves_extension(self, handler):
        """拡張子を保持してリネーム"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "document_ABC123.pdf"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "document_ABC123", ".pdf")

            expected_path = Path(r"C:\test\document.pdf")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_rename_file_increments_counter_correctly(self, handler):
        """連番が正しくインクリメントされる"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"

        # 最初の5つは存在し、6つ目は存在しない
        exists_results = [True, True, True, True, True, False]
        with patch("pathlib.Path.exists", side_effect=exists_results):
            handler.rename_file(mock_path, "file_ABC123", ".txt")

            # file (5).txtにリネームされる
            expected_path = Path(r"C:\test\file (5).txt")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_rename_file_with_no_extension(self, handler):
        """拡張子のないファイルをリネーム"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "file_ABC123", "")

            expected_path = Path(r"C:\test\file")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_rename_file_with_long_extension(self, handler):
        """長い拡張子のファイルをリネーム"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "archive_ABC123.tar.gz"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "archive_ABC123", ".tar.gz")

            expected_path = Path(r"C:\test\archive.tar.gz")
            mock_path.rename.assert_called_once_with(expected_path)


class TestFileRenameHandlerEdgeCases:
    """エッジケースのテスト"""

    def test_empty_patterns_list(self):
        """パターンが空の場合"""
        handler = FileRenameHandler([], 0.1)
        assert handler.should_rename("any_filename") is False

    def test_zero_wait_time(self):
        """待機時間が0の場合"""
        handler = FileRenameHandler([re.compile(r"_test$")], 0.0)

        with (
            patch("time.sleep") as mock_sleep,
            patch("pathlib.Path.exists", return_value=False),
        ):
            handler._process_file(r"C:\test\file.txt")
            mock_sleep.assert_called_once_with(0.0)

    def test_pattern_removes_entire_filename(self):
        """パターンがファイル名全体にマッチする場合"""
        # ファイル名全体を削除するパターン
        handler = FileRenameHandler([re.compile(r"^file_ABC123$")], 0.1)

        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file_ABC123.txt"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "file_ABC123", ".txt")

            # 空のファイル名になる
            expected_path = Path(r"C:\test\.txt")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_unicode_filename(self, handler):
        """Unicode文字を含むファイル名の処理"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "日本語ファイル_ABC123.txt"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "日本語ファイル_ABC123", ".txt")

            expected_path = Path(r"C:\test\日本語ファイル.txt")
            mock_path.rename.assert_called_once_with(expected_path)

    def test_special_characters_in_filename(self, handler):
        """特殊文字を含むファイル名の処理"""
        mock_path = MagicMock(spec=Path)
        mock_path.parent = Path(r"C:\test")
        mock_path.name = "file-name (with spaces)_ABC123.txt"

        with patch("pathlib.Path.exists", return_value=False):
            handler.rename_file(mock_path, "file-name (with spaces)_ABC123", ".txt")

            expected_path = Path(r"C:\test\file-name (with spaces).txt")
            mock_path.rename.assert_called_once_with(expected_path)


class TestFileRenameHandlerProcessExistingFiles:
    """起動時の既存ファイル処理のテスト"""

    def test_renames_existing_files(self, handler, tmp_path):
        """既存ファイルがリネームされる"""
        (tmp_path / "report_ABC123.txt").write_text("x", encoding="utf-8")

        handler.process_existing_files(str(tmp_path))

        assert (tmp_path / "report.txt").exists()
        assert not (tmp_path / "report_ABC123.txt").exists()

    def test_skips_non_matching_files(self, handler, tmp_path):
        """パターンに一致しないファイルはそのまま残る"""
        (tmp_path / "report.txt").write_text("x", encoding="utf-8")

        handler.process_existing_files(str(tmp_path))

        assert (tmp_path / "report.txt").exists()

    def test_skips_directories(self, handler, tmp_path):
        """ディレクトリは処理対象外"""
        (tmp_path / "folder_ABC123").mkdir()

        handler.process_existing_files(str(tmp_path))

        assert (tmp_path / "folder_ABC123").is_dir()

    def test_does_not_wait(self, handler, tmp_path):
        """既存ファイル処理では書き込み完了待ちを行わない"""
        (tmp_path / "report_ABC123.txt").write_text("x", encoding="utf-8")

        with patch("time.sleep") as mock_sleep:
            handler.process_existing_files(str(tmp_path))
            mock_sleep.assert_not_called()

    def test_empty_directory(self, handler, tmp_path):
        """空のディレクトリでも例外が発生しない"""
        handler.process_existing_files(str(tmp_path))
