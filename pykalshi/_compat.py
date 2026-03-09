"""Backward-compatibility layer for the fixed-point migration.

Provides:
- CompatModel: Pydantic BaseModel subclass that exposes legacy integer field accessors
- Conversion functions between old integer formats and new string formats
- convert_legacy_kwargs: Helper for accepting deprecated integer params in POST methods
"""

from __future__ import annotations

import warnings
from decimal import Decimal
from typing import Any, Callable, ClassVar

from pydantic import BaseModel


# --- Conversion functions ---

def dollars_to_cents(val: str | None) -> int | None:
    """Dollar string → cents int. '0.45' → 45. Truncates via int()."""
    if val is None:
        return None
    return int(Decimal(val) * 100)


def fp_to_int(val: str | None) -> int | None:
    """Fixed-point string → int. '100.50' → 100. Truncates via int()."""
    if val is None:
        return None
    return int(Decimal(val))


def cents_to_dollars(val: int) -> str:
    """Cents int → dollar string. 45 → '0.45'."""
    return str((Decimal(val) / 100).quantize(Decimal("0.01")))


def int_to_fp(val: int) -> str:
    """Int → fixed-point string. 5 → '5.00'."""
    return str(Decimal(int(val)).quantize(Decimal("0.01")))


def orderbook_to_legacy(levels: list[tuple[str, str]] | None) -> list[tuple[int, int]] | None:
    """Convert orderbook levels from (dollar_str, fp_str) to (cents_int, qty_int)."""
    if levels is None:
        return None
    return [(int(Decimal(p) * 100), int(Decimal(q))) for p, q in levels]


# --- CompatModel base class ---

class CompatModel(BaseModel):
    """BaseModel subclass that provides deprecated legacy field accessors.

    Subclasses declare a _legacy_fields class variable mapping old field names
    to (new_field_name, converter_function) tuples. Accessing an old name
    emits a DeprecationWarning and returns the converted value.
    """

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {}

    def __getattr__(self, name: str) -> Any:
        legacy_map = type(self)._legacy_fields
        if name in legacy_map:
            new_name, converter = legacy_map[name]
            warnings.warn(
                f"'{name}' is deprecated, use '{new_name}' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return converter(getattr(self, new_name))
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# --- POST/PUT legacy param conversion ---

def convert_legacy_kwargs(
    kwargs: dict[str, Any],
    mappings: dict[str, tuple[str, Callable]],
) -> dict[str, Any]:
    """Convert deprecated integer kwargs to new string kwargs in-place.

    Args:
        kwargs: The keyword arguments dict to modify.
        mappings: {old_param_name: (new_param_name, converter_fn)}

    New param takes precedence if both old and new are provided.
    Emits DeprecationWarning for each conversion.

    Returns:
        The modified kwargs dict.
    """
    for old_name, (new_name, converter) in mappings.items():
        if old_name in kwargs:
            old_val = kwargs.pop(old_name)
            if old_val is not None and kwargs.get(new_name) is None:
                warnings.warn(
                    f"Parameter '{old_name}' is deprecated, use '{new_name}' instead.",
                    DeprecationWarning,
                    stacklevel=3,
                )
                kwargs[new_name] = converter(old_val)
    return kwargs


# --- Standard legacy param mappings for POST methods ---

PLACE_ORDER_LEGACY = {
    "yes_price": ("yes_price_dollars", cents_to_dollars),
    "no_price": ("no_price_dollars", cents_to_dollars),
    "count": ("count_fp", int_to_fp),
    "buy_max_cost": ("buy_max_cost_dollars", cents_to_dollars),
}

AMEND_ORDER_LEGACY = {
    "yes_price": ("yes_price_dollars", cents_to_dollars),
    "no_price": ("no_price_dollars", cents_to_dollars),
    "count": ("count_fp", int_to_fp),
}

DECREASE_ORDER_LEGACY = {
    "reduce_by": ("reduce_by_fp", int_to_fp),
}

BATCH_ORDER_LEGACY = {
    "yes_price": ("yes_price_dollars", cents_to_dollars),
    "no_price": ("no_price_dollars", cents_to_dollars),
    "count": ("count_fp", int_to_fp),
}

ORDER_GROUP_LEGACY = {
    "contracts_limit": ("contracts_limit_fp", int_to_fp),
}

TRANSFER_LEGACY = {
    "amount": ("amount_dollars", cents_to_dollars),
}

RFQ_LEGACY = {
    "contracts": ("contracts_fp", int_to_fp),
    "target_cost": ("target_cost_dollars", cents_to_dollars),
}
