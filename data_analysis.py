import discord
import threading
import time
import asyncio
import os
import getpass
# import openrouter
import openrouter.chat

from daytona import Daytona, DaytonaConfig
import os
import getpass
from langchain_daytona import DaytonaSandbox

# Openrouter validation bypass patch code
original_send = openrouter.chat.Chat.send

def fix_openrouter_payload(data):
    if isinstance(data, list):
        return [fix_openrouter_payload(item) for item in data]
    elif isinstance(data, dict):
        if data.get("type") == "image":
            base64_data = data.get("base64")
            mime_type = data.get("mime_type", "image/png")
            if base64_data:
                return {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_data}"
                    }
                }
        return {k: fix_openrouter_payload(v) for k, v in data.items()}
    return data

def patched_send(self, messages, *args, **kwargs):
    fixed_messages = fix_openrouter_payload(messages)
    return original_send(self, messages=fixed_messages, *args, **kwargs)

openrouter.chat.Chat.send = patched_send



if not os.getenv("DISC_TOKEN"):
    os.environ["DISC_TOKEN"] = getpass.getpass("Enter your discord bot token: ")

bot_token = os.environ["DISC_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
CHANNEL_ID = 1511902321427091558

def independent_llm_agent(discord_loop):
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
            asyncio.run_coroutine_threadsafe(
                send_discord_message(text,"text"), discord_loop
            )
        else:
            # return
            # asyncio.run_coroutine_threadsafe(
            #     send_discord_message(text,"text"), discord_loop
            # )
            print(text)
            print(file_path)
            asyncio.run_coroutine_threadsafe(
                send_discord_message(text,"text"), discord_loop
            )
            asyncio.run_coroutine_threadsafe(
                send_discord_message(file_path,"file"), discord_loop
            )
    
        return "Message sent."

        # asyncio.run_coroutine_threadsafe(
        #     send_discord_message(agent_response), discord_loop
        # )
  
    from langchain_core.utils.uuid import uuid7
    
    from langgraph.checkpoint.memory import InMemorySaver
    from deepagents import create_deep_agent
    
    
    if not os.getenv("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = getpass.getpass("Enter your OpenRouter API key: ")
    
    checkpointer = InMemorySaver()
    
    from langchain_openrouter import ChatOpenRouter
    
    
    agent = create_deep_agent(
        model="openrouter:deepseek-v4-flash",
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
    
    input_message = {
        "role": "user",
        "content": (
            "Analyze /home/daytona/data/sales_data.csv in the current dir and generate a beautiful plot. When finished, send your analysis to discord using the tool send_message."
        ),
    }
    
    
    
    
    
    print(type(agent.stream))
    for step in agent.stream(
        {"messages": [input_message]},
        config=config,
        stream_mode="updates"
    ):
        for _, update in step.items():
            if update and (messages := update.get("messages")) and isinstance(messages, list):
                for message in messages:
                    message.pretty_print()



async def send_discord_message(text,type):
    channel = client.get_channel(CHANNEL_ID)
    if type=='text':
        # slack_client.chat_postMessage(channel=channel, text=text)
        # print(text)
        if channel:
            print("text is sent")
            await channel.send(text)
        else:
            print("Invalid Channel")
    else:
        print("file "+text+ " is sent")
        # response = backend.download_files([text])
        # if response.error:
        #   await channel.send(f"Failed to download image: {response.error}")
        #   return
        # image_stream = io.BytesIO(response.content)
        # discord_file = discord.File(fp=image_stream, filename="downloaded_image.png")
        _, _, after = text.rpartition('/')
        if channel:
            # print(type(discord_file))
            await channel.send(file=discord.File(after))
        else:
            print("Invalid Channel")
    return "successful discord sent"

@client.event
async def on_ready():
    print("Discord client ready. Starting autonomous LLM thread...")
    # Pass Discord's event loop to the thread
    threading.Thread(target=independent_llm_agent, args=(client.loop,), daemon=True).start()

client.run(bot_token)