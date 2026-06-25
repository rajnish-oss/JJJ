import os
from datetime import datetime, timezone
from typing import Any, Mapping, Dict, Optional
from dotenv import load_dotenv
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from pydantic import BaseModel, ValidationError

from .model import CivicAwarenessReportCreate

# MongoDB Connection Configuration
load_dotenv()
MONGO_DETAILS = os.getenv("MONGO_URI")

if not MONGO_DETAILS:
    raise RuntimeError("MONGO_URI environment variable is missing!")

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.civic_platform
reports_collection = db.get_collection("reports")


async def create_civic_report(
    report_data: CivicAwarenessReportCreate | BaseModel | Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Validates the input payload and asynchronously inserts a new civic awareness report 
    into MongoDB, preserving proper BSON datetime indexing structures.
    """
    # Prepare complete dictionary object payload
    validation_input = (
        report_data.model_dump() if isinstance(report_data, BaseModel) else report_data
    )
    
    try:
        validated_report = CivicAwarenessReportCreate.model_validate(validation_input)
    except ValidationError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_error.errors(),
        ) from validation_error

    # Dump to a standard python dictionary for database insertion
    document = validated_report.model_dump()
    
    # Store as true native datetimes so MongoDB can handle index ranges and sorting natively
    current_time = datetime.now(timezone.utc)
    document["created_at"] = current_time
    document["updated_at"] = current_time

    try:
        # Save record asynchronously into MongoDB collection
        result = await reports_collection.insert_one(document)
        
        # Retrieve freshly generated document
        inserted_document = await reports_collection.find_one({"_id": result.inserted_id})
        
        if inserted_document is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document was inserted but could not be verified after creation."
            )
            
        # Coerce ObjectId to string format for Pydantic serialization
        inserted_document["_id"] = str(inserted_document["_id"])
        return inserted_document

    except DuplicateKeyError as duplicate_error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A profile record for organizational entityalready exists."
        ) from duplicate_error

    except PyMongoError as network_or_db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection offline or query failed: {str(network_or_db_error)}"
        ) from network_or_db_error


async def retrieve_report(org_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single audited infrastructure report using its unique organization name.
    """
    try:
        report = await reports_collection.find_one({"organization": org_name})
        
        if report is None:
            return None
        
        report["_id"] = str(report["_id"])
        return report
        
    except PyMongoError as network_or_db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity issue: {str(network_or_db_error)}"
        ) from network_or_db_error