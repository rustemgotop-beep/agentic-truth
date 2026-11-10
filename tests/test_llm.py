"""Проверки параметров инициализации GigaChat."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.llm import get_gigachat_llm


class TestGigaChatInitialization(unittest.TestCase):
    def test_scope_is_explicit_even_if_env_scope_is_empty(self):
        test_config = SimpleNamespace(
            gigachat_credentials="test-credentials",
            gigachat_scope="",
            gigachat_model="GigaChat",
            gigachat_base_url="https://example.invalid/api/v1",
            verify_ssl_certs=False,
        )
        with (
            patch("core.llm.config", test_config),
            patch("langchain_gigachat.chat_models.GigaChat") as client,
        ):
            result = get_gigachat_llm()

        self.assertIs(result, client.return_value)
        self.assertEqual(client.call_args.kwargs["scope"], "GIGACHAT_API_PERS")
