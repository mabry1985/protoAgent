"""Minimal Tool base class — legacy shim for non-LangChain tools.

Kept for backwards compatibility with any tool classes forked in from
earlier agent builds. New tools should use `@tool` from
`langchain_core.tools` — see `tools/lg_tools.py`.
"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Base class for legacy non-LangChain tools. Subclasses implement name, description, parameters, and execute."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def parameters(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str: ...
