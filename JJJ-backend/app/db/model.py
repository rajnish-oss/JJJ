from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class OperationalScale(BaseModel):
    """Metrics reflecting the human and financial footprint of the institution."""
    budget_allocated: str = Field(
        ..., 
        description="The approved financial budget for the fiscal year, including currency equivalents."
    )
    faculty_count: str = Field(
        ..., 
        description="Total number of academic/faculty staff members."
    )
    support_staff_count: str = Field(
        ..., 
        description="Total number of administrative, technical, and supporting staff members."
    )
    beneficiary_capacity: str = Field(
        ..., 
        description="Total number of active students or directly enrolled beneficiaries."
    )

class CivicAwarenessReport(BaseModel):
    """The complete evaluation report mapping institutional metrics and accountability gaps."""
    organization: str = Field(
        ..., 
        description="Name of the infrastructure."
    )
    fabric_of_accountability: str = Field(
        ..., 
        description="Core background, legal status, and foundational context of the institution."
    )
    human_and_financial_scale_context: str = Field(
        ..., 
        description="Introductory framing highlighting the scale and resource allocation of the entity."
    )
    scale_metrics: OperationalScale = Field(
        ..., 
        description="Granular resource, personnel, and capacity metrics."
    )
    transparency_gap_introduction: str = Field(
        ..., 
        description="Opening statement defining what high-level data is public versus what execution details remain hidden."
    )
    missing_accountability_metrics: List[str] = Field(
        ..., 
        description="Specific types of operational, financial, or contract data currently shielded from public view."
    )
    transparency_gap_conclusion: str = Field(
        ..., 
        description="Analysis of how this missing information impacts taxpayer oversight and public trust."
    )
    citizen_action_item: str = Field(
        ..., 
        description="Actionable steps a citizen can take (e.g., filing RTIs) to legally demand and uncover this data."
    )

class CivicAwarenessReportCreate(CivicAwarenessReport):
    pass


class CivicAwarenessReportResponse(CivicAwarenessReport):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}