# DAVEBOT Product Requirements

## Vision

Deliver a "toolmaker’s best friend" platform that manages toolmaking and moulding jobs end-to-end. The system should provide fast, repeatable quoting, keep material and component inventory accurate, and track every job from enquiry to sampling. The DAVEBOT assistant should answer and calculate common tooling questions based on shop standards and captured historical data.

## Scope

### Job Management (WMS)

- **Job types**: new plastic mould tools, diecast tools, repairs, modifications, and one-offs.
- **Stages**: enquiry → quote → order → design → machining → assembly → sampling/tryout → delivery → close.
- **Traceability**: each job links to customer, quote, BOM, routing steps, revisions, and inspection results.
- **Milestones**: planned vs actual dates for each stage.

### Quoting & Documentation

- **Quote builder** with configurable assumptions:
  - tool size / complexity
  - cavity count
  - material type (e.g., P20, H13)
  - standard components (guides, ejectors, hot runner, etc.)
  - finishing and texture
  - inspection and sampling
- **Auto-generated documentation** for quotes and job packs:
  - company logo, address, and contact info
  - quote terms and validity
  - breakdown and exclusions
- **Customer assets** (logos, PO formats, delivery requirements).

### Calculators

1. **Plastic mould tooling quote**
   - engineering hours
   - machining hours
   - material weight and waste
   - standard components
   - tryout samples
2. **Moulding quote (production)**
   - cycle time
   - material cost per shot
   - machine rate
   - scrap/overhead

> Note: Pricing formulas should be configurable per company standards. The system should record which parameters were used for every quote to allow audits later.

### Inventory (Ancillaries / Plates / Materials)

- Stock levels, reserved quantities, and reorder thresholds.
- Categorization for plates, steels, standard components, ancillaries, and consumables.
- Traceability of materials used on each job (for cost roll-up).

### Tool Tracking & Sampling

- Track tool build status, tryout history, and sampling outcomes.
- Record issues, modifications, and corrective actions.
- Link revisions to design and manufacturing data.

### DAVEBOT Assistant

- Provide a conversational assistant that can:
  - explain toolmaking and moulding concepts
  - estimate or compare costs based on configuration
  - calculate shot weights, cycle time estimates, and machine requirements
  - answer FAQ using company policies and historical data

## Key Roles

- **Sales/Estimator**: builds quotes and sends documentation.
- **Toolmaker/Planner**: creates routings and tracks progress.
- **Purchasing**: manages materials and ancillaries.
- **Management**: sees margins, utilization, and forecast.

## Non-Functional Requirements

- Auditable changes for quotes and job statuses.
- Exportable reports (PDF/CSV).
- Secure access with role-based permissions.
- Scalable data model to handle multiple sites or teams.

## Open Questions

- Target stack (web framework, database)?
- How to ingest or sync historical job data?
- How accurate should the initial pricing formulas be vs. company tuning?
