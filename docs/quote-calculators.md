# DAVEBOT Quote Calculators

This document defines the calculation inputs, outputs, and data capture needed for DAVEBOT quoting. The formulas below are intentionally configurable to reflect each shop’s standards.

## Shared Concepts

- **Assumptions are versioned** and stored with the quote for auditability.
- **Rates** (labor, machine, overhead) are stored in configuration and can be time-bound.
- **Materials and components** reference inventory items to preserve cost roll-up.
- **Margin** may be applied as a fixed amount or percentage.

## Tooling Quote Calculator (Plastic Mould / Diecast)

### Required Inputs

- Job type (new, repair, modification, one-off)
- Tool size / complexity class
- Cavity count
- Steel spec (e.g., P20, H13)
- Standard components (guides, ejectors, hot runner, etc.)
- Surface finish / texture requirements
- Expected tryouts / sampling rounds
- Engineering hours estimate
- Machining hours estimate (CNC, EDM, etc.)

### Derived Inputs

- Material weight and waste allowance
- Standard component bundle pricing
- Assembly and fitting hours
- Inspection and measurement time

### Outputs

- Labor subtotal
- Material subtotal
- Standard component subtotal
- Overhead
- Margin
- Total quote value

### Data to Persist with Quote

- Every input and derived value
- Rate tables used
- Material unit costs and suppliers
- Assumptions or exclusions

## Moulding Quote Calculator (Production)

### Required Inputs

- Part weight
- Material cost per kg
- Cycle time (sec)
- Machine rate per hour
- Scrap rate (%)
- Packaging and logistics cost per unit
- Secondary operations (if any)

### Derived Inputs

- Shots per hour
- Material cost per shot
- Machine cost per shot
- Scrap allowance cost

### Outputs

- Unit cost
- Total run cost
- Quoted unit price (with margin)

### Data to Persist with Quote

- Inputs, derived values, and rate tables
- Cycle-time assumptions or supporting references
- Scrap/overage assumptions

## Configuration Tables (Suggested)

- **Labor rates**: by role (designer, CNC, EDM, fitter)
- **Machine rates**: by machine type
- **Overhead factors**: fixed or % of labor
- **Material costs**: by alloy/grade and supplier
- **Standard component bundles**: predefined kits by tool type
