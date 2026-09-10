from unittest.mock import MagicMock, patch

from src.state.dynamodb_session_repository import DynamoDBSessionRepository
from strands.types.session import SessionMessage


@patch("src.state.dynamodb_session_repository.boto3.resource")
def test_list_messages_handles_default_offset(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table
    table.query.return_value = {"Items": []}

    repository = DynamoDBSessionRepository()

    assert repository.list_messages("session-1", "RecoveryAgent") == []


@patch("src.state.dynamodb_session_repository.boto3.resource")
def test_create_message_accepts_non_integer_message_id(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table
    repository = DynamoDBSessionRepository()
    message = SessionMessage(
        message={"role": "assistant", "content": []},
        message_id="message-id",
    )

    repository.create_message("session-1", "RecoveryAgent", message)

    assert table.put_item.call_args.kwargs["Item"]["sk"] == (
        "MESSAGE#RecoveryAgent#message-id"
    )