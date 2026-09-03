from strands import Agent, tool


@tool
def get_delivery_status(order_id: str) -> str:
    """Look up the current delivery status for an order.

    Args:
        order_id: The customer's order ID.
    """
    deliveries = {
        "ORD-1001": "In transit — expected delivery tomorrow.",
        "ORD-1002": "Delivered — signed for at 14:32.",
        "ORD-1003": "Delayed — expected delivery in 2 days.",
    }

    return deliveries.get(
        order_id,
        f"No delivery information found for order {order_id}."
    )


agent = Agent(
    model="us.anthropic.claude-sonnet-4-6",
    tools=[get_delivery_status],
)

response = agent(
    "What is the status of order ORD-1003? "
    )

print(response)