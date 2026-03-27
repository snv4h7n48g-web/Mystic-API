from __future__ import annotations

from dataclasses import dataclass

from .products.compatibility import contracts as compatibility_contracts
from .products.daily_horoscope import contracts as daily_contracts
from .products.feng_shui import contracts as feng_shui_contracts
from .products.lunar import contracts as lunar_contracts
from .products.palm import contracts as palm_contracts
from .products.tarot import contracts as tarot_contracts


@dataclass(frozen=True)
class ProductContract:
    product_key: str
    prompt_ids: dict[str, str]
    expected_section_ids: list[str]
    contract_instruction: str


CONTRACTS: dict[str, ProductContract] = {
    "daily": ProductContract(
        product_key=daily_contracts.PRODUCT_KEY,
        prompt_ids=daily_contracts.PROMPT_IDS,
        expected_section_ids=daily_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=daily_contracts.CONTRACT_INSTRUCTION,
    ),
    "lunar": ProductContract(
        product_key=lunar_contracts.PRODUCT_KEY,
        prompt_ids=lunar_contracts.PROMPT_IDS,
        expected_section_ids=lunar_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=lunar_contracts.CONTRACT_INSTRUCTION,
    ),
    "tarot": ProductContract(
        product_key=tarot_contracts.PRODUCT_KEY,
        prompt_ids=tarot_contracts.PROMPT_IDS,
        expected_section_ids=tarot_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=tarot_contracts.CONTRACT_INSTRUCTION,
    ),
    "compatibility": ProductContract(
        product_key=compatibility_contracts.PRODUCT_KEY,
        prompt_ids=compatibility_contracts.PROMPT_IDS,
        expected_section_ids=compatibility_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=compatibility_contracts.CONTRACT_INSTRUCTION,
    ),
    "palm": ProductContract(
        product_key=palm_contracts.PRODUCT_KEY,
        prompt_ids=palm_contracts.PROMPT_IDS,
        expected_section_ids=palm_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=palm_contracts.CONTRACT_INSTRUCTION,
    ),
    "feng_shui": ProductContract(
        product_key=feng_shui_contracts.PRODUCT_KEY,
        prompt_ids=feng_shui_contracts.PROMPT_IDS,
        expected_section_ids=feng_shui_contracts.EXPECTED_SECTION_IDS,
        contract_instruction=feng_shui_contracts.CONTRACT_INSTRUCTION,
    ),
}


def get_product_contract(product_key: str) -> ProductContract | None:
    return CONTRACTS.get(product_key)
