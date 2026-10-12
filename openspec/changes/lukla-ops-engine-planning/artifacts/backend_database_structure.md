/supabase
 ├── /migrations            # Skema Database & Triggers
 │    ├── 01_schema_rbac.sql         # 8 Role Enum & User Profiles
 │    ├── 02_schema_ledger.sql       # Chart of Accounts, Journal Entries (Append-only)
 │    ├── 03_schema_inventory.sql    # Multi-tenant Stock Lots (Client_ID, Order_ID)
 │    ├── 04_rls_policies.sql        # Row Level Security untuk isolasi Client B2B
 │    └── 05_trigger_guardrail.sql   # PL/pgSQL function: validate_material_dispatch()
 ├── /functions             # Edge Functions (Deno/Node.js)
 │    ├── calculate-payroll          # Algoritma Upah, Uang Makan, Bonus QC
 │    └── allocate-overhead          # Skrip bulanan pembagian biaya utilitas
 └── /tests                 # DB Logic Tests (pgTAP)

