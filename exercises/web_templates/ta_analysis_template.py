from daytona import Daytona, DaytonaConfig
import os
import getpass
from langchain_daytona import DaytonaSandbox

if not os.getenv("DAYTONA_KEY"):
    os.environ["DAYTONA_KEY"] = getpass.getpass("Enter your sandbox token: ")

config = DaytonaConfig(api_key=os.environ["DAYTONA_KEY"]) # Replace with your API key

# Initialize the Daytona client
daytona = Daytona(config)

sandbox = daytona.create()
backend = DaytonaSandbox(sandbox=sandbox)

result = backend.execute("echo ready")
print(result)
# ExecuteResponse(output='ready', exit_code=0, ...)

import csv
import io

# Create sample sales data
data = [
    ["Date", "Product", "Units Sold", "Revenue"],
    ["2025-08-01", "Widget A", 10, 250],
    ["2025-08-02", "Widget B", 5, 125],
    ["2025-08-03", "Widget A", 7, 175],
    ["2025-08-04", "Widget C", 3, 90],
    ["2025-08-05", "Widget B", 8, 200],
]

# Convert to CSV bytes
text_buf = io.StringIO()
writer = csv.writer(text_buf)
writer.writerows(data)
csv_bytes = text_buf.getvalue().encode("utf-8")
text_buf.close()

# Upload to backend
backend.upload_files([("/home/daytona/data/sales_data.csv", csv_bytes)])

from langchain.tools import tool
# from slack_sdk import WebClient

# if not os.getenv("SLACK_USER_TOKEN"):
#     os.environ["SLACK_USER_TOKEN"] = getpass.getpass("Enter your slack token: ")

# slack_token = os.environ["SLACK_USER_TOKEN"]
# slack_client = WebClient(token=slack_token)


@tool(parse_docstring=True)
def send_message(text: str, file_path: str | None = None) -> str:
    """Send message, optionally including attachments such as images.

    Args:
        text: (str) text content of the message
        file_path: (str) file path of attachment in the filesystem.
    """
    if not file_path:
        # slack_client.chat_postMessage(channel=channel, text=text)
        print(text)
    # else:
    #     fp = backend.download_files([file_path])
    #     slack_client.files_upload_v2(
    #         channel="C0123456ABC",  # specify your own channel here
    #         content=fp[0].content,
    #         initial_comment=text,
    #     )

    return "Message sent."

from langchain_core.utils.uuid import uuid7

from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent


if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = getpass.getpass("Enter your model token: ")

checkpointer = InMemorySaver()

agent = create_deep_agent(
    model="huggingface:microsoft/Phi-3-mini-4k-instruct",
    tools=[send_message],
    backend=backend,
    system_prompt="You are a data analyst.",
    checkpointer=checkpointer,
)

thread_id = str(uuid7())
config={"configurable": {"thread_id": thread_id}}

from langchain_core.messages import HumanMessage

# input_message = HumanMessage(
#     content=("Analyze ./data/sales_data.csv in the current dir and generate a beautiful plot. "
#             "When finished, print your analysis using the tool."
#             )
# )

# print(f"Content type: {type(input_message.content)}")  # Should be <class 'str'>
# print(f"Content: {input_message.content}")

# input_message = {
#     "role": "user",
#     "content": (
#         "Analyze ./data/sales_data.csv in the current dir and generate a beautiful plot. When finished, print your analysis using the tool."
#     ),
# }





# print(type(agent.stream))
# for step in agent.stream(
#     {"messages": [{"role": "user", "content": "Analyze ./data/sales_data.csv in the current dir and generate a beautiful plot. When finished, print your analysis using the tool."}]},
#     config=config,
#     stream_mode="updates"
# ):
#     for _, update in step.items():
#         if update and (messages := update.get("messages")) and isinstance(messages, list):
#             for message in messages:
#                 message.pretty_print()




for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze ./data/sales_data.csv in the current dir and generate a beautiful plot. When finished, print your analysis using the tool."}]},
    config=config,
    stream_mode="updates",
    version="v2",
):
    if chunk["type"] == "updates":
        for step, data in chunk["data"].items():
            print(f"step: {step}")
            # print(f"content: {data['messages'][-1].content_blocks}")
