"""
One-time setup script: creates the Databricks secret scope and stores the
Lakebase Postgres connection URL. Run this locally (with the Databricks CLI 
configured) or from a notebook - never commit the resulting secret value anywhere.

Usage:
    python set_secrets.py
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace
import getpass

w = WorkspaceClient()

# Create secret scope
print("Creating secret scope...")
try:
    w.secrets.create_scope(scope="database")
    print("✓ Created 'database' scope")
except Exception as e:
    print(f"'database' scope may already exist: {e}")

# Store Lakebase URL
print("\nStoring secret...")
w.secrets.put_secret(
    scope="database",
    key="lakebase-url",
    string_value=getpass.getpass("Paste your Lakebase URL: ")
)
print("✓ Stored Lakebase URL")

# Set ACL to allow all users to read the secret
print("\nSetting permissions...")
w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)
print("✓ Set READ permission for 'database' scope")

print("\n✅ Setup complete! Lakebase connection is now available in your workspace.")
print("\nTo use in your code:")
print("  - Lakebase URL: dbutils.secrets.get('database', 'lakebase-url')")
