"""Keep backend tests hermetic: disable startup conversation warmup by default."""

from __future__ import annotations

import os

os.environ.setdefault("CHAT_APP_WARMUP_ON_START", "0")
