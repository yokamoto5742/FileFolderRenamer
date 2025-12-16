import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pystray
from PIL import Image, ImageDraw
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from utils.config_manager import get_rename_pattern, get_src_dir, get_wait_time


class FileRenameHandler(FileSystemEventHandler):
    """ファイルシステムイベントを処理し、ファイル名を変換するハンドラー"""

    def __init__(self):
        super().__init__()
        self.pattern = get_rename_pattern()
        self.wait_time = get_wait_time()

    def on_created(self, event):
        """新規ファイル作成時の処理"""
        if event.is_directory:
            return
        self._process_file(event.src_path)

    def on_moved(self, event):
        """ファイル移動時の処理（フォルダに移動されてきたファイル）"""
        if event.is_directory:
            return
        self._process_file(event.dest_path)

    def _process_file(self, file_path: str):
        """ファイルを処理してリネームする"""
        # ファイル書き込み完了を待つ
        time.sleep(self.wait_time)

        path = Path(file_path)
        if not path.exists():
            return

        filename = path.stem  # 拡張子を除いたファイル名
        extension = path.suffix  # 拡張子

        if self.should_rename(filename):
            self.rename_file(path, filename, extension)

    def should_rename(self, filename: str) -> bool:
        """ファイル名が変換対象かどうかを判定"""
        return bool(self.pattern.search(filename))

    def rename_file(self, file_path: Path, filename: str, extension: str):
        """ファイル名を変換する"""
        # パターンに一致する部分を削除
        new_filename = self.pattern.sub('', filename)
        new_file_path = file_path.parent / f"{new_filename}{extension}"

        # 変換後のファイル名が既に存在する場合
        if new_file_path.exists():
            print(f"[スキップ] 変換後のファイルが既に存在します: {new_file_path}")
            return

        try:
            file_path.rename(new_file_path)
            print(f"[成功] リネーム完了:")
            print(f"  変換前: {file_path.name}")
            print(f"  変換後: {new_file_path.name}")
        except PermissionError:
            print(f"[エラー] ファイルにアクセスできません: {file_path}")
        except OSError as e:
            print(f"[エラー] リネーム失敗: {e}")


class TrayApp:
    """タスクトレイアプリケーション"""

    def __init__(self):
        self.src_dir = get_src_dir()
        self.observer = None
        self.icon = None
        self._validate_src_dir()

    def _validate_src_dir(self):
        """監視フォルダの存在確認"""
        if not os.path.exists(self.src_dir):
            print(f"[エラー] 監視フォルダが存在しません: {self.src_dir}")
            sys.exit(1)

    def _create_icon_image(self) -> Image.Image:
        """タスクトレイ用のアイコン画像を作成"""
        # 64x64の画像を作成
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 背景円（青）
        draw.ellipse([4, 4, size - 4, size - 4], fill='#4A90D9')

        # ファイルアイコン風の図形（白）
        # 外枠
        draw.rectangle([20, 12, 44, 52], fill='white')
        # 折り返し部分
        draw.polygon([(32, 12), (44, 24), (32, 24)], fill='#4A90D9')

        # 矢印（リネームを表現）
        draw.line([(24, 38), (40, 38)], fill='#4A90D9', width=3)
        draw.polygon([(36, 33), (42, 38), (36, 43)], fill='#4A90D9')

        return image

    def _open_folder(self):
        """監視フォルダをエクスプローラーで開く"""
        subprocess.Popen(['explorer', self.src_dir])

    def _quit_app(self):
        """アプリケーションを終了"""
        print("[終了] アプリケーションを終了します...")
        self.stop_watching()
        if self.icon:
            self.icon.stop()

    def _create_menu(self) -> pystray.Menu:
        """タスクトレイメニューを作成"""
        return pystray.Menu(
            pystray.MenuItem(
                text=f"監視中: {os.path.basename(self.src_dir)}",
                action=None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                text="監視フォルダを開く",
                action=lambda: self._open_folder()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                text="終了",
                action=lambda: self._quit_app()
            )
        )

    def start_watching(self):
        """ファイル監視を開始"""
        event_handler = FileRenameHandler()
        self.observer = Observer()
        self.observer.schedule(event_handler, self.src_dir, recursive=False)
        self.observer.start()
        print(f"[開始] フォルダ監視を開始しました: {self.src_dir}")

    def stop_watching(self):
        """ファイル監視を停止"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("[停止] フォルダ監視を停止しました")

    def run(self):
        """アプリケーションを実行"""
        # ファイル監視を別スレッドで開始
        watch_thread = threading.Thread(target=self.start_watching, daemon=True)
        watch_thread.start()

        # タスクトレイアイコンを設定
        self.icon = pystray.Icon(
            name="FileRenamer",
            icon=self._create_icon_image(),
            title="ファイル名自動変換",
            menu=self._create_menu()
        )

        print("[起動] タスクトレイに常駐しています")
        print("       終了するにはタスクトレイアイコンを右クリック→「終了」")

        # タスクトレイアイコンを実行（メインスレッドでブロック）
        self.icon.run()


def main():
    """エントリーポイント"""
    print("=" * 50)
    print("ファイル名自動変換アプリケーション")
    print("=" * 50)

    try:
        app = TrayApp()
        app.run()
    except FileNotFoundError as e:
        print(f"[エラー] 設定ファイルエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[エラー] 予期せぬエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
