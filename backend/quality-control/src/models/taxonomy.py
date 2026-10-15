"""The tenant defect taxonomy: the only source of recordable defect codes.

``qc_defects.defect_code`` is untyped ``text`` and the BRD names only three
examples (``broken stitch``, ``puckering``, ``uneven seam``), so this module
carries no code list of its own. The taxonomy arrives as configuration and an
unknown code is refused rather than stored, because a defect recorded against an
invented code cannot be counted or reviewed later.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class DefectTaxonomy:
    """The set of defect codes a tenant's QC inspectors may select."""

    codes: frozenset[str]

    def __post_init__(self) -> None:
        if not self.codes:
            raise ValueError("A defect taxonomy must contain at least one code")
        blank = sorted(code for code in self.codes if not code or code != code.strip())
        if blank:
            raise ValueError(f"Defect codes must be non-blank and untrimmed: {blank}")

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> Self:
        """Build a taxonomy from the tenant's configured defect codes."""
        return cls(codes=frozenset(codes))

    def contains(self, code: str) -> bool:
        return code in self.codes

    def known_codes(self) -> tuple[str, ...]:
        """The configured codes in a stable order, for error messages and pickers."""
        return tuple(sorted(self.codes))
