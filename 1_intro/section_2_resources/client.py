"""Section 2 client: Resources."""

import asyncio
import json
import os
import sys

from pydantic import AnyUrl

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_here = os.path.dirname(os.path.abspath(__file__))
_venv_root = os.path.dirname(os.path.dirname(_here))
_python = os.path.join(
    _venv_root, ".venv",
    "Scripts" if sys.platform == "win32" else "bin",
    "python.exe" if sys.platform == "win32" else "python",
)
server_params = StdioServerParameters(
    command=_python,
    args=[os.path.join(_here, "server.py")],
)


async def run():
    # --- TRANSPORT: uncomment one line ---
    # STDIO — server launched as subprocess, run client only:
    async with stdio_client(server_params) as (read, write):
    # ↕ TOGGLE
    # async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List static resources (fixed URIs, no parameters)
            print("\n" + "=" * 50)
            print("INVOCATION 1: list_resources")
            print("=" * 50)
            resources = await session.list_resources()
            print(json.dumps(resources.model_dump(), indent=2, default=str))
            print("-" * 50)
            uris = []
            for r in resources.resources:
                uris.append(str(r.uri))
            print(f"[static resources] available URIs: {uris}")

            # Read the static conversions resource
            print("\n" + "=" * 50)
            print("INVOCATION 2: read_resource (static) kitchen://conversions")
            print("=" * 50)
            conversions = await session.read_resource(AnyUrl("kitchen://conversions"))
            print(f"[raw result] {conversions}")
            print("-" * 50)
            texts = []
            for content_block in conversions.contents:
                if isinstance(content_block, types.TextResourceContents):
                    texts.append(content_block.text)
            print(f"[static resource] {texts[0] if len(texts) == 1 else texts}")

            # List resource templates (URI templates with parameters)
            print("\n" + "=" * 50)
            print("INVOCATION 3: list_resource_templates")
            print("=" * 50)
            templates = await session.list_resource_templates()
            print(json.dumps(templates.model_dump(), indent=2, default=str))
            print("-" * 50)
            template_uris = []
            for t in templates.resourceTemplates:
                template_uris.append(t.uriTemplate)
            print(f"[resource templates] available templates: {template_uris}")

            # Read the dynamic recipe resource — URI template resolved to recipe://pancakes
            print("\n" + "=" * 50)
            print("INVOCATION 4: read_resource (dynamic) recipe://pancakes")
            print("=" * 50)
            resource_content = await session.read_resource(AnyUrl("recipe://pancakes"))
            print(f"[raw result] {resource_content}")
            print("-" * 50)
            texts = []
            for content_block in resource_content.contents:
                if isinstance(content_block, types.TextResourceContents):
                    texts.append(content_block.text)
            print(f"[dynamic resource] {texts[0] if len(texts) == 1 else texts}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
