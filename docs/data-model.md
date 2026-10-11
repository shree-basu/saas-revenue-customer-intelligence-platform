# Dimensional core contract

`dim_account` is **one current row per account_id** from the validated CRM batch. Its deterministic MD5 key is a stable identifier for the natural key, not an SCD2 version key. `dim_product` is one row per product_id with the same key policy. `dim_date` is one row per **observed** non-null business date; it is a sparse calendar and must not be used to infer that absent dates were processed. Its integer key is YYYYMMDD.

Day 3 facts join these current dimensions. Thus their account attributes are **current-state classifications**, not as-of-event historical attributes. A later historical account snapshot must have a distinct version key and explicit validity interval. As-of joins, late corrections and replay-safe incrementality are not implemented by this dimension build; they remain Days 5+. Do not present current-state joins as historical SCD2 analytics.
