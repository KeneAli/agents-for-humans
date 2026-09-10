from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from strands.session.session_repository import SessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage


class DynamoDBSessionRepository(SessionRepository):
    """DynamoDB-backed Strands session records, including interrupt state."""

    def __init__(
        self,
        table_name: str = "agents-for-humans-state",
        region_name: str = "us-east-1",
    ):
        self.table = boto3.resource(
            "dynamodb",
            region_name=region_name,
        ).Table(table_name)

    @staticmethod
    def _session_key(session_id: str, suffix: str) -> dict[str, str]:
        return {"pk": f"AGENT_SESSION#{session_id}", "sk": suffix}

    @staticmethod
    def _item(data: dict[str, Any], key: dict[str, str], entity_type: str) -> dict:
        return {**key, "entity_type": entity_type, "data": data}

    @staticmethod
    def _message_key(session_id: str, agent_id: str, message_id: Any) -> dict[str, str]:
        if isinstance(message_id, int) and not isinstance(message_id, bool):
            message_suffix = f"{message_id:012d}"
        else:
            message_suffix = str(message_id)
        return DynamoDBSessionRepository._session_key(
            session_id,
            f"MESSAGE#{agent_id}#{message_suffix}",
        )

    def create_session(self, session: Session, **kwargs: Any) -> Session:
        self.table.put_item(
            Item=self._item(
                session.to_dict(),
                self._session_key(session.session_id, "SESSION"),
                "AGENT_SESSION",
            )
        )
        return session

    def read_session(self, session_id: str, **kwargs: Any) -> Session | None:
        item = self.table.get_item(Key=self._session_key(session_id, "SESSION")).get("Item")
        return Session.from_dict(item["data"]) if item else None

    def create_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        self.table.put_item(
            Item=self._item(
                session_agent.to_dict(),
                self._session_key(session_id, f"AGENT#{session_agent.agent_id}"),
                "AGENT_SESSION_AGENT",
            )
        )

    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> SessionAgent | None:
        item = self.table.get_item(
            Key=self._session_key(session_id, f"AGENT#{agent_id}")
        ).get("Item")
        return SessionAgent.from_dict(item["data"]) if item else None

    def update_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        session_agent.updated_at = datetime.now(timezone.utc).isoformat()
        self.create_agent(session_id, session_agent, **kwargs)

    def create_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        self.table.put_item(
            Item=self._item(
                session_message.to_dict(),
                self._message_key(session_id, agent_id, session_message.message_id),
                "AGENT_SESSION_MESSAGE",
            )
        )

    def read_message(self, session_id: str, agent_id: str, message_id: Any, **kwargs: Any) -> SessionMessage | None:
        item = self.table.get_item(
            Key=self._message_key(session_id, agent_id, message_id)
        ).get("Item")
        return SessionMessage.from_dict(item["data"]) if item else None

    def update_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        self.create_message(session_id, agent_id, session_message, **kwargs)

    def list_messages(
        self,
        session_id: str,
        agent_id: str,
        limit: int | None = None,
        offset: int = 0,
        **kwargs: Any,
    ) -> list[SessionMessage]:
        response = self.table.query(
            KeyConditionExpression=(
                Key("pk").eq(f"AGENT_SESSION#{session_id}")
                & Key("sk").begins_with(f"MESSAGE#{agent_id}#")
            ),
            ScanIndexForward=True,
        )
        messages = [
            SessionMessage.from_dict(item["data"])
            for item in response.get("Items", [])
        ]
        start = offset if isinstance(offset, int) else 0
        if limit is None:
            return messages[start:]
        return messages[start : start + int(limit)]
