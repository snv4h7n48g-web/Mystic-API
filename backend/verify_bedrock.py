#!/usr/bin/env python3
"""Verify AWS Bedrock model access and Mystic structured-output configuration."""

from __future__ import annotations

import json
import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from bedrock_service import BedrockService
from deployment_env import aws_client_kwargs, effective_persona_profile_models


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def check_credentials() -> bool:
    """Check whether AWS credentials are configured without printing secret material."""
    print_header("1. Checking AWS Credentials")

    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")

    if access_key and access_key != "your_access_key_here":
        if not secret_key or secret_key == "your_secret_key_here":
            print("FAIL AWS_ACCESS_KEY_ID is set but AWS_SECRET_ACCESS_KEY is missing")
            return False
        print("OK using explicit AWS credentials from .env (values hidden)")
        print(f"OK AWS_REGION: {region}")
        return True

    print("INFO no explicit credentials in .env; using AWS default credential chain")
    print(f"OK AWS_REGION: {region}")

    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        print(f"OK AWS Account: {identity['Account']}")
        print(f"OK AWS Principal: {identity['Arn'].split('/')[-1]}")
        return True
    except Exception as exc:
        print(f"FAIL could not verify AWS credentials: {exc}")
        print("\nPlease ensure AWS CLI/default credentials are configured, or add local-only credentials to .env.")
        return False


def check_bedrock_service() -> tuple[bool, dict | None]:
    """Check whether the Bedrock control-plane API is accessible."""
    print_header("2. Testing Bedrock Service Access")

    try:
        client = boto3.client(**aws_client_kwargs("bedrock"))
        response = client.list_foundation_models()
        print("OK Bedrock service accessible")
        print(f"OK found {len(response.get('modelSummaries', []))} foundation models")
        return True, response
    except Exception as exc:
        print(f"FAIL error accessing Bedrock: {exc}")
        return False, None


def check_model_access(response: dict | None) -> bool:
    """Check whether configured model IDs are listed or valid inference profile IDs."""
    print_header("3. Checking Model Availability")

    if not response:
        return False

    models = response.get("modelSummaries", [])
    model_by_id = {model.get("modelId", ""): model for model in models}

    found_any = False
    targets = [
        ("Legacy preview", "BEDROCK_PREVIEW_MODEL", "us.amazon.nova-lite-v1:0"),
        ("Legacy full", "BEDROCK_FULL_MODEL", "us.amazon.nova-pro-v1:0"),
        ("Claude Opus", "BEDROCK_MODEL_CLAUDE_OPUS", "global.anthropic.claude-opus-4-5-20251101-v1:0"),
    ]
    for profile_id, model_id in effective_persona_profile_models().items():
        targets.append((f"Persona profile {profile_id}", "", model_id))

    for label, env_name, fallback in targets:
        target = os.getenv(env_name, fallback).strip()
        if not target:
            print(f"- {label}: not configured")
            continue
        model = model_by_id.get(target)
        if model:
            found_any = True
            print(f"OK {label} found: {target}")
            print(f"  Status: {model.get('modelLifecycle', {}).get('status', 'unknown')}")
        elif target.startswith(("us.", "global.")):
            found_any = True
            print(f"- {label} configured as inference profile: {target}")
            print("  Availability will be checked by inference tests")
        else:
            print(f"FAIL {label} not found: {target}")

    if not found_any:
        print("\nWARN none of the configured target models were found in available models")
        print("Check Bedrock model access, exact model IDs, and AWS region alignment.")
        return False

    return True


def configured_test_model() -> str:
    return (
        os.getenv("MYSTIC_LLM_PROFILE_PREVIEW_MODEL")
        or os.getenv("BEDROCK_MODEL_CLAUDE_OPUS")
        or os.getenv("BEDROCK_PREVIEW_MODEL", "us.amazon.nova-lite-v1:0")
    ).strip()


def test_inference() -> bool:
    """Test a simple model inference call."""
    print_header("4. Testing Model Inference")

    test_model = configured_test_model()
    persona_enabled = os.getenv("MYSTIC_USE_PERSONA_ORCHESTRATION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    try:
        client = boto3.client(**aws_client_kwargs("bedrock-runtime"))
        print(f"Testing inference with: {test_model}")
        print(f"Persona orchestration enabled: {persona_enabled}")

        response = client.converse(
            modelId=test_model,
            messages=[{"role": "user", "content": [{"text": "Say hello in one word."}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.7},
        )

        output = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        print("OK inference successful")
        print(f"  Response: {output}")
        print(f"  Input tokens: {usage.get('inputTokens', 0)}")
        print(f"  Output tokens: {usage.get('outputTokens', 0)}")
        return True
    except Exception as exc:
        print(f"FAIL inference failed: {exc}")
        return False


def test_structured_inference() -> bool:
    """Test the same structured-output path Mystic uses for generation."""
    print_header("5. Testing Structured Output")

    schema = {
        "type": "object",
        "properties": {
            "opening_hook": {"type": "string"},
            "current_pattern": {"type": "string"},
            "emotional_truth": {"type": "string"},
            "continuity_callback": {"type": "string"},
            "next_return_invitation": {"type": "string"},
            "premium_teaser": {"type": "string"},
            "theme_tags": {"type": "array", "items": {"type": "string"}},
            "practical_guidance": {"type": "string"},
        },
        "required": [
            "opening_hook",
            "current_pattern",
            "emotional_truth",
            "continuity_callback",
            "next_return_invitation",
            "premium_teaser",
            "theme_tags",
            "practical_guidance",
        ],
        "additionalProperties": False,
    }

    try:
        service = BedrockService()
        result = service.invoke_text(
            model_id=configured_test_model(),
            system_prompt="Return only the requested Mystic JSON fields.",
            user_messages=["Create a tiny test reading about steady focus."],
            temperature=0.3,
            top_p=0.9,
            max_tokens=220,
            timeout_ms=120_000,
            structured_schema=schema,
        )
        parsed = json.loads(result["text"])
        missing = [key for key in schema["required"] if key not in parsed]
        if missing:
            print(f"FAIL structured output missing keys: {missing}")
            return False
        print("OK structured output successful")
        print(f"  Model: {result['model']}")
        print(f"  Input tokens: {result['input_tokens']}")
        print(f"  Output tokens: {result['output_tokens']}")
        return True
    except Exception as exc:
        print(f"FAIL structured output failed: {exc}")
        return False


def main() -> int:
    print("\n" + "=" * 60)
    print("  AWS BEDROCK MODEL ACCESS VERIFICATION")
    print("=" * 60)

    if not check_credentials():
        print("\nFAIL please configure AWS credentials")
        return 1

    success, response = check_bedrock_service()
    if not success:
        print("\nFAIL cannot access Bedrock service")
        return 1

    if not check_model_access(response):
        print("\nFAIL configured models may not be accessible")
        return 1

    if not test_inference():
        print("\nFAIL model inference test failed")
        return 1

    if not test_structured_inference():
        print("\nFAIL structured-output test failed")
        return 1

    print_header("ALL CHECKS PASSED")
    print("Your AWS Bedrock configuration is ready.")
    print("\nYou can start the API server from backend/:")
    print("  python -m uvicorn main:app --host 127.0.0.1 --port 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
