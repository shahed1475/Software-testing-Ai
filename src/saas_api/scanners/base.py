from __future__ import annotations

from typing import Any, Dict


class ScanAdapter:
    name = "base"

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
