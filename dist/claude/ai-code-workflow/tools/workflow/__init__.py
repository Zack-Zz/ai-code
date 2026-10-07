"""ai-code-workflow management tools.

Standard-library-only package implementing the fixed data contracts:
controlled JSON IO, product/policy loading, task & evidence state, package
build/check and owned-file staging. No background services, no model calls,
no Git mutations.
"""

__all__ = ["io", "product", "policy", "state", "build", "package_check", "owned_files", "cli"]
