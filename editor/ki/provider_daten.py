# -*- coding: utf-8 -*-
"""
provider_daten.py
─────────────────
Anbieter-URLs und Modell-Listen als Modul-Konstanten.
`lade_anbieter_url(source)` liefert (base_url, key_id) für einen Anbieter-Namen.
"""

# Anbieter-Name → (OpenAI-kompatibler Base-URL, key_id für lade_api_key)
_OAI_URLS = {
    "OpenAI":      ("https://api.openai.com/v1",                               "openai"),
    "GitHub":      ("https://models.inference.ai.azure.com",                   "github"),
    "DeepSeek":    ("https://api.deepseek.com/v1",                             "deepseek"),
    "Gemini":      ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini"),
    "Groq":        ("https://api.groq.com/openai/v1",                          "groq"),
    "Mistral":     ("https://api.mistral.ai/v1",                               "mistral"),
    "Together":    ("https://api.together.xyz/v1",                             "together"),
    "HuggingFace": ("https://api-inference.huggingface.co/v1",                 "huggingface"),
    "xAI":         ("https://api.x.ai/v1",                                     "xai"),
    "Fireworks":   ("https://api.fireworks.ai/inference/v1",                   "fireworks"),
    "Moonshot":    ("https://api.moonshot.cn/v1",                              "moonshot"),
    "Qwen":        ("https://dashscope.aliyuncs.com/compatible-mode/v1",       "qwen"),
    "Cohere":      ("https://api.cohere.com/compatibility/v1",                 "cohere"),
    "SambaNova":   ("https://api.sambanova.ai/v1",                             "sambanova"),
    "MiniMax":     ("https://api.minimax.chat/v1",                             "minimax"),
    "Llama":       ("https://api.llama.com/compat/v1",                         "llama"),
}

# Anbieter-Präfix → (Anzeigename, [Modell-IDs])
_MODELLE = {
    "Anthropic":  ("Anthropic",        ["claude-opus-4-6",
                                        "claude-sonnet-4-6",
                                        "claude-haiku-4-5-20251001"]),
    "OpenAI":     ("OpenAI",           ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]),
    "GitHub":     ("GitHub Copilot",   ["gpt-4o", "gpt-4o-mini", "o1-mini"]),
    "DeepSeek":   ("DeepSeek",         ["deepseek-coder", "deepseek-chat",
                                        "deepseek-reasoner"]),
    "Gemini":     ("Gemini",           ["gemini-2.0-flash", "gemini-1.5-pro",
                                        "gemini-1.5-flash"]),
    "Groq":       ("Groq",             ["llama-3.3-70b-versatile",
                                        "llama-3.1-8b-instant",
                                        "mixtral-8x7b-32768", "gemma2-9b-it"]),
    "Mistral":    ("Mistral",          ["mistral-large-latest",
                                        "mistral-small-latest",
                                        "codestral-latest"]),
    "Together":   ("Together AI",      ["meta-llama/Llama-3.3-70B-Instruct-Turbo",
                                        "mistralai/Mixtral-8x7B-Instruct-v0.1",
                                        "codellama/CodeLlama-34b-Instruct-hf"]),
    "HuggingFace":("HuggingFace",      ["meta-llama/Llama-3.2-3B-Instruct",
                                        "Qwen/Qwen2.5-Coder-32B-Instruct",
                                        "mistralai/Mistral-7B-Instruct-v0.3"]),
    "xAI":        ("xAI",              ["grok-3", "grok-3-mini", "grok-2"]),
    "Fireworks":  ("Fireworks AI",     ["accounts/fireworks/models/llama-v3p3-70b-instruct",
                                        "accounts/fireworks/models/deepseek-coder-v2-instruct",
                                        "accounts/fireworks/models/qwen2p5-coder-32b-instruct"]),
    "Moonshot":   ("Moonshot",         ["moonshot-v1-8k", "moonshot-v1-32k",
                                        "moonshot-v1-128k"]),
    "Qwen":       ("Qwen (Alibaba)",   ["qwen-coder-plus", "qwen-plus", "qwen-max",
                                        "qwen2.5-coder-32b-instruct"]),
    "Cohere":     ("Cohere",           ["command-a-03-2025", "command-r-plus",
                                        "command-r"]),
    "SambaNova":  ("SambaNova",        ["DeepSeek-R1", "Meta-Llama-3.3-70B-Instruct",
                                        "Qwen2.5-Coder-32B-Instruct"]),
    "MiniMax":    ("MiniMax",          ["MiniMax-Text-01", "abab6.5s-chat"]),
    "Llama":      ("Llama API",        ["Llama-4-Scout-17B-16E-Instruct-FP8",
                                        "Llama-4-Maverick-17B-128E-Instruct-FP8",
                                        "Llama-3.3-70B-Instruct"]),
}


# Ollama-Modelle die Tool-Calling unterstützen (Substring-Match, lowercase)
OLLAMA_TOOL_MODELLE = {
    "llama3.1", "llama3.2", "llama3.3",
    "qwen2.5", "qwen2.5-coder",
    "mistral-nemo", "mistral-small",
    "command-r",
    "phi4",
    "deepseek-r1",
    "granite3",
}


def ollama_unterstuetzt_tools(modell: str) -> bool:
    """True wenn das Ollama-Modell Tool-Calling unterstützt."""
    m = modell.lower()
    return any(name in m for name in OLLAMA_TOOL_MODELLE)


def lade_anbieter_url(source: str):
    """Gibt (base_url, key_id) für den Anbieter-Namen zurück.

    Fallback: OpenRouter wenn kein Präfix passt.
    """
    return next(
        ((url, kid) for pfx, (url, kid) in _OAI_URLS.items()
         if source.startswith(pfx)),
        ("https://openrouter.ai/api/v1", "openrouter")
    )
