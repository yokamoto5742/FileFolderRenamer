import configparser
import logging
import re
from unittest.mock import patch

import pytest

from utils.config_manager import compile_patterns, get_watch_targets


def build_config(text: str) -> configparser.ConfigParser:
    """テスト用の設定オブジェクトを生成"""
    config = configparser.ConfigParser()
    config.read_string(text)
    return config


def patch_config(text: str):
    """load_configを差し替えるコンテキストマネージャを返す"""
    return patch("utils.config_manager.load_config", return_value=build_config(text))


class TestCompilePatterns:
    """パターンのコンパイルテスト"""

    def test_appends_end_anchor(self):
        """末尾に$が無いパターンには$が付与される"""
        config = build_config("[Watch1]\nsrc_dir = C:\\a\npattern1 = _tmp\n")
        patterns = compile_patterns(config, "Watch1")
        assert patterns[0].pattern == "_tmp$"

    def test_sorts_by_length_descending(self):
        """長いパターンが先に適用されるようソートされる"""
        config = build_config(
            "[Watch1]\nsrc_dir = C:\\a\n"
            "pattern1 = _[A-Za-z0-9]{6}$\n"
            "pattern2 = _magnate_[A-Za-z0-9]{6}$\n"
        )
        patterns = compile_patterns(config, "Watch1")
        assert patterns[0].pattern == "_magnate_[A-Za-z0-9]{6}$"
        assert patterns[1].pattern == "_[A-Za-z0-9]{6}$"

    def test_ignores_non_pattern_keys(self):
        """pattern以外のキーは無視される"""
        config = build_config("[Watch1]\nsrc_dir = C:\\a\npattern1 = _tmp$\n")
        assert len(compile_patterns(config, "Watch1")) == 1

    def test_raises_on_invalid_regex(self):
        """不正な正規表現は例外を送出"""
        config = build_config("[Watch1]\nsrc_dir = C:\\a\npattern1 = [unclosed$\n")
        with pytest.raises(re.error):
            compile_patterns(config, "Watch1")


class TestGetWatchTargets:
    """監視対象の取得テスト"""

    def test_returns_single_target(self):
        """単一の監視対象を取得"""
        with patch_config("[Watch1]\nsrc_dir = C:\\a\npattern1 = _tmp$\n"):
            targets = get_watch_targets()
            assert len(targets) == 1
            assert targets[0].src_dir == "C:\\a"
            assert targets[0].patterns[0].pattern == "_tmp$"

    def test_returns_multiple_targets_with_own_patterns(self):
        """監視対象ごとに固有のパターンを持つ"""
        with patch_config(
            "[Watch1]\nsrc_dir = C:\\a\npattern1 = _magnate_[A-Za-z0-9]{6}$\n"
            "[Watch2]\nsrc_dir = C:\\b\npattern1 = _sales_[A-Za-z0-9]{4}$\n"
        ):
            targets = get_watch_targets()
            assert [target.src_dir for target in targets] == ["C:\\a", "C:\\b"]
            assert targets[0].patterns[0].pattern == "_magnate_[A-Za-z0-9]{6}$"
            assert targets[1].patterns[0].pattern == "_sales_[A-Za-z0-9]{4}$"

    def test_sorts_sections_numerically(self):
        """セクションは番号順に並ぶ（文字列順ではない）"""
        with patch_config(
            "[Watch10]\nsrc_dir = C:\\ten\npattern1 = _tmp$\n"
            "[Watch2]\nsrc_dir = C:\\two\npattern1 = _tmp$\n"
        ):
            targets = get_watch_targets()
            assert [target.src_dir for target in targets] == ["C:\\two", "C:\\ten"]

    def test_skips_duplicate_src_dir(self, caplog):
        """重複した監視対象ディレクトリはスキップし警告を出す"""
        with patch_config(
            "[Watch1]\nsrc_dir = C:\\a\npattern1 = _tmp$\n"
            "[Watch2]\nsrc_dir = C:\\a\npattern1 = _other$\n"
        ):
            with caplog.at_level(logging.WARNING):
                targets = get_watch_targets()

            assert len(targets) == 1
            assert targets[0].patterns[0].pattern == "_tmp$"
            assert "監視対象ディレクトリが重複しているため" in caplog.text

    def test_detects_duplicate_ignoring_case_and_separator(self, caplog):
        """大文字小文字・末尾区切りの違いも重複として扱う"""
        with patch_config(
            "[Watch1]\nsrc_dir = C:\\Data\npattern1 = _tmp$\n"
            "[Watch2]\nsrc_dir = c:\\data\\\npattern1 = _tmp$\n"
        ):
            with caplog.at_level(logging.WARNING):
                targets = get_watch_targets()
            assert len(targets) == 1

    def test_ignores_non_watch_sections(self):
        """Watch以外のセクションは監視対象にならない"""
        with patch_config("[Watch1]\nsrc_dir = C:\\a\npattern1 = _tmp$\n[App]\nwait_time = 0.5\n"):
            assert len(get_watch_targets()) == 1

    def test_raises_when_no_watch_section(self):
        """Watchセクションが無い場合はValueError"""
        with patch_config("[App]\nwait_time = 0.5\n"):
            with pytest.raises(ValueError, match="監視対象が設定されていません"):
                get_watch_targets()

    def test_allows_target_without_patterns(self):
        """パターン未設定でも監視対象として扱う"""
        with patch_config("[Watch1]\nsrc_dir = C:\\a\n"):
            targets = get_watch_targets()
            assert targets[0].patterns == []
