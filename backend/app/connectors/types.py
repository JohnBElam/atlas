from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnDef:
    name: str
    type: str
    nullable: bool = True
