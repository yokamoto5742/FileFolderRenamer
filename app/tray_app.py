import logging
import os
import subprocess
import sys
import threading

import pystray
from PIL import Image, ImageDraw
from watchdog.observers import Observer

from service.file_rename_handler import FileRenameHandler
from utils.config_manager import get_wait_time, get_watch_targets

logger = logging.getLogger(__name__)


class TrayApp:
    """タスクトレイアプリケーション"""

    def __init__(self):
        self.targets = get_watch_targets()
        self.wait_time = get_wait_time()
        self.observer = None
        self.icon = None
        self._validate_src_dirs()

    def _validate_src_dirs(self):
        """全監視フォルダの存在確認"""
        missing = [target.src_dir for target in self.targets if not os.path.exists(target.src_dir)]
        if missing:
            for src_dir in missing:
                logger.error(f"監視フォルダが存在しません: {src_dir}")
            sys.exit(1)

    def _create_icon_image(self) -> Image.Image:
        """タスクトレイ用のアイコン画像を作成"""
        # 64x64の画像を作成
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 背景円（青）
        draw.ellipse([4, 4, size - 4, size - 4], fill="#4A90D9")

        # ファイルアイコン風の図形（白）
        # 外枠
        draw.rectangle([20, 12, 44, 52], fill="white")
        # 折り返し部分
        draw.polygon([(32, 12), (44, 24), (32, 24)], fill="#4A90D9")

        # 矢印（リネームを表現）
        draw.line([(24, 38), (40, 38)], fill="#4A90D9", width=3)
        draw.polygon([(36, 33), (42, 38), (36, 43)], fill="#4A90D9")

        return image

    def _open_folder(self, src_dir: str):
        """監視フォルダをエクスプローラーで開く"""
        subprocess.Popen(["explorer", src_dir])

    def _quit_app(self):
        """アプリケーションを終了"""
        logger.info("アプリケーションを終了します")
        self.stop_watching()
        if self.icon:
            self.icon.stop()

    def _create_folder_submenu(self) -> pystray.Menu:
        """監視フォルダごとの「開く」サブメニューを作成"""
        return pystray.Menu(
            *[
                pystray.MenuItem(
                    text=os.path.basename(target.src_dir),
                    # ループ変数を束縛するためデフォルト引数を使用
                    action=lambda _item, src_dir=target.src_dir: self._open_folder(src_dir),
                )
                for target in self.targets
            ]
        )

    def _create_menu(self) -> pystray.Menu:
        """タスクトレイメニューを作成"""
        return pystray.Menu(
            pystray.MenuItem(text=f"監視中: {len(self.targets)}件", action=None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(text="監視フォルダを開く", action=self._create_folder_submenu()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(text="終了", action=lambda: self._quit_app()),
        )

    def start_watching(self):
        """ファイル監視を開始"""
        self.observer = Observer()
        handlers = []
        for target in self.targets:
            event_handler = FileRenameHandler(target.patterns, self.wait_time)
            self.observer.schedule(event_handler, target.src_dir, recursive=False)
            handlers.append((event_handler, target.src_dir))
            logger.info(f"フォルダ監視を開始しました: {target.src_dir}")
        self.observer.start()

        # 監視開始後に既存ファイルを処理し、スキャン中に届いたファイルの取りこぼしを防ぐ
        for event_handler, src_dir in handlers:
            event_handler.process_existing_files(src_dir)

    def stop_watching(self):
        """ファイル監視を停止"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("フォルダ監視を停止しました")

    def run(self):
        """アプリケーションを実行"""
        # ファイル監視を別スレッドで開始
        watch_thread = threading.Thread(target=self.start_watching, daemon=True)
        watch_thread.start()

        # タスクトレイアイコンを設定
        self.icon = pystray.Icon(
            name="FileFolderRenamer",
            icon=self._create_icon_image(),
            title="FileFolderRenamer",
            menu=self._create_menu(),
        )

        logger.info("タスクトレイに常駐しています")

        # タスクトレイアイコンを実行（メインスレッドでブロック）
        self.icon.run()
