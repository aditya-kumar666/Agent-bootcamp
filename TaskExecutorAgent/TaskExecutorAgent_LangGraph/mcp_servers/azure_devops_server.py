"""MCP Server for Azure DevOps integration.

Provides tools for accessing Azure DevOps work items, pipelines, and repositories.
Requires environment variables:
- AZURE_DEVOPS_ORG: Organization name
- AZURE_DEVOPS_PROJECT: Project name  
- AZURE_DEVOPS_PAT: Personal Access Token
"""

import os
import json
from pathlib import Path
from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("FastMCP not installed. Run: pip install fastmcp")

# Initialize MCP server
mcp = FastMCP("azure_devops")

# Azure DevOps configuration
ORG = os.getenv("AZURE_DEVOPS_ORG", "")
PROJECT = os.getenv("AZURE_DEVOPS_PROJECT", "")
PAT = os.getenv("AZURE_DEVOPS_PAT", "")
BASE_URL = f"https://dev.azure.com/{ORG}/{PROJECT}"


@mcp.tool()
def list_work_items(query: str = "", work_item_type: str = "Task") -> str:
    """List Azure DevOps work items.
    
    Args:
        query: Optional WIQL query filter (e.g., "state=Active")
        work_item_type: Work item type to filter (Task, Bug, Feature, etc.)
    
    Returns:
        JSON list of work items with id, title, state, assigned_to
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured (AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT)"
    
    try:
        import base64
        import requests
        
        # Azure DevOps WIQL endpoint
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/wiql?api-version=7.0"
        
        # Default query or custom
        wiql_query = query or f"SELECT [System.Id], [System.Title], [System.State] FROM workitems WHERE [System.WorkItemType]='{work_item_type}'"
        
        # Basic auth with PAT
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json={"query": wiql_query}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return json.dumps(data.get("workItems", []), indent=2)
        else:
            return f"ERROR: Azure DevOps API returned {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def get_work_item(work_item_id: int) -> str:
    """Get details of a specific work item.
    
    Args:
        work_item_id: Work item ID
    
    Returns:
        JSON object with work item details
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured"
    
    try:
        import base64
        import requests
        
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/workitems/{work_item_id}?api-version=7.0"
        
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        else:
            return f"ERROR: {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def update_work_item(work_item_id: int, fields: str) -> str:
    """Update work item fields.
    
    Args:
        work_item_id: Work item ID
        fields: JSON object of fields to update (e.g., {"System.State": "Done"})
    
    Returns:
        Success message with updated work item
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured"
    
    try:
        import base64
        import requests
        
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/workitems/{work_item_id}?api-version=7.0"
        
        # Parse fields JSON
        fields_dict = json.loads(fields)
        
        # Format as Azure DevOps patch operations
        patch_ops = [{"op": "replace", "path": f"/fields/{k}", "value": v} for k, v in fields_dict.items()]
        
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json-patch+json"
        }
        
        response = requests.patch(url, json=patch_ops, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return f"SUCCESS: Work item {work_item_id} updated"
        else:
            return f"ERROR: {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def list_repositories() -> str:
    """List all repositories in the Azure DevOps project.
    
    Returns:
        JSON list of repositories with id, name, url
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured"
    
    try:
        import base64
        import requests
        
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/repositories?api-version=7.0"
        
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            repos = [{"id": r["id"], "name": r["name"], "url": r["webUrl"]} for r in data.get("value", [])]
            return json.dumps(repos, indent=2)
        else:
            return f"ERROR: {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def get_pipeline_runs(repo_id: str = "") -> str:
    """Get recent pipeline runs (builds).
    
    Args:
        repo_id: Optional repository ID to filter
    
    Returns:
        JSON list of recent pipeline runs
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured"
    
    try:
        import base64
        import requests
        
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/builds?api-version=7.0&$top=10"
        if repo_id:
            url += f"&repositoryId={repo_id}"
        
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            builds = [{"id": b["id"], "status": b["status"], "result": b.get("result", ""), "sourceVersion": b.get("sourceVersion", "")} for b in data.get("value", [])]
            return json.dumps(builds, indent=2)
        else:
            return f"ERROR: {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def get_pull_requests(repo_id: str = "", status: str = "active") -> str:
    """Get pull requests for a repository.
    
    Args:
        repo_id: Repository ID (optional)
        status: Filter status (active, completed, abandoned, all)
    
    Returns:
        JSON list of pull requests
    """
    if not all([ORG, PROJECT, PAT]):
        return "ERROR: Azure DevOps credentials not configured"
    
    try:
        import base64
        import requests
        
        url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git"
        
        if repo_id:
            url += f"/repositories/{repo_id}"
        
        url += f"/pullrequests?api-version=7.0&searchCriteria.status={status}"
        
        auth = base64.b64encode(f":{PAT}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prs = [{"id": pr["pullRequestId"], "title": pr["title"], "status": pr["status"], "createdBy": pr["createdBy"]["displayName"]} for pr in data.get("value", [])]
            return json.dumps(prs, indent=2)
        else:
            return f"ERROR: {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"ERROR: {e}"


if __name__ == "__main__":
    mcp.run()
