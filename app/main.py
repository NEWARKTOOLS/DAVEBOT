from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class JobType(str, Enum):
    new_tool = "new_tool"
    diecast = "diecast"
    repair = "repair"
    modification = "modification"
    one_off = "one_off"


class JobStatus(str, Enum):
    enquiry = "enquiry"
    quoted = "quoted"
    ordered = "ordered"
    in_design = "in_design"
    machining = "machining"
    assembly = "assembly"
    sampling = "sampling"
    delivered = "delivered"
    closed = "closed"


class InventoryCategory(str, Enum):
    ancillary = "ancillary"
    plate = "plate"
    material = "material"
    standard_component = "standard_component"
    consumable = "consumable"


class Customer(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    billing_address: str
    shipping_address: Optional[str] = None
    contacts: List[str] = Field(default_factory=list)
    pricing_terms: Optional[str] = None
    brand_assets: Dict[str, str] = Field(default_factory=dict)


class QuoteLineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_cost: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_cost


class Quote(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    customer_id: UUID
    job_id: Optional[UUID] = None
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[date] = None
    assumptions: Dict[str, str] = Field(default_factory=dict)
    line_items: List[QuoteLineItem] = Field(default_factory=list)
    totals: Dict[str, float] = Field(default_factory=dict)
    document_uri: Optional[str] = None


class Tool(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tool_number: str
    cavity_count: int
    moulding_material: str
    steel_spec: str
    hot_runner: bool = False
    tryouts: List[str] = Field(default_factory=list)
    sampling_results: List[str] = Field(default_factory=list)


class RoutingStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    step_name: str
    planned_hours: float
    actual_hours: Optional[float] = None
    status: Optional[str] = None


class InventoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: InventoryCategory
    description: str
    unit: str
    stock_on_hand: float
    reserved: float = 0
    reorder_point: float = 0


class BOMItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    inventory_item_id: UUID
    quantity: float
    unit_cost: float


class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_type: JobType
    status: JobStatus = JobStatus.enquiry
    customer_id: UUID
    quote_id: Optional[UUID] = None
    tool_id: Optional[UUID] = None
    revisions: List[str] = Field(default_factory=list)
    target_dates: Dict[str, date] = Field(default_factory=dict)


class ToolingQuoteInput(BaseModel):
    engineering_hours: float
    machining_hours: float
    labor_rate_per_hour: float
    material_cost: float
    component_cost: float
    overhead_rate: float = Field(ge=0, description="Overhead as fraction of labor")
    margin_rate: float = Field(ge=0, description="Margin as fraction of subtotal")


class ToolingQuoteResult(BaseModel):
    labor_subtotal: float
    material_subtotal: float
    component_subtotal: float
    overhead: float
    margin: float
    total: float


class MouldingQuoteInput(BaseModel):
    part_weight_kg: float
    material_cost_per_kg: float
    cycle_time_seconds: float
    machine_rate_per_hour: float
    scrap_rate: float = Field(ge=0, description="Scrap as fraction of units")
    packaging_cost_per_unit: float = 0
    margin_rate: float = Field(ge=0)


class MouldingQuoteResult(BaseModel):
    shots_per_hour: float
    material_cost_per_shot: float
    machine_cost_per_shot: float
    scrap_allowance_cost: float
    unit_cost: float
    quoted_unit_price: float


app = FastAPI(title="DAVEBOT WMS")

customers: Dict[UUID, Customer] = {}
quotes: Dict[UUID, Quote] = {}
jobs: Dict[UUID, Job] = {}
tools: Dict[UUID, Tool] = {}
routing_steps: Dict[UUID, RoutingStep] = {}
inventory: Dict[UUID, InventoryItem] = {}
boms: Dict[UUID, BOMItem] = {}


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "DAVEBOT WMS is running",
        "docs": "/docs",
    }


@app.post("/customers", response_model=Customer)
def create_customer(customer: Customer) -> Customer:
    customers[customer.id] = customer
    return customer


@app.get("/customers", response_model=List[Customer])
def list_customers() -> List[Customer]:
    return list(customers.values())


@app.post("/jobs", response_model=Job)
def create_job(job: Job) -> Job:
    if job.customer_id not in customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    jobs[job.id] = job
    return job


@app.get("/jobs", response_model=List[Job])
def list_jobs() -> List[Job]:
    return list(jobs.values())


@app.post("/quotes", response_model=Quote)
def create_quote(quote: Quote) -> Quote:
    if quote.customer_id not in customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    if quote.job_id and quote.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    quote.totals = _calculate_quote_totals(quote)
    quotes[quote.id] = quote
    if quote.job_id:
        job = jobs[quote.job_id]
        job.quote_id = quote.id
        job.status = JobStatus.quoted
        jobs[job.id] = job
    return quote


@app.get("/quotes", response_model=List[Quote])
def list_quotes() -> List[Quote]:
    return list(quotes.values())


@app.post("/inventory", response_model=InventoryItem)
def create_inventory_item(item: InventoryItem) -> InventoryItem:
    inventory[item.id] = item
    return item


@app.get("/inventory", response_model=List[InventoryItem])
def list_inventory_items() -> List[InventoryItem]:
    return list(inventory.values())


@app.post("/tools", response_model=Tool)
def create_tool(tool: Tool) -> Tool:
    tools[tool.id] = tool
    return tool


@app.get("/tools", response_model=List[Tool])
def list_tools() -> List[Tool]:
    return list(tools.values())


@app.post("/routing-steps", response_model=RoutingStep)
def create_routing_step(step: RoutingStep) -> RoutingStep:
    if step.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    routing_steps[step.id] = step
    return step


@app.get("/routing-steps", response_model=List[RoutingStep])
def list_routing_steps() -> List[RoutingStep]:
    return list(routing_steps.values())


@app.post("/boms", response_model=BOMItem)
def create_bom_item(item: BOMItem) -> BOMItem:
    if item.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    if item.inventory_item_id not in inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    boms[item.id] = item
    return item


@app.get("/boms", response_model=List[BOMItem])
def list_boms() -> List[BOMItem]:
    return list(boms.values())


@app.post("/calculators/tooling", response_model=ToolingQuoteResult)
def calculate_tooling_quote(payload: ToolingQuoteInput) -> ToolingQuoteResult:
    labor_subtotal = (payload.engineering_hours + payload.machining_hours) * payload.labor_rate_per_hour
    overhead = labor_subtotal * payload.overhead_rate
    subtotal = labor_subtotal + payload.material_cost + payload.component_cost + overhead
    margin = subtotal * payload.margin_rate
    total = subtotal + margin
    return ToolingQuoteResult(
        labor_subtotal=labor_subtotal,
        material_subtotal=payload.material_cost,
        component_subtotal=payload.component_cost,
        overhead=overhead,
        margin=margin,
        total=total,
    )


@app.post("/calculators/moulding", response_model=MouldingQuoteResult)
def calculate_moulding_quote(payload: MouldingQuoteInput) -> MouldingQuoteResult:
    shots_per_hour = 3600 / payload.cycle_time_seconds
    material_cost_per_shot = payload.part_weight_kg * payload.material_cost_per_kg
    machine_cost_per_shot = payload.machine_rate_per_hour / shots_per_hour
    scrap_allowance_cost = (material_cost_per_shot + machine_cost_per_shot) * payload.scrap_rate
    unit_cost = material_cost_per_shot + machine_cost_per_shot + scrap_allowance_cost + payload.packaging_cost_per_unit
    quoted_unit_price = unit_cost * (1 + payload.margin_rate)
    return MouldingQuoteResult(
        shots_per_hour=shots_per_hour,
        material_cost_per_shot=material_cost_per_shot,
        machine_cost_per_shot=machine_cost_per_shot,
        scrap_allowance_cost=scrap_allowance_cost,
        unit_cost=unit_cost,
        quoted_unit_price=quoted_unit_price,
    )


def _calculate_quote_totals(quote: Quote) -> Dict[str, float]:
    labor_total = 0.0
    material_total = 0.0
    component_total = 0.0
    for item in quote.line_items:
        if "labor" in item.description.lower():
            labor_total += item.total
        elif "material" in item.description.lower():
            material_total += item.total
        else:
            component_total += item.total
    subtotal = labor_total + material_total + component_total
    return {
        "labor": labor_total,
        "material": material_total,
        "components": component_total,
        "subtotal": subtotal,
    }
