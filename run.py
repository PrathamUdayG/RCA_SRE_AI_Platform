"""
Purpose
-------
Root CLI entrypoint delegating to presentation.cli.cli_app presentation module.

Responsibilities
----------------
- Launch CLI investigation execution.

Does NOT
---------
- Implement business logic or direct SSH/database calls.
"""

from presentation.cli.cli_app import main

if __name__ == "__main__":
    main()