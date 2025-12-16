import configparser
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


def get_config_path():
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'config.ini')


CONFIG_PATH = get_config_path()


def load_environment_variables():
    current_dir = Path(__file__).parent.parent
    env_path = current_dir / '.env'

    if env_path.exists():
        load_dotenv(env_path)
        return True
    return False


load_environment_variables()


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
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
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise


def get_ai_provider_config() -> Dict[str, str]:
    config = load_config()

    provider = config.get('AI', 'provider', fallback='gemini')
    fallback_provider = config.get('AI', 'fallback_provider', fallback='openai')

    return {
        'provider': provider,
        'fallback_provider': fallback_provider
    }


def get_available_providers() -> Dict[str, bool]:
    providers = {
        'claude': bool(os.environ.get("CLAUDE_API_KEY")),
        'openai': bool(os.environ.get("OPENAI_API_KEY")),
        'gemini': bool(os.environ.get("GEMINI_API_KEY"))
    }
    return providers


def get_provider_credentials(provider: str) -> Optional[Dict[str, str]]:
    credentials_map = {
        'claude': {
            'api_key': os.environ.get("CLAUDE_API_KEY"),
            'model': os.environ.get("CLAUDE_MODEL")
        },
        'openai': {
            'api_key': os.environ.get("OPENAI_API_KEY"),
            'model': os.environ.get("OPENAI_MODEL")
        },
        'gemini': {
            'api_key': os.environ.get("GEMINI_API_KEY"),
            'model': os.environ.get("GEMINI_MODEL"),
            'thinking_budget': os.environ.get("GEMINI_THINKING_BUDGET")
        }
    }

    return credentials_map.get(provider)


def validate_provider_config(provider: str) -> bool:
    credentials = get_provider_credentials(provider)
    if not credentials or not credentials.get('api_key'):
        return False
    return True


def get_active_provider() -> str:
    config = get_ai_provider_config()
    available_providers = get_available_providers()

    main_provider = config['provider']
    if available_providers.get(main_provider, False):
        return main_provider

    fallback_provider = config['fallback_provider']
    if available_providers.get(fallback_provider, False):
        print(f"警告: '{main_provider}' が利用できないため、'{fallback_provider}' を使用します")
        return fallback_provider

    for provider, available in available_providers.items():
        if available:
            print(f"警告: 設定されたプロバイダーが利用できないため、'{provider}' を使用します")
            return provider

    raise Exception("利用可能なAIプロバイダーがありません。APIキーの設定を確認してください。")


CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
GEMINI_THINKING_BUDGET = os.environ.get("GEMINI_THINKING_BUDGET")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
