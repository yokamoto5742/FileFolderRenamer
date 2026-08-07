import configparser
import logging
import os
import re
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 監視対象セクション名（[Watch1], [Watch2], ...）
WATCH_SECTION_PATTERN = re.compile(r"^Watch(\d+)$")


@dataclass
class WatchTarget:
    """監視対象ディレクトリと、そのディレクトリ専用のリネームパターン"""

    src_dir: str
    patterns: list[re.Pattern]


def get_config_path() -> str:
    if getattr(sys, "frozen", False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, "config.ini")


CONFIG_PATH = get_config_path()


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config.read_file(f)
    except FileNotFoundError:
        print(f"設定ファイルが見つかりません: {CONFIG_PATH}")
        raise
    except configparser.Error as e:
        print(f"設定ファイルの解析中にエラーが発生しました: {e}")
        raise
    return config


def save_config(config: configparser.ConfigParser):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise


def compile_patterns(config: configparser.ConfigParser, section: str) -> list[re.Pattern]:
    """指定セクションの pattern1, pattern2... を正規表現にコンパイルして取得"""
    pattern_items = []

    for key in config[section]:
        if key.startswith("pattern"):
            pattern_str = config.get(section, key)

            # パターンが$で終わっていない場合は末尾マッチとして$を追加
            if not pattern_str.endswith("$"):
                pattern_str = pattern_str + "$"

            try:
                pattern_items.append((pattern_str, re.compile(pattern_str)))
            except re.error as e:
                print(f"正規表現パターンが無効です: [{section}] {pattern_str}")
                print(f"エラー: {e}")
                raise

    # より具体的なパターン（長いパターン）を先に適用するため、パターン文字列長の降順でソート
    pattern_items.sort(key=lambda x: len(x[0]), reverse=True)

    return [pattern for _, pattern in pattern_items]


def get_watch_targets() -> list[WatchTarget]:
    """[Watch1], [Watch2]... の監視対象をセクション番号順に取得"""
    config = load_config()

    numbered_sections = []
    for section in config.sections():
        match = WATCH_SECTION_PATTERN.match(section)
        if match:
            numbered_sections.append((int(match.group(1)), section))
    numbered_sections.sort()

    if not numbered_sections:
        raise ValueError(f"[Watch1] 形式の監視対象が設定されていません: {CONFIG_PATH}")

    targets = []
    seen_dirs = set()
    for _, section in numbered_sections:
        src_dir = config.get(section, "src_dir")

        # 同一ディレクトリを複数登録するとハンドラが二重に発火するためスキップ
        normalized = os.path.normcase(os.path.abspath(src_dir))
        if normalized in seen_dirs:
            logger.warning(
                f"監視対象ディレクトリが重複しているためスキップします: [{section}] {src_dir}"
            )
            continue
        seen_dirs.add(normalized)

        targets.append(WatchTarget(src_dir=src_dir, patterns=compile_patterns(config, section)))

    return targets


def get_wait_time() -> float:
    """ファイル書き込み完了を待つ時間を取得（秒）"""
    config = load_config()
    return config.getfloat("App", "wait_time", fallback=0.5)


def get_config_value(config: configparser.ConfigParser, section: str, key: str, default=None):
    """設定値を取得する汎用ヘルパー関数"""
    if not config.has_option(section, key):
        return default

    # デフォルト値の型に応じて適切な変換を行う
    if isinstance(default, bool):
        return config.getboolean(section, key)
    elif isinstance(default, int):
        return config.getint(section, key)
    elif isinstance(default, float):
        return config.getfloat(section, key)
    else:
        return config.get(section, key)
