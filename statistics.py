"""Statistics calculation module for budget proposals."""

from typing import Dict, List, Any
from collections import defaultdict


class ProposalStats:
    """Container for proposal statistics."""
    
    def __init__(self):
        self.reduction_amount: float = 0.0
        self.reduction_count: int = 0
        self.freeze_amount: float = 0.0
        self.freeze_count: int = 0
        self.other_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "reductionAmount": int(self.reduction_amount) if self.reduction_amount else 0,
            "reductionCount": self.reduction_count,
            "freezeAmount": int(self.freeze_amount) if self.freeze_amount else 0,
            "freezeCount": self.freeze_count,
            "otherCount": self.other_count,
        }


def add_proposal_to_stats(stats: ProposalStats, proposal: Dict[str, Any]) -> None:
    """Add a proposal's data to statistics."""
    proposal_types = proposal.get("proposalTypes", []) or []
    
    if "reduce" in proposal_types:
        stats.reduction_count += 1
        stats.reduction_amount += proposal.get("reductionAmount") or 0.0
    
    if "freeze" in proposal_types:
        stats.freeze_count += 1
        stats.freeze_amount += proposal.get("freezeAmount") or 0.0
    
    if "other" in proposal_types:
        stats.other_count += 1


def calculate_overall_stats(proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall statistics for all proposals."""
    stats = ProposalStats()
    
    for proposal in proposals:
        add_proposal_to_stats(stats, proposal)
    
    return stats.to_dict()


def calculate_legislator_stats(
    proposals: List[Dict[str, Any]], 
    people: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate statistics for each legislator.
    Returns both proposer-only and all-involved statistics.
    """
    # Create a mapping of person_id to person data
    people_map = {person["id"]: person for person in people}
    
    # Track statistics for each person
    legislator_stats = {}
    
    for person in people:
        person_id = person["id"]
        legislator_stats[person_id] = {
            "peopleId": person_id,
            "name": person["name"],
            "proposer_only": ProposalStats(),
            "all_involved": ProposalStats(),
        }
    
    # Process each proposal
    for proposal in proposals:
        proposers = proposal.get("proposers", []) or []
        co_signers = proposal.get("coSigners", []) or []
        
        # Get IDs
        proposer_ids = {p["id"] for p in proposers}
        co_signer_ids = {p["id"] for p in co_signers}
        all_involved_ids = proposer_ids | co_signer_ids
        
        # Add to proposer-only stats
        for person_id in proposer_ids:
            if person_id in legislator_stats:
                add_proposal_to_stats(legislator_stats[person_id]["proposer_only"], proposal)
        
        # Add to all-involved stats
        for person_id in all_involved_ids:
            if person_id in legislator_stats:
                add_proposal_to_stats(legislator_stats[person_id]["all_involved"], proposal)
    
    # Convert to output format
    result = []
    for person_id, stats in legislator_stats.items():
        # Only include legislators who have at least one proposal
        if stats["proposer_only"].reduction_count > 0 or \
           stats["proposer_only"].freeze_count > 0 or \
           stats["proposer_only"].other_count > 0 or \
           stats["all_involved"].reduction_count > 0 or \
           stats["all_involved"].freeze_count > 0 or \
           stats["all_involved"].other_count > 0:
            result.append({
                "peopleId": stats["peopleId"],
                "name": stats["name"],
                "proposerOnly": stats["proposer_only"].to_dict(),
                "allInvolved": stats["all_involved"].to_dict(),
            })
    
    # Sort by name
    result.sort(key=lambda x: x["name"])
    
    return result


def calculate_department_stats(proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate statistics for each department (government).
    """
    # Track statistics for each department
    department_stats = defaultdict(lambda: {
        "government_id": None,
        "government_name": None,
        "stats": ProposalStats(),
    })
    
    for proposal in proposals:
        government = proposal.get("government")
        if not government:
            continue
        
        gov_id = government["id"]
        gov_name = government.get("name", "Unknown")
        
        if department_stats[gov_id]["government_id"] is None:
            department_stats[gov_id]["government_id"] = gov_id
            department_stats[gov_id]["government_name"] = gov_name
        
        add_proposal_to_stats(department_stats[gov_id]["stats"], proposal)
    
    # Convert to output format
    result = []
    for gov_id, data in department_stats.items():
        result.append({
            "governmentId": data["government_id"],
            "name": data["government_name"],
            **data["stats"].to_dict(),
        })
    
    # Sort by name
    result.sort(key=lambda x: x["name"])
    
    return result


def generate_statistics_by_legislator(
    proposals: List[Dict[str, Any]], 
    people: List[Dict[str, Any]],
    budget_years: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate complete statistics organized by budget year and legislator.
    """
    # Group proposals by year
    proposals_by_year = defaultdict(list)
    for proposal in proposals:
        year_data = proposal.get("year")
        if year_data:
            year_id = year_data["id"]
            proposals_by_year[year_id].append(proposal)
    
    # Generate statistics for each year
    result = []
    for year in budget_years:
        year_id = year["id"]
        year_proposals = proposals_by_year.get(year_id, [])
        
        if not year_proposals:
            continue
        
        year_stats = {
            "yearInfo": {
                "budgetYearId": year_id,
                "year": year["year"],
            },
            "overall": calculate_overall_stats(year_proposals),
            "legislators": calculate_legislator_stats(year_proposals, people),
        }
        
        result.append(year_stats)
    
    # Sort by year descending
    result.sort(key=lambda x: x["yearInfo"]["year"], reverse=True)
    
    return result


def generate_statistics_by_department(
    proposals: List[Dict[str, Any]],
    budget_years: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate complete statistics organized by budget year and department.
    """
    # Group proposals by year
    proposals_by_year = defaultdict(list)
    for proposal in proposals:
        year_data = proposal.get("year")
        if year_data:
            year_id = year_data["id"]
            proposals_by_year[year_id].append(proposal)
    
    # Generate statistics for each year
    result = []
    for year in budget_years:
        year_id = year["id"]
        year_proposals = proposals_by_year.get(year_id, [])
        
        if not year_proposals:
            continue
        
        year_stats = {
            "yearInfo": {
                "budgetYearId": year_id,
                "year": year["year"],
            },
            "overall": calculate_overall_stats(year_proposals),
            "departments": calculate_department_stats(year_proposals),
        }
        
        result.append(year_stats)
    
    # Sort by year descending
    result.sort(key=lambda x: x["yearInfo"]["year"], reverse=True)
    
    return result
