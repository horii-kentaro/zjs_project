"""
Integration tests package.

All tests in this package connect to real external services:
- JVN iPedia API (no mocks)
- PostgreSQL database (real Neon database)

Test isolation is achieved through unique test data and transaction rollback.
"""
