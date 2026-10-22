"""Deprecated v0.1 compatibility entry point; use delta_receipt.py."""
import sys

if __package__:
    from . import delta_receipt as _impl
    from .delta_receipt import *  # noqa: F401,F403 - preserve the legacy import surface
else:
    import delta_receipt as _impl
    from delta_receipt import *  # noqa: F401,F403 - preserve direct script execution

main = _impl.main

if __name__ == "__main__":
    sys.exit(main())
