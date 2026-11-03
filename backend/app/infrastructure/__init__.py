"""Concrete adapters implementing the application ports.

Adapters are the only place that knows about an external SDK (``openai``,
``redis``, ``requests``) or a transport. They are intentionally thin: convert
inputs/outputs and translate errors, but hold no business rules.
"""
