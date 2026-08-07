import logging
import re
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from watchdog.observers import Observer

from app.tray_app import TrayApp
from utils.config_manager import WatchTarget


def make_target(src_dir: str, pattern: str = r"_[A-Za-z0-9]{6}$") -> WatchTarget:
    """テスト用の監視対象を生成"""
    return WatchTarget(src_dir=src_dir, patterns=[re.compile(pattern)])


@pytest.fixture
def mock_config():
    """設定のモックを提供（単一の監視対象）"""
    with (
        patch("app.tray_app.get_watch_targets") as mock_targets,
        patch("app.tray_app.get_wait_time") as mock_wait_time,
    ):
        mock_targets.return_value = [make_target(r"C:\test\src")]
        mock_wait_time.return_value = 0.5
        yield mock_targets


@pytest.fixture
def mock_multi_config():
    """設定のモックを提供（複数の監視対象）"""
    with (
        patch("app.tray_app.get_watch_targets") as mock_targets,
        patch("app.tray_app.get_wait_time") as mock_wait_time,
    ):
        mock_targets.return_value = [
            make_target(r"C:\test\src1", r"_magnate_[A-Za-z0-9]{6}$"),
            make_target(r"C:\test\src2", r"_sales_[A-Za-z0-9]{4}$"),
        ]
        mock_wait_time.return_value = 0.5
        yield mock_targets


@pytest.fixture
def mock_observer():
    """Observerのモックを提供"""
    with patch("app.tray_app.Observer") as mock_obs:
        yield mock_obs


@pytest.fixture
def mock_pystray():
    """pystrayのモックを提供"""
    with patch("app.tray_app.pystray") as mock_ps:
        yield mock_ps


@pytest.fixture
def mock_subprocess():
    """subprocessのモックを提供"""
    with patch("app.tray_app.subprocess") as mock_sp:
        yield mock_sp


class TestTrayAppInit:
    """TrayAppの初期化テスト"""

    def test_init_success(self, mock_config):
        """正常な初期化"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            assert len(app.targets) == 1
            assert app.targets[0].src_dir == r"C:\test\src"
            assert app.wait_time == 0.5
            assert app.observer is None
            assert app.icon is None

    def test_init_with_multiple_targets(self, mock_multi_config):
        """複数の監視対象を読み込む"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            assert [target.src_dir for target in app.targets] == [
                r"C:\test\src1",
                r"C:\test\src2",
            ]

    def test_init_with_missing_src_dir(self, mock_config):
        """監視フォルダが存在しない場合はsys.exitを呼ぶ"""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(SystemExit) as excinfo:
                TrayApp()
            assert excinfo.value.code == 1

    def test_validate_src_dir_logs_error(self, mock_config, caplog):
        """監視フォルダが存在しない場合のログ出力"""
        with patch("os.path.exists", return_value=False):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    TrayApp()
            assert "監視フォルダが存在しません" in caplog.text

    def test_validate_logs_every_missing_dir(self, mock_multi_config, caplog):
        """存在しない監視フォルダを全てログ出力する"""
        with patch("os.path.exists", return_value=False):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    TrayApp()
            assert r"C:\test\src1" in caplog.text
            assert r"C:\test\src2" in caplog.text

    def test_validate_exits_when_one_dir_is_missing(self, mock_multi_config):
        """一部の監視フォルダが存在しない場合も終了する"""
        with patch("os.path.exists", side_effect=[True, False]):
            with pytest.raises(SystemExit) as excinfo:
                TrayApp()
            assert excinfo.value.code == 1


class TestTrayAppIconCreation:
    """アイコン作成のテスト"""

    def test_create_icon_image_returns_pil_image(self, mock_config):
        """アイコン画像が正しく作成される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            image = app._create_icon_image()
            assert isinstance(image, Image.Image)
            assert image.size == (64, 64)
            assert image.mode == "RGBA"


class TestTrayAppFolderOperations:
    """フォルダ操作のテスト"""

    def test_open_folder_calls_subprocess(self, mock_config, mock_subprocess):
        """監視フォルダを開く処理が正しく実行される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app._open_folder(r"C:\test\src")
            mock_subprocess.Popen.assert_called_once_with(["explorer", r"C:\test\src"])


class TestTrayAppQuitApp:
    """アプリケーション終了のテスト"""

    def test_quit_app_stops_observer_and_icon(self, mock_config, caplog):
        """終了時にobserverとiconを停止"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = MagicMock(spec=Observer)
            app.icon = MagicMock()

            with caplog.at_level(logging.INFO):
                app._quit_app()

            app.observer.stop.assert_called_once()
            app.observer.join.assert_called_once()
            app.icon.stop.assert_called_once()
            assert "アプリケーションを終了します" in caplog.text

    def test_quit_app_without_icon(self, mock_config):
        """iconがNoneの場合でも正常終了"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = MagicMock(spec=Observer)
            app.icon = None

            app._quit_app()
            app.observer.stop.assert_called_once()

    def test_quit_app_without_observer(self, mock_config):
        """observerがNoneの場合でも正常終了"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = None
            app.icon = MagicMock()

            app._quit_app()
            app.icon.stop.assert_called_once()


class TestTrayAppMenu:
    """メニュー作成のテスト"""

    def test_create_menu_structure(self, mock_config, mock_pystray):
        """メニューが正しい構造で作成される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app._create_menu()

            assert mock_pystray.Menu.called
            assert mock_pystray.MenuItem.called

    def test_menu_displays_target_count(self, mock_multi_config, mock_pystray):
        """メニューに監視対象の件数が表示される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app._create_menu()

            texts = [call.kwargs["text"] for call in mock_pystray.MenuItem.call_args_list]
            assert "監視中: 2件" in texts

    def test_folder_submenu_lists_every_target(self, mock_multi_config, mock_pystray):
        """サブメニューに全監視フォルダが列挙される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app._create_folder_submenu()

            texts = [call.kwargs["text"] for call in mock_pystray.MenuItem.call_args_list]
            assert texts == ["src1", "src2"]

    def test_folder_submenu_actions_open_own_folder(
        self, mock_multi_config, mock_pystray, mock_subprocess
    ):
        """サブメニューの各アクションが対応するフォルダを開く"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app._create_folder_submenu()

            actions = [call.kwargs["action"] for call in mock_pystray.MenuItem.call_args_list]
            actions[1](MagicMock())
            mock_subprocess.Popen.assert_called_once_with(["explorer", r"C:\test\src2"])


class TestTrayAppWatching:
    """ファイル監視のテスト"""

    def test_start_watching_creates_observer(self, mock_config, mock_observer, caplog):
        """ファイル監視が正しく開始される"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.FileRenameHandler"):
                app = TrayApp()

                with caplog.at_level(logging.INFO):
                    app.start_watching()

                mock_observer.assert_called_once()
                observer_instance = mock_observer.return_value
                observer_instance.schedule.assert_called_once()
                observer_instance.start.assert_called_once()
                assert "フォルダ監視を開始しました" in caplog.text

    def test_start_watching_schedules_every_target(self, mock_multi_config, mock_observer):
        """監視対象ごとに単一のObserverへ登録される"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.FileRenameHandler"):
                app = TrayApp()
                app.start_watching()

                mock_observer.assert_called_once()
                observer_instance = mock_observer.return_value
                assert observer_instance.schedule.call_count == 2
                scheduled_dirs = [
                    call.args[1] for call in observer_instance.schedule.call_args_list
                ]
                assert scheduled_dirs == [r"C:\test\src1", r"C:\test\src2"]

    def test_start_watching_passes_section_patterns(self, mock_multi_config, mock_observer):
        """各ハンドラにセクション固有のパターンが渡される"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.FileRenameHandler") as mock_handler:
                app = TrayApp()
                app.start_watching()

                passed_patterns = [call.args[0] for call in mock_handler.call_args_list]
                assert passed_patterns[0] == app.targets[0].patterns
                assert passed_patterns[1] == app.targets[1].patterns
                # wait_time は全監視対象で共通
                assert all(call.args[1] == 0.5 for call in mock_handler.call_args_list)

    def test_start_watching_processes_existing_files(self, mock_multi_config, mock_observer):
        """監視開始後に既存ファイルを処理する"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.FileRenameHandler") as mock_handler:
                handler_instances = [MagicMock(), MagicMock()]
                mock_handler.side_effect = handler_instances

                app = TrayApp()
                app.start_watching()

                handler_instances[0].process_existing_files.assert_called_once_with(r"C:\test\src1")
                handler_instances[1].process_existing_files.assert_called_once_with(r"C:\test\src2")

    def test_stop_watching_stops_observer(self, mock_config, caplog):
        """ファイル監視が正しく停止される"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = MagicMock(spec=Observer)

            with caplog.at_level(logging.INFO):
                app.stop_watching()

            app.observer.stop.assert_called_once()
            app.observer.join.assert_called_once()
            assert "フォルダ監視を停止しました" in caplog.text

    def test_stop_watching_without_observer(self, mock_config):
        """observerがNoneの場合でも正常終了"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = None
            # 例外が発生しないことを確認
            app.stop_watching()


class TestTrayAppRun:
    """アプリケーション実行のテスト"""

    def test_run_starts_thread_and_icon(self, mock_config, mock_pystray):
        """runメソッドがスレッドとアイコンを起動"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.threading.Thread") as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance
                mock_icon_instance = MagicMock()
                mock_pystray.Icon.return_value = mock_icon_instance

                app = TrayApp()
                app.run()

                # スレッドが作成され、daemon=Trueで開始されることを確認
                mock_thread.assert_called_once()
                call_kwargs = mock_thread.call_args[1]
                assert call_kwargs["daemon"] is True
                mock_thread_instance.start.assert_called_once()

                # アイコンが作成され実行されることを確認
                mock_pystray.Icon.assert_called_once()
                mock_icon_instance.run.assert_called_once()

    def test_run_creates_icon_with_correct_params(self, mock_config, mock_pystray):
        """アイコンが正しいパラメータで作成される"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.threading.Thread"):
                mock_icon_instance = MagicMock()
                mock_pystray.Icon.return_value = mock_icon_instance

                app = TrayApp()
                app.run()

                # Icon呼び出しの引数を確認
                call_kwargs = mock_pystray.Icon.call_args[1]
                assert call_kwargs["name"] == "FileFolderRenamer"
                assert call_kwargs["title"] == "FileFolderRenamer"
                assert "icon" in call_kwargs
                assert "menu" in call_kwargs


class TestTrayAppEdgeCases:
    """エッジケースのテスト"""

    def test_open_folder_with_unicode_path(self, mock_config, mock_subprocess):
        """Unicode文字を含むパスでフォルダを開く"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()

            app._open_folder(r"C:\test\日本語フォルダ")
            mock_subprocess.Popen.assert_called_once_with(["explorer", r"C:\test\日本語フォルダ"])

    def test_quit_app_without_observer_and_icon(self, mock_config):
        """observerもiconもNoneの場合でも正常終了"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = None
            app.icon = None

            # 例外が発生しないことを確認
            app._quit_app()

    def test_stop_watching_called_multiple_times(self, mock_config):
        """stop_watchingを複数回呼び出しても問題ない"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = MagicMock(spec=Observer)

            app.stop_watching()
            # observerは停止後にNoneにならないため、2回目は同じobserverに対して呼ばれる
            # 実装上は問題ないことを確認
            app.stop_watching()

    def test_create_icon_image_properties(self, mock_config):
        """アイコン画像の詳細なプロパティを確認"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            image = app._create_icon_image()

            # 画像の基本プロパティ
            assert image.size == (64, 64)
            assert image.mode == "RGBA"
            # 画像が完全に透明でないことを確認（何かが描画されている）
            assert image.getbbox() is not None

    def test_validate_src_dir_with_network_path(self, mock_config):
        """ネットワークパスが存在しない場合"""
        with patch("os.path.exists", return_value=False):
            mock_config.return_value = [make_target(r"\\network\share\folder")]
            with pytest.raises(SystemExit) as excinfo:
                TrayApp()
            assert excinfo.value.code == 1

    def test_start_watching_with_already_started_observer(self, mock_config, mock_observer):
        """既にobserverが存在する場合の処理"""
        with patch("os.path.exists", return_value=True):
            with patch("app.tray_app.FileRenameHandler"):
                app = TrayApp()
                app.observer = MagicMock(spec=Observer)
                old_observer = app.observer

                # start_watchingを再度呼び出すと新しいobserverが作成される
                app.start_watching()

                # 古いobserverは置き換えられる
                assert app.observer != old_observer

    def test_menu_callback_functions(self, mock_config, mock_subprocess):
        """メニューのコールバック関数が正しく動作"""
        with patch("os.path.exists", return_value=True):
            app = TrayApp()
            app.observer = MagicMock(spec=Observer)
            app.icon = MagicMock()

            # フォルダを開くコールバック
            app._open_folder(r"C:\test\src")
            mock_subprocess.Popen.assert_called_once()

            # 終了コールバック
            app._quit_app()
            app.observer.stop.assert_called_once()
            app.icon.stop.assert_called_once()
