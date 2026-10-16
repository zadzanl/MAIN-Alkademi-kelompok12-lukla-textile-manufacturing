"""
Lukla Operations Engine & Intelligence — Root Application Entry Point.
Compatible with EC2 launch command:
    uvicorn main:app --host 0.0.0.0 --port 3000
"""
import sys
from pathlib import Path

# Ensure root directory is in python search path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Python < 3.11 compatibility polyfills (e.g. Amazon Linux 2023 Python 3.9)
import enum
if not hasattr(enum, "StrEnum"):
    class StrEnum(str, enum.Enum):
        pass
    enum.StrEnum = StrEnum

import typing
if not hasattr(typing, "Self"):
    try:
        from typing_extensions import Self
        typing.Self = Self
    except ImportError:
        pass

from backend.app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=False)
