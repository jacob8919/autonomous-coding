#!/usr/bin/env python3
"""
MCP Server for Feature Management
==================================

Provides tools to manage features in the autonomous coding system,
replacing the previous FastAPI-based REST API.

Tools:
- feature_get_stats: Get progress statistics
- feature_get_next: Get next feature to implement
- feature_get_for_regression: Get random passing features for testing
- feature_mark_passing: Mark a feature as passing
- feature_skip: Skip a feature (move to end of queue)
- feature_create_bulk: Create multiple features at once
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from sqlalchemy.sql.expression import func

# Add parent directory to path so we can import from api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import Feature, create_database
from api.migration import migrate_json_to_sqlite, migrate_schema

# Configuration from environment
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", ".")).resolve()


# Pydantic models for input validation
class MarkPassingInput(BaseModel):
    """Input for marking a feature as passing."""
    feature_id: int = Field(..., description="The ID of the feature to mark as passing", ge=1)


class SkipFeatureInput(BaseModel):
    """Input for skipping a feature."""
    feature_id: int = Field(..., description="The ID of the feature to skip", ge=1)


class RegressionInput(BaseModel):
    """Input for getting regression features."""
    limit: int = Field(default=3, ge=1, le=10, description="Maximum number of passing features to return")


class FeatureCreateItem(BaseModel):
    """Schema for creating a single feature."""
    category: str = Field(..., min_length=1, max_length=100, description="Feature category")
    name: str = Field(..., min_length=1, max_length=255, description="Feature name")
    description: str = Field(..., min_length=1, description="Detailed description")
    steps: list[str] = Field(..., min_length=1, description="Implementation/test steps")


class BulkCreateInput(BaseModel):
    """Input for bulk creating features."""
    features: list[FeatureCreateItem] = Field(..., min_length=1, description="List of features to create")


# Global database session maker (initialized on startup)
_session_maker = None
_engine = None


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize database on startup, cleanup on shutdown."""
    global _session_maker, _engine

    # Create project directory if it doesn't exist
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize database
    _engine, _session_maker = create_database(PROJECT_DIR)

    # Run migrations if needed
    migrate_json_to_sqlite(PROJECT_DIR, _session_maker)  # Legacy JSON to SQLite
    migrate_schema(_session_maker)  # Add new columns to existing tables

    yield

    # Cleanup
    if _engine:
        _engine.dispose()


# Initialize the MCP server
mcp = FastMCP("features", lifespan=server_lifespan)


def get_session():
    """Get a new database session."""
    if _session_maker is None:
        raise RuntimeError("Database not initialized")
    return _session_maker()


@mcp.tool()
def feature_get_stats() -> str:
    """Get statistics about feature completion progress.

    Returns the number of passing features, total features, and completion percentage.
    Use this to track overall progress of the implementation.

    Returns:
        JSON with: passing (int), total (int), percentage (float)
    """
    session = get_session()
    try:
        total = session.query(Feature).count()
        passing = session.query(Feature).filter(Feature.passes == True).count()
        percentage = round((passing / total) * 100, 1) if total > 0 else 0.0

        return json.dumps({
            "passing": passing,
            "total": total,
            "percentage": percentage
        }, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_get_next() -> str:
    """Get the highest-priority pending feature to work on.

    Returns the feature with the lowest priority number that has passes=false.
    Use this at the start of each coding session to determine what to implement next.

    Returns:
        JSON with feature details (id, priority, category, name, description, steps, passes)
        or error message if all features are passing.
    """
    session = get_session()
    try:
        feature = (
            session.query(Feature)
            .filter(Feature.passes == False)
            .order_by(Feature.priority.asc(), Feature.id.asc())
            .first()
        )

        if feature is None:
            return json.dumps({"error": "All features are passing! No more work to do."})

        return json.dumps(feature.to_dict(), indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_get_for_regression(
    limit: Annotated[int, Field(default=3, ge=1, le=10, description="Maximum number of passing features to return")] = 3
) -> str:
    """Get random passing features for regression testing.

    Returns a random selection of features that are currently passing.
    Use this to verify that previously implemented features still work
    after making changes.

    Args:
        limit: Maximum number of features to return (1-10, default 3)

    Returns:
        JSON with: features (list of feature objects), count (int)
    """
    session = get_session()
    try:
        features = (
            session.query(Feature)
            .filter(Feature.passes == True)
            .order_by(func.random())
            .limit(limit)
            .all()
        )

        return json.dumps({
            "features": [f.to_dict() for f in features],
            "count": len(features)
        }, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_get_all_categories() -> str:
    """Get all unique feature categories currently in the database.

    Returns a list of category names to help maintain consistency
    when adding new features. Use this to understand what categories
    already exist before creating new features.

    Returns:
        JSON with: categories (list of strings), count (int)
    """
    session = get_session()
    try:
        categories = (
            session.query(Feature.category)
            .distinct()
            .order_by(Feature.category.asc())
            .all()
        )
        category_list = [c[0] for c in categories]

        return json.dumps({
            "categories": category_list,
            "count": len(category_list)
        }, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_get_summary() -> str:
    """Get a summary of all features grouped by category.

    Returns category counts and passing status to help understand
    existing coverage without loading all feature details.
    This is more context-efficient than loading all features.

    Returns:
        JSON with: categories (list of {name, total, passing}), overall (total, passing)
    """
    session = get_session()
    try:
        from sqlalchemy import case

        # Get counts by category
        category_stats = (
            session.query(
                Feature.category,
                func.count(Feature.id).label('total'),
                func.sum(case((Feature.passes == True, 1), else_=0)).label('passing')
            )
            .group_by(Feature.category)
            .order_by(Feature.category.asc())
            .all()
        )

        result = {
            "categories": [
                {
                    "name": cat,
                    "total": int(total),
                    "passing": int(passing)
                }
                for cat, total, passing in category_stats
            ],
            "overall": {
                "total": sum(r[1] for r in category_stats),
                "passing": sum(r[2] for r in category_stats)
            }
        }
        return json.dumps(result, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_search(
    query: Annotated[str, Field(description="Search query for feature names/descriptions")],
    limit: Annotated[int, Field(default=10, ge=1, le=50, description="Maximum results to return")] = 10
) -> str:
    """Search existing features by name or description.

    Helps check if a feature already exists before adding duplicates.
    Use this before creating new features to avoid redundancy.

    Args:
        query: Search term to match against feature names and descriptions
        limit: Maximum number of results to return (1-50, default 10)

    Returns:
        JSON with: features (list of {id, name, category, passes}), count (int)
    """
    session = get_session()
    try:
        features = (
            session.query(Feature)
            .filter(
                (Feature.name.ilike(f"%{query}%")) |
                (Feature.description.ilike(f"%{query}%"))
            )
            .order_by(Feature.priority.asc())
            .limit(limit)
            .all()
        )

        return json.dumps({
            "features": [
                {
                    "id": f.id,
                    "name": f.name,
                    "category": f.category,
                    "passes": f.passes
                }
                for f in features
            ],
            "count": len(features)
        }, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_mark_passing(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as passing", ge=1)]
) -> str:
    """Mark a feature as passing after successful implementation.

    Updates the feature's passes field to true. Use this after you have
    implemented the feature and verified it works correctly.

    Args:
        feature_id: The ID of the feature to mark as passing

    Returns:
        JSON with the updated feature details, or error if not found.
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()

        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        feature.passes = True
        session.commit()
        session.refresh(feature)

        return json.dumps(feature.to_dict(), indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_skip(
    feature_id: Annotated[int, Field(description="The ID of the feature to skip", ge=1)]
) -> str:
    """Skip a feature by moving it to the end of the priority queue.

    Use this when a feature cannot be implemented yet due to:
    - Dependencies on other features that aren't implemented yet
    - External blockers (missing assets, unclear requirements)
    - Technical prerequisites that need to be addressed first

    The feature's priority is set to max_priority + 1, so it will be
    worked on after all other pending features.

    Args:
        feature_id: The ID of the feature to skip

    Returns:
        JSON with skip details: id, name, old_priority, new_priority, message
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()

        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        if feature.passes:
            return json.dumps({"error": "Cannot skip a feature that is already passing"})

        old_priority = feature.priority

        # Get max priority and set this feature to max + 1
        max_priority_result = session.query(Feature.priority).order_by(Feature.priority.desc()).first()
        new_priority = (max_priority_result[0] + 1) if max_priority_result else 1

        feature.priority = new_priority
        session.commit()
        session.refresh(feature)

        return json.dumps({
            "id": feature.id,
            "name": feature.name,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "message": f"Feature '{feature.name}' moved to end of queue"
        }, indent=2)
    finally:
        session.close()


@mcp.tool()
def feature_create_bulk(
    features: Annotated[list[dict], Field(description="List of features to create, each with category, name, description, and steps")],
    priority_mode: Annotated[str, Field(default="append", description="Priority mode: 'append' (after existing) or 'prepend' (before pending)")] = "append",
    source: Annotated[str, Field(default="initializer", description="Source of features: 'initializer' or 'enhancement'")] = "initializer",
    batch_id: Annotated[str, Field(default=None, description="Optional UUID to group features added together")] = None
) -> str:
    """Create multiple features in a single operation.

    Features are assigned sequential priorities based on their order and priority_mode.
    All features start with passes=false.

    This is used by the initializer agent to set up the initial feature list,
    and by the enhancement agent to add new features to existing projects.

    Args:
        features: List of features to create, each with:
            - category (str): Feature category
            - name (str): Feature name
            - description (str): Detailed description
            - steps (list[str]): Implementation/test steps
        priority_mode: How to assign priorities:
            - "append": New features get lowest priority (worked on last)
            - "prepend": New features get highest priority (worked on first)
        source: Where features came from ("initializer" or "enhancement")
        batch_id: Optional UUID to group features that were added together

    Returns:
        JSON with: created (int), priority_mode (str), start_priority (int)
    """
    session = get_session()
    try:
        # Calculate starting priority based on mode
        if priority_mode == "prepend":
            # Get minimum priority of pending (non-passing) features
            min_pending = (
                session.query(Feature.priority)
                .filter(Feature.passes == False)
                .order_by(Feature.priority.asc())
                .first()
            )
            if min_pending:
                # Start before the first pending feature
                start_priority = min_pending[0] - len(features)
            else:
                # No pending features, use normal append logic
                max_priority_result = session.query(Feature.priority).order_by(Feature.priority.desc()).first()
                start_priority = (max_priority_result[0] + 1) if max_priority_result else 1
        else:
            # Append mode: add after all existing features
            max_priority_result = session.query(Feature.priority).order_by(Feature.priority.desc()).first()
            start_priority = (max_priority_result[0] + 1) if max_priority_result else 1

        created_count = 0
        for i, feature_data in enumerate(features):
            # Validate required fields
            if not all(key in feature_data for key in ["category", "name", "description", "steps"]):
                return json.dumps({
                    "error": f"Feature at index {i} missing required fields (category, name, description, steps)"
                })

            db_feature = Feature(
                priority=start_priority + i,
                category=feature_data["category"],
                name=feature_data["name"],
                description=feature_data["description"],
                steps=feature_data["steps"],
                passes=False,
                source=source,
                batch_id=batch_id,
            )
            session.add(db_feature)
            created_count += 1

        session.commit()

        return json.dumps({
            "created": created_count,
            "priority_mode": priority_mode,
            "start_priority": start_priority,
            "source": source,
            "batch_id": batch_id
        }, indent=2)
    except Exception as e:
        session.rollback()
        return json.dumps({"error": str(e)})
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run()
