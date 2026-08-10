from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path[:0] = [
    str(ROOT),
    str(ROOT / ".pythonlibs_ai"),
    str(ROOT / ".pythonlibs"),
]

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
