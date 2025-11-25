"""FastAPI application for budget proposal statistics."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from graphql_client import graphql_client
from gcs_client import gcs_client
from statistics import (
    generate_statistics_by_legislator,
    generate_statistics_by_department,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Budget Proposal Statistics API",
    description="API for generating statistics from budget proposals",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Budget Proposal Statistics API",
        "endpoints": {
            "/api/statistics/by-legislator": "Get statistics organized by legislator",
            "/api/statistics/by-department": "Get statistics organized by department",
        },
    }


@app.get("/api/statistics/by-legislator")
async def get_statistics_by_legislator(
    year: Optional[int] = Query(None, description="Filter by specific budget year")
):
    """
    Get budget proposal statistics organized by legislator.
    
    Returns statistics for each budget year including:
    - Overall statistics
    - Per-legislator statistics (proposer-only and all-involved)
    
    Query Parameters:
    - year: Optional budget year to filter results
    """
    try:
        logger.info(f"Fetching statistics by legislator (year={year})")
        
        # Fetch all required data
        proposals = await graphql_client.fetch_proposals()
        people = await graphql_client.fetch_people()
        budget_years = await graphql_client.fetch_budget_years()
        
        logger.info(f"Fetched {len(proposals)} proposals, {len(people)} people, {len(budget_years)} budget years")
        
        # Filter by year if specified
        if year is not None:
            budget_years = [y for y in budget_years if y["year"] == year]
            if not budget_years:
                raise HTTPException(status_code=404, detail=f"Budget year {year} not found")
        
        # Generate statistics
        stats = generate_statistics_by_legislator(proposals, people, budget_years)
        
        logger.info(f"Generated statistics for {len(stats)} years")
        
        return JSONResponse(content=stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/statistics/by-department")
async def get_statistics_by_department(
    year: Optional[int] = Query(None, description="Filter by specific budget year")
):
    """
    Get budget proposal statistics organized by department.
    
    Returns statistics for each budget year including:
    - Overall statistics
    - Per-department statistics
    
    Query Parameters:
    - year: Optional budget year to filter results
    """
    try:
        logger.info(f"Fetching statistics by department (year={year})")
        
        # Fetch all required data
        proposals = await graphql_client.fetch_proposals()
        budget_years = await graphql_client.fetch_budget_years()
        
        logger.info(f"Fetched {len(proposals)} proposals, {len(budget_years)} budget years")
        
        # Filter by year if specified
        if year is not None:
            budget_years = [y for y in budget_years if y["year"] == year]
            if not budget_years:
                raise HTTPException(status_code=404, detail=f"Budget year {year} not found")
        
        # Generate statistics
        stats = generate_statistics_by_department(proposals, budget_years)
        
        logger.info(f"Generated statistics for {len(stats)} years")
        
        return JSONResponse(content=stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/upload/by-legislator")
async def upload_statistics_by_legislator(
    year: Optional[int] = Query(None, description="Filter by specific budget year"),
    use_latest: bool = Query(True, description="Use 'latest' filename instead of timestamp")
):
    """
    Generate and upload budget proposal statistics organized by legislator to GCS.
    
    Returns the GCS path of the uploaded file.
    
    Query Parameters:
    - year: Optional budget year to filter results
    - use_latest: If true, uploads as 'by-legislator_latest.json', otherwise uses timestamp
    """
    try:
        logger.info(f"Received request: POST /api/upload/by-legislator (year={year}, use_latest={use_latest})")
        
        # Fetch all required data
        logger.info("Fetching data from GraphQL...")
        proposals = await graphql_client.fetch_proposals()
        people = await graphql_client.fetch_people()
        budget_years = await graphql_client.fetch_budget_years()
        
        # Filter by year if specified
        if year is not None:
            budget_years = [y for y in budget_years if y["year"] == year]
            if not budget_years:
                logger.warning(f"Budget year {year} not found")
                raise HTTPException(status_code=404, detail=f"Budget year {year} not found")
        
        # Generate statistics
        logger.info("Generating statistics...")
        stats = generate_statistics_by_legislator(proposals, people, budget_years)
        logger.info(f"Statistics generated. Count: {len(stats)} years")
        
        # Upload to GCS
        logger.info("Initiating GCS upload...")
        if use_latest:
            gcs_path = gcs_client.upload_latest_statistics("by-legislator", stats)
        else:
            gcs_path = gcs_client.upload_statistics("by-legislator", stats)
        
        logger.info(f"Successfully uploaded to {gcs_path}")
        
        return {
            "status": "success",
            "gcs_path": gcs_path,
            "years_count": len(stats),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/upload/by-department")
async def upload_statistics_by_department(
    year: Optional[int] = Query(None, description="Filter by specific budget year"),
    use_latest: bool = Query(True, description="Use 'latest' filename instead of timestamp")
):
    """
    Generate and upload budget proposal statistics organized by department to GCS.
    
    Returns the GCS path of the uploaded file.
    
    Query Parameters:
    - year: Optional budget year to filter results
    - use_latest: If true, uploads as 'by-department_latest.json', otherwise uses timestamp
    """
    try:
        logger.info(f"Generating and uploading statistics by department (year={year})")
        
        # Fetch all required data
        proposals = await graphql_client.fetch_proposals()
        budget_years = await graphql_client.fetch_budget_years()
        
        # Filter by year if specified
        if year is not None:
            budget_years = [y for y in budget_years if y["year"] == year]
            if not budget_years:
                raise HTTPException(status_code=404, detail=f"Budget year {year} not found")
        
        # Generate statistics
        stats = generate_statistics_by_department(proposals, budget_years)
        
        # Upload to GCS
        if use_latest:
            gcs_path = gcs_client.upload_latest_statistics("by-department", stats)
        else:
            gcs_path = gcs_client.upload_statistics("by-department", stats)
        
        logger.info(f"Successfully uploaded to {gcs_path}")
        
        return {
            "status": "success",
            "gcs_path": gcs_path,
            "years_count": len(stats),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
