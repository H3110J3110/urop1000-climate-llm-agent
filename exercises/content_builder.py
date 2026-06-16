
from pathlib import Path
import os
import sys
import yaml
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.messages import HumanMessage
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

load_dotenv()
EXAMPLE_DIR = Path(__file__).parent

@tool
def web_search(query: str, max_results: int = 3, topic: str = "general") -> dict:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY not set"}
    from tavily import TavilyClient
    return TavilyClient(api_key=api_key).search(query, max_results=max_results, topic=topic)

@tool
def generate_cover(prompt: str, slug: str) -> str:
    from google import genai
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt]
    )
    output_path = EXAMPLE_DIR / "blogs" / slug / "hero.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response.parts[0].as_image().save(output_path)
    return f"Image saved to {output_path}"

@tool
def generate_social_image(prompt: str, platform: str, slug: str) -> str:
    from google import genai
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt]
    )
    output_path = EXAMPLE_DIR / platform / slug / "image.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response.parts[0].as_image().save(output_path)
    return f"Image saved to {output_path}"

def load_subagents(config_path: Path) -> list:
    available_tools = {"web_search": web_search}
    with open(config_path) as f:
        config = yaml.safe_load(f)
    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        if "model" in spec:
            subagent["model"] = spec["model"]
        if "tools" in spec:
            subagent["tools"] = [available_tools[t] for t in spec["tools"]]
        subagents.append(subagent)
    return subagents

def create_content_writer():
    return create_deep_agent(
        model="deepseek-v4-flash",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )

if __name__ == "__main__":
    task = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "Write a blog post about how AI agents are transforming software development"
    )
    agent = create_content_writer()
    result = agent.invoke(
        {"messages": [HumanMessage(content=task)]},
        config={"configurable": {"thread_id": "content-builder-demo"}}
    )
    for msg in result.get("messages", []):
        if hasattr(msg, "content") and msg.content:
            print(msg.content)
