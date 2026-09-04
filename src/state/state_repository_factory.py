import os

from .dynamodb_state_repository import (
    DynamoDBStateRepository,
)
from .in_memory_state_repository import (
    InMemoryStateRepository,
)
from .state_repository import StateRepository


def create_state_repository() -> StateRepository:
    repository_type = os.getenv(
        "STATE_REPOSITORY",
        "in_memory",
    ).lower()

    if repository_type == "in_memory":
        return InMemoryStateRepository()

    if repository_type == "dynamodb":
        table_name = os.getenv(
            "DYNAMODB_TABLE_NAME",
            "agents-for-humans-state",
        )

        region_name = os.getenv(
            "AWS_REGION",
            "us-east-1",
        )

        return DynamoDBStateRepository(
            table_name=table_name,
            region_name=region_name,
        )

    raise ValueError(
        "Unsupported STATE_REPOSITORY: "
        f"{repository_type}. "
        "Expected 'in_memory' or 'dynamodb'."
    )