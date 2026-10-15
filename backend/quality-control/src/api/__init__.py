"""HTTP routers bound one-to-one to contract operationIds.

The routers land with the real repository (tasks phase 4), so that no endpoint
ships against a fake store.
"""
