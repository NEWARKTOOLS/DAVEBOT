from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from flask import Flask, jsonify, request


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


@dataclass
class Customer:
    name: str
    billing_address: str
    id: UUID = field(default_factory=uuid4)
    shipping_address: Optional[str] = None
    contacts: List[str] = field(default_factory=list)
    pricing_terms: Optional[str] = None
    brand_assets: Dict[str, str] = field(default_factory=dict)


@dataclass
class QuoteLineItem:
    description: str
    unit_cost: float
    quantity: int = 1

    @property
    def total(self) -> float:
        return self.quantity * self.unit_cost


@dataclass
class Quote:
    customer_id: UUID
    id: UUID = field(default_factory=uuid4)
    job_id: Optional[UUID] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[date] = None
    assumptions: Dict[str, str] = field(default_factory=dict)
    line_items: List[QuoteLineItem] = field(default_factory=list)
    totals: Dict[str, float] = field(default_factory=dict)
    document_uri: Optional[str] = None


@dataclass
class Tool:
    tool_number: str
    cavity_count: int
    moulding_material: str
    steel_spec: str
    id: UUID = field(default_factory=uuid4)
    hot_runner: bool = False
    tryouts: List[str] = field(default_factory=list)
    sampling_results: List[str] = field(default_factory=list)


@dataclass
class RoutingStep:
    job_id: UUID
    step_name: str
    planned_hours: float
    id: UUID = field(default_factory=uuid4)
    actual_hours: Optional[float] = None
    status: Optional[str] = None


@dataclass
class InventoryItem:
    category: InventoryCategory
    description: str
    unit: str
    stock_on_hand: float
    id: UUID = field(default_factory=uuid4)
    reserved: float = 0
    reorder_point: float = 0


@dataclass
class BOMItem:
    job_id: UUID
    inventory_item_id: UUID
    quantity: float
    unit_cost: float
    id: UUID = field(default_factory=uuid4)


@dataclass
class Job:
    job_type: JobType
    customer_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.enquiry
    quote_id: Optional[UUID] = None
    tool_id: Optional[UUID] = None
    revisions: List[str] = field(default_factory=list)
    target_dates: Dict[str, date] = field(default_factory=dict)


@dataclass
class ToolingQuoteInput:
    engineering_hours: float
    machining_hours: float
    labor_rate_per_hour: float
    material_cost: float
    component_cost: float
    overhead_rate: float
    margin_rate: float


@dataclass
class ToolingQuoteResult:
    labor_subtotal: float
    material_subtotal: float
    component_subtotal: float
    overhead: float
    margin: float
    total: float


@dataclass
class MouldingQuoteInput:
    part_weight_kg: float
    material_cost_per_kg: float
    cycle_time_seconds: float
    machine_rate_per_hour: float
    scrap_rate: float
    packaging_cost_per_unit: float
    margin_rate: float


@dataclass
class MouldingQuoteResult:
    shots_per_hour: float
    material_cost_per_shot: float
    machine_cost_per_shot: float
    scrap_allowance_cost: float
    unit_cost: float
    quoted_unit_price: float


app = Flask(__name__)

customers: Dict[UUID, Customer] = {}
quotes: Dict[UUID, Quote] = {}
jobs: Dict[UUID, Job] = {}
tools: Dict[UUID, Tool] = {}
routing_steps: Dict[UUID, RoutingStep] = {}
inventory: Dict[UUID, InventoryItem] = {}
boms: Dict[UUID, BOMItem] = {}


@app.get("/")
def root():
    return jsonify({"message": "DAVEBOT WMS is running", "docs": "/health"})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/customers")
def create_customer():
    payload = request.get_json(force=True)
    customer = Customer(**payload)
    customers[customer.id] = customer
    return jsonify(_serialize(customer)), 201


@app.get("/customers")
def list_customers():
    return jsonify([_serialize(item) for item in customers.values()])


@app.post("/jobs")
def create_job():
    payload = request.get_json(force=True)
    customer_id = UUID(payload["customer_id"])
    if customer_id not in customers:
        return jsonify({"error": "Customer not found"}), 404
    job = Job(
        job_type=JobType(payload["job_type"]),
        customer_id=customer_id,
        status=JobStatus(payload.get("status", JobStatus.enquiry.value)),
        revisions=payload.get("revisions", []),
        target_dates=_parse_dates(payload.get("target_dates", {})),
    )
    jobs[job.id] = job
    return jsonify(_serialize(job)), 201


@app.get("/jobs")
def list_jobs():
    return jsonify([_serialize(item) for item in jobs.values()])


@app.post("/quotes")
def create_quote():
    payload = request.get_json(force=True)
    customer_id = UUID(payload["customer_id"])
    if customer_id not in customers:
        return jsonify({"error": "Customer not found"}), 404
    job_id = payload.get("job_id")
    parsed_job_id = UUID(job_id) if job_id else None
    if parsed_job_id and parsed_job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    line_items = [QuoteLineItem(**item) for item in payload.get("line_items", [])]
    quote = Quote(
        customer_id=customer_id,
        job_id=parsed_job_id,
        version=payload.get("version", 1),
        valid_until=_parse_date(payload.get("valid_until")),
        assumptions=payload.get("assumptions", {}),
        line_items=line_items,
        document_uri=payload.get("document_uri"),
    )
    quote.totals = _calculate_quote_totals(quote)
    quotes[quote.id] = quote
    if parsed_job_id:
        job = jobs[parsed_job_id]
        job.quote_id = quote.id
        job.status = JobStatus.quoted
        jobs[job.id] = job
    return jsonify(_serialize(quote)), 201


@app.get("/quotes")
def list_quotes():
    return jsonify([_serialize(item) for item in quotes.values()])


@app.post("/inventory")
def create_inventory_item():
    payload = request.get_json(force=True)
    item = InventoryItem(
        category=InventoryCategory(payload["category"]),
        description=payload["description"],
        unit=payload["unit"],
        stock_on_hand=payload["stock_on_hand"],
        reserved=payload.get("reserved", 0),
        reorder_point=payload.get("reorder_point", 0),
    )
    inventory[item.id] = item
    return jsonify(_serialize(item)), 201


@app.get("/inventory")
def list_inventory_items():
    return jsonify([_serialize(item) for item in inventory.values()])


@app.post("/tools")
def create_tool():
    payload = request.get_json(force=True)
    tool = Tool(
        tool_number=payload["tool_number"],
        cavity_count=payload["cavity_count"],
        moulding_material=payload["moulding_material"],
        steel_spec=payload["steel_spec"],
        hot_runner=payload.get("hot_runner", False),
        tryouts=payload.get("tryouts", []),
        sampling_results=payload.get("sampling_results", []),
    )
    tools[tool.id] = tool
    return jsonify(_serialize(tool)), 201


@app.get("/tools")
def list_tools():
    return jsonify([_serialize(item) for item in tools.values()])


@app.post("/routing-steps")
def create_routing_step():
    payload = request.get_json(force=True)
    job_id = UUID(payload["job_id"])
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    step = RoutingStep(
        job_id=job_id,
        step_name=payload["step_name"],
        planned_hours=payload["planned_hours"],
        actual_hours=payload.get("actual_hours"),
        status=payload.get("status"),
    )
    routing_steps[step.id] = step
    return jsonify(_serialize(step)), 201


@app.get("/routing-steps")
def list_routing_steps():
    return jsonify([_serialize(item) for item in routing_steps.values()])


@app.post("/boms")
def create_bom_item():
    payload = request.get_json(force=True)
    job_id = UUID(payload["job_id"])
    inventory_item_id = UUID(payload["inventory_item_id"])
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    if inventory_item_id not in inventory:
        return jsonify({"error": "Inventory item not found"}), 404
    item = BOMItem(
        job_id=job_id,
        inventory_item_id=inventory_item_id,
        quantity=payload["quantity"],
        unit_cost=payload["unit_cost"],
    )
    boms[item.id] = item
    return jsonify(_serialize(item)), 201


@app.get("/boms")
def list_boms():
    return jsonify([_serialize(item) for item in boms.values()])


@app.post("/calculators/tooling")
def calculate_tooling():
    payload = ToolingQuoteInput(**request.get_json(force=True))
    result = calculate_tooling_quote(payload)
    return jsonify(_serialize(result))


@app.post("/calculators/moulding")
def calculate_moulding():
    payload = MouldingQuoteInput(**request.get_json(force=True))
    result = calculate_moulding_quote(payload)
    return jsonify(_serialize(result))


def calculate_tooling_quote(payload: ToolingQuoteInput) -> ToolingQuoteResult:
    if payload.overhead_rate < 0 or payload.margin_rate < 0:
        raise ValueError("Rates must be positive")
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


def calculate_moulding_quote(payload: MouldingQuoteInput) -> MouldingQuoteResult:
    if payload.cycle_time_seconds <= 0:
        raise ValueError("Cycle time must be positive")
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


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        data = asdict(value)
        return {key: _serialize(item) for key, item in data.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_dates(values: Dict[str, str]) -> Dict[str, date]:
    return {key: date.fromisoformat(val) for key, val in values.items()}


if __name__ == "__main__":
    app.run(debug=True)
