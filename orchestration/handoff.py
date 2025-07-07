# Handoff Orchestration Example
# https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff?pivots=programming-language-python

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.functions import kernel_function
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import OrchestrationHandoffs
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.agents import HandoffOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime

load_dotenv(override=True)

service = AzureChatCompletion(
	deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
	endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
	api_key=os.getenv("AZURE_OPENAI_API_KEY"),
	api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
	service_id="azure_gpt4"
)

class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """Check the status of an order."""
        # Simulate checking the order status
        return f"Order {order_id} is shipped and will arrive in 2-3 days."

class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process a refund for an order."""
        # Simulate processing a refund
        print(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."

class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """Process a return for an order."""
        # Simulate processing a return
        print(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."

support_agent = ChatCompletionAgent(
    name="TriageAgent",
    description="A customer support agent that triages issues.",
    instructions="Handle customer requests.",
    service=service,
)

refund_agent = ChatCompletionAgent(
    name="RefundAgent",
    description="A customer support agent that handles refunds.",
    instructions="Handle refund requests.",
    service=service,
    plugins=[OrderRefundPlugin()],
)

order_status_agent = ChatCompletionAgent(
    name="OrderStatusAgent",
    description="A customer support agent that checks order status.",
    instructions="Handle order status requests.",
    service=service,
    plugins=[OrderStatusPlugin()],
)

order_return_agent = ChatCompletionAgent(
    name="OrderReturnAgent",
    description="A customer support agent that handles order returns.",
    instructions="Handle order return requests.",
    service=service,
    plugins=[OrderReturnPlugin()],
)

handoffs = (
    OrchestrationHandoffs()
    .add_many(    # Use add_many to add multiple handoffs to the same source agent at once
        source_agent=support_agent.name,
        target_agents={
            refund_agent.name: "Transfer to this agent if the issue is refund related",
            order_status_agent.name: "Transfer to this agent if the issue is order status related",
            order_return_agent.name: "Transfer to this agent if the issue is order return related",
        },
    )
    .add(    # Use add to add a single handoff
        source_agent=refund_agent.name,
        target_agent=support_agent.name,
        description="Transfer to this agent if the issue is not refund related",
    )
    .add(
        source_agent=order_status_agent.name,
        target_agent=support_agent.name,
        description="Transfer to this agent if the issue is not order status related",
    )
    .add(
        source_agent=order_return_agent.name,
        target_agent=support_agent.name,
        description="Transfer to this agent if the issue is not order return related",
    )
)

def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"{message.name}: {message.content}")
    
def human_response_function() -> ChatMessageContent:
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)

handoff_orchestration = HandoffOrchestration(
    members=[
        support_agent,
        refund_agent,
        order_status_agent,
        order_return_agent,
    ],
    handoffs=handoffs,
    agent_response_callback=agent_response_callback,
    human_response_function=human_response_function,
)

async def main():
	print("Handoff Orchestration Example")
	print("=" * 50)
	print("Customer support agent triaging issues\n")

	# Start the runtime
	runtime = InProcessRuntime()
	runtime.start()

	orchestration_result = await handoff_orchestration.invoke(
		task="A customer is on the line.",
		runtime=runtime,
	)

	value = await orchestration_result.get()
	print(value)

	await runtime.stop_when_idle()

if __name__ == "__main__":
	asyncio.run(main())	