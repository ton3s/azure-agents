# Group Chat Orchestration Example
# https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.agents import GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.agents.runtime import InProcessRuntime

# Load environment variables
load_dotenv()

azure_chat_completion = AzureChatCompletion(
	deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
	endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
	api_key=os.getenv("AZURE_OPENAI_API_KEY"),
	api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
	service_id="azure_gpt4"
)

kernel = Kernel()
kernel.add_service(azure_chat_completion)

def get_agents() -> list[Agent]:
    writer = ChatCompletionAgent(
        name="Writer",
        description="A content writer.",
        instructions=(
            "You are an excellent content writer. You create new content and edit contents based on the feedback."
        ),
        kernel=kernel,
    )
    reviewer = ChatCompletionAgent(
        name="Reviewer",
        description="A content reviewer.",
        instructions=(
            "You are an excellent content reviewer. You review the content and provide feedback to the writer."
        ),
        kernel=kernel,
    )
    return [writer, reviewer]

def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"**{message.name}**\n{message.content}")
    

agents = get_agents()
group_chat_orchestration = GroupChatOrchestration(
    members=agents,
    manager=RoundRobinGroupChatManager(max_rounds=5),  # Odd number so writer gets the last word
    agent_response_callback=agent_response_callback,
)

async def main():
	print("Group Chat Orchestration Example")
	print("=" * 50)
	print("Writer and Reviewer discussing a new content piece\n")

	runtime = InProcessRuntime()
	runtime.start()

	orchestration_result = await group_chat_orchestration.invoke(
		task="Create a slogan for a new electric SUV that is affordable and fun to drive.",
		runtime=runtime,
	)

	value = await orchestration_result.get()
	print(f"***** Final Result *****\n{value}")

	await runtime.stop_when_idle()
     
if __name__ == "__main__":
	asyncio.run(main())	