import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class SupabaseConfig:
    url: str
    key: str


@dataclass
class GeminiConfig:  # Changed from OpenAIConfig
    api_key: str
    model: str


@dataclass
class EmailConfig:
    enabled: bool
    smtp_host: str
    smtp_port: int
    use_tls: bool
    username: str
    password: str
    from_address: str
    to_addresses: list[str]


@dataclass
class TeamsConfig:
    enabled: bool
    webhook_url: str


@dataclass
class OutputConfig:
    base_dir: Path
    generate_docx: bool


@dataclass
class LLMConfig:
    temperature: float
    max_tokens: int


@dataclass
class AppConfig:
    supabase: SupabaseConfig
    gemini: GeminiConfig  # Changed from openai
    email: EmailConfig
    teams: TeamsConfig
    output: OutputConfig
    llm: LLMConfig


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: str | None = None) -> AppConfig:
    if config_path is None:
        config_path = os.environ.get("BOOK_GEN_CONFIG", "config.yaml")

    cfg_file = Path(config_path)
    if not cfg_file.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_file}")

    raw = _load_yaml(cfg_file)

    # Use environment variables for secrets, fallback to config file
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        # Try to get from config, but warn if secrets are hardcoded
        supabase_config = raw.get("supabase", {})
        supabase_url = supabase_url or supabase_config.get("url", "")
        supabase_key = supabase_key or supabase_config.get("key", "")
        
        if supabase_config.get("url") or supabase_config.get("key"):
            print("⚠️  Warning: Supabase credentials found in config file. Consider using environment variables.")
    
    supabase = SupabaseConfig(
        url=supabase_url,
        key=supabase_key,
    )

    # Gemini config with env var fallback
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    gemini_model = os.environ.get("GEMINI_MODEL")
    
    if not gemini_api_key or not gemini_model:
        gemini_config = raw.get("gemini", {})
        gemini_api_key = gemini_api_key or gemini_config.get("api_key", "")
        gemini_model = gemini_model or gemini_config.get("model", "gemini-1.5-flash")
        
        if gemini_config.get("api_key"):
            print("⚠️  Warning: Gemini API key found in config file. Consider using GEMINI_API_KEY environment variable.")
    
    gemini_cfg = GeminiConfig(
        api_key=gemini_api_key,
        model=gemini_model,
    )

    notif_email = raw.get("notifications", {}).get("email", {})
    email_cfg = EmailConfig(
        enabled=bool(notif_email.get("enabled", False)),
        smtp_host=notif_email.get("smtp_host", ""),
        smtp_port=int(notif_email.get("smtp_port", 587)),
        use_tls=bool(notif_email.get("use_tls", True)),
        username=notif_email.get("username", ""),
        password=os.environ.get("SMTP_PASSWORD") or notif_email.get("password", ""),
        from_address=notif_email.get("from_address", ""),
        to_addresses=list(notif_email.get("to_addresses", [])),
    )

    notif_teams = raw.get("notifications", {}).get("teams", {})
    teams_cfg = TeamsConfig(
        enabled=bool(notif_teams.get("enabled", False)),
        webhook_url=notif_teams.get("webhook_url", ""),
    )

    out_raw = raw.get("output", {})
    output_cfg = OutputConfig(
        base_dir=Path(out_raw.get("base_dir", "outputs")),
        generate_docx=bool(out_raw.get("generate_docx", False)),
    )

    llm_raw = raw.get("llm", {})
    llm_cfg = LLMConfig(
        temperature=float(llm_raw.get("temperature", 0.7)),
        max_tokens=int(llm_raw.get("max_tokens", 2000)),
    )

    # Ensure output directory exists
    output_cfg.base_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        supabase=supabase,
        gemini=gemini_cfg,
        email=email_cfg,
        teams=teams_cfg,
        output=output_cfg,
        llm=llm_cfg,
    )