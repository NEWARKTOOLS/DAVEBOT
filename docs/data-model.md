# DAVEBOT Data Model (Draft)

This draft describes the minimum viable domain entities to support quoting, job tracking, and inventory.

## Core Entities

### Customer

- id
- name
- billing_address
- shipping_address
- contacts[]
- pricing_terms
- brand_assets (logo, quote template settings)

### Job

- id
- job_type (new tool, diecast, repair, modification, one-off)
- status (enquiry, quoted, ordered, in_design, machining, assembly, sampling, delivered, closed)
- customer_id
- quote_id
- tool_id
- revisions[]
- target_dates[] (planned/actual per stage)

### Quote

- id
- customer_id
- job_id
- version
- created_at
- valid_until
- assumptions
- line_items[]
- totals (material, labor, overhead, profit, tax)
- document_uri

### Tool

- id
- tool_number
- cavity_count
- moulding_material
- steel_spec
- hot_runner (boolean)
- tryouts[]
- sampling_results[]

### RoutingStep

- id
- job_id
- step_name (design, CNC, EDM, etc.)
- planned_hours
- actual_hours
- status

### InventoryItem

- id
- category (ancillary, plate, material, standard component, consumable)
- description
- unit
- stock_on_hand
- reserved
- reorder_point

### BOMItem

- id
- job_id
- inventory_item_id
- quantity
- unit_cost

### CostingParams

- id
- category (tool_quote, moulding_quote)
- parameters (json)
- effective_date

## Relationships (high level)

- A **Job** belongs to one **Customer** and may reference one **Quote** and one **Tool**.
- A **Quote** is versioned and stored with a document artifact.
- **RoutingSteps** break down **Jobs** into scheduled work.
- **InventoryItems** are consumed by **BOMItems** linked to a job.
- **CostingParams** store the calculation assumptions used when creating quotes.

## Suggested Indexes

- Job status + customer for search dashboards.
- Tool number and customer for historical lookup.
- Quote version + job id.
