"""ファイル名自動変換アプリケーション

指定ディレクトリを監視し、ファイル名から不要なパターンを自動削除する
Windowsタスクトレイに常駐して動作する
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
import pystray
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirMovedEvent,
)
from watchdog.observers import Observer

if TYPE_CHECKING:
    from pystray import MenuItem

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import load_config


class FileRenameHandler(FileSystemEventHandler):
    """ファイル作成イベントを監視し、ファイル名を変換するハンドラ"""

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)
        self.processed_files: set[str] = set()

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if event.is_directory:
            return
        self._process_file(str(event.src_path))

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.is_directory:
            return
        self._process_file(str(event.dest_path))

    def _process_file(self, file_path: str):
        # 短い遅延を入れてファイルの書き込み完了を待つ
        time.sleep(0.5)

        if file_path in self.processed_files:
            return

        path = Path(file_path)
        if not path.exists():
            return

        original_name = path.stem
        extension = path.suffix
        new_name = self.pattern.sub('', original_name)

        if new_name != original_name:
            new_path = path.parent / f"{new_name}{extension}"

            # 同名ファイルが存在する場合はスキップ
            if new_path.exists():
                print(f"スキップ: {new_path} は既に存在します")
                return

            try:
                path.rename(new_path)
                self.processed_files.add(str(new_path))
                print(f"リネーム: {path.name} → {new_path.name}")
            except OSError as e:
                print(f"エラー: {path.name} のリネームに失敗しました - {e}")


class FileRenamerApp:
    """タスクトレイ常駐アプリケーション"""

    def __init__(self):
        self.config = load_config()
        self.src_dir = self.config.get('Paths', 'src_dir')
        self.pattern = self.config.get('Rename', 'pattern')
        self._observer: Observer | None = None
        self._icon: pystray.Icon | None = None
        self.running = False

    def create_icon_image(self) -> Image.Image:
        """タスクトレイアイコン用の画像を生成"""
        # 32x32のシンプルなアイコンを生成
        img = Image.new('RGB', (32, 32), color=(70, 130, 180))
        return img

    def start_watching(self) -> bool:
        """ファイル監視を開始"""
        if not os.path.exists(self.src_dir):
            print(f"エラー: 監視ディレクトリが存在しません - {self.src_dir}")
            return False

        handler = FileRenameHandler(self.pattern)
        observer = Observer()
        observer.schedule(handler, self.src_dir, recursive=False)
        observer.start()
        self._observer = observer
        self.running = True
        print(f"監視開始: {self.src_dir}")
        print(f"パターン: {self.pattern}")
        return True

    def stop_watching(self) -> None:
        """ファイル監視を停止"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self.running = False
        print("監視停止")

    def on_quit(self, icon: pystray.Icon, item: "MenuItem") -> None:
        """終了メニュー選択時の処理"""
        self.stop_watching()
        icon.stop()

    def on_toggle(self, icon: pystray.Icon, item: "MenuItem") -> None:
        """監視の開始/停止を切り替え"""
        if self.running:
            self.stop_watching()
        else:
            self.start_watching()
        # メニューを更新
        icon.update_menu()

    def get_status_text(self, item: "MenuItem") -> str:
        """現在の監視状態を返す"""
        return "監視中..." if self.running else "停止中"

    def create_menu(self) -> pystray.Menu:
        """タスクトレイメニューを作成"""
        return pystray.Menu(
            pystray.MenuItem(
                self.get_status_text,
                None,
                enabled=False
            ),
            pystray.MenuItem(
                lambda item: "停止" if self.running else "開始",
                self.on_toggle
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self.on_quit)
        )

    def run(self) -> None:
        """アプリケーションを起動"""
        # 監視を開始
        if not self.start_watching():
            return

        # タスクトレイアイコンを作成
        icon = pystray.Icon(
            "FileRenamer",
            self.create_icon_image(),
            "FileRenamer - ファイル名自動変換",
            self.create_menu()
        )
        self._icon = icon

        # タスクトレイで実行
        icon.run()


def main() -> None:
    """エントリーポイント"""
    app = FileRenamerApp()
    app.run()


if __name__ == "__main__":
    main()
