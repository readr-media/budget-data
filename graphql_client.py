"""GraphQL client for querying Keystone API."""

import httpx
from typing import Any, Dict, List, Optional
from config import settings


class GraphQLClient:
    """Client for interacting with the Keystone GraphQL API."""
    
    def __init__(self):
        self.endpoint = settings.graphql_endpoint
        self.timeout = settings.api_timeout
        self.max_retries = settings.api_max_retries
        
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication if configured."""
        headers = {"Content-Type": "application/json"}
        
        if settings.bearer_token:
            headers["Authorization"] = f"Bearer {settings.bearer_token}"
        elif settings.api_key:
            headers["X-API-Key"] = settings.api_key
            
        return headers
    
    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query with retry logic."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        self.endpoint,
                        json={"query": query, "variables": variables or {}},
                        headers=self._get_headers(),
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "errors" in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    return data.get("data", {})
                    
                except httpx.HTTPError as e:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Failed to execute GraphQL query after {self.max_retries} attempts: {e}")
                    continue
    
    async def fetch_proposals(self, year_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all proposals with filtering criteria:
        - publishStatus = "published"
        - result = "passed"
        - mergedParentProposals = null (no parent, meaning this is not a child proposal)
        - historicalParentProposals = null (no parent, meaning this is not a child proposal)
        """
        # Build the where clause
        where_clause = """
              publishStatus: { equals: "published" }
              result: { equals: "passed" }
              mergedParentProposals: null
              historicalParentProposals: null
        """
        
        # Add year filter if provided
        if year_id:
            where_clause += f'\n              year: {{ id: {{ equals: "{year_id}" }} }}'
        
        query = f"""
        query FetchProposals {{
          proposals(
            where: {{
{where_clause}
            }}
          ) {{
            id
            proposalTypes
            reductionAmount
            freezeAmount
            year {{
              id
              year
            }}
            government {{
              id
              name
            }}
            proposers {{
              id
              name
            }}
            coSigners {{
              id
              name
            }}
          }}
        }}
        """
        
        data = await self._execute_query(query)
        return data.get("proposals", [])
    
    async def fetch_people(self) -> List[Dict[str, Any]]:
        """Fetch all people (legislators)."""
        query = """
        query FetchPeople {
          peopleList {
            id
            name
            type
          }
        }
        """
        
        data = await self._execute_query(query)
        return data.get("peopleList", [])
    
    async def fetch_budget_years(self) -> List[Dict[str, Any]]:
        """Fetch all budget years."""
        query = """
        query FetchBudgetYears {
          budgetYears {
            id
            year
          }
        }
        """
        
        data = await self._execute_query(query)
        return data.get("budgetYears", [])


# Global client instance
graphql_client = GraphQLClient()
