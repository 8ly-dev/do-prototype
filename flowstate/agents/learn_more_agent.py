"""
This module contains the LearnMoreAgent class for providing information about the application.
"""

from itertools import chain
from pathlib import Path

from starlette.websockets import WebSocket

from flowstate.agents.base_agent import Agent
from flowstate.db_models import User


class LearnMoreAgent(Agent):
    """You don't have a name, you are an authoritative representative of our company, 8ly, our first app, Flowstate, and
    me, Zech, the founder.

    Your purpose is to communicate the goals and values of 8ly and the value of Flowstate to investors and potential
    co-founders. You're also tasked with discussing the prototype's codebase with the goal of demonstrating the
    feasibility of the project using existing technologies and putting the user at ease that we understand what to do.
    Make your messages as clear and scannable as possible. Review the project's README file before addressing
    questions about the codebase.

    Use tools to look up all relevant documents to help you answer any questions the user may have. If the user asks
    technical questions about how the Flowstate prototype functions, you can look through the relevant code files.
    These documents are your understanding, don't refer to them as documents.

    BE AWARE:
    The code is solely intended for demonstration purposes. It is not intended for production use. The actual finished
    version of Flowstate is not yet created. The code you have access to is ONLY for the prototype and IS NOT
    representative of the actual version that is coming. When discussing the prototype's code, focus on the
    technologies and the patterns used.

    Guidelines:
    - Never refer to yourself as an AI, agent, or assistant.
    - Don't talk about Flowstate as an app, use the name Flowstate instead.
    - Respond and act in a way that feels intuitive, supportive, and innately human.
    - When the user goes off-topic, redirect them back to discuss Flowstate and 8ly.
    - Don't overuse the user's name, it's ok occasionally.
    - Don't refer to yourself or the company in the first person.
    - If the documents don't have a clear answer for the user's question, offer a generic answer with a probable
    expectation.
    - When sharing links, use markdown link formatting.

    ALWAYS surface information relevant to the user's question to avoid the need for followup questions.
    ALWAYS validate technical answers against the codebase.

    Whatever you do: NEVER EVER make anything up. All necessary information is available in the documents."""
    def __init__(self, user: User | None, chat: WebSocket):
        """
        Initialize the LearnMoreAgent with user information and WebSocket connection.

        Args:
            user: Optional user information
            chat: WebSocket connection for sending messages to the client
        """
        root = Path(__file__).parent.parent.parent
        readme_path = root / "README.md"
        with readme_path.open("r") as f:
            self.readme = f.read()

        if user:
            self.system_prompt += (
                f"\n\nThe user is currently logged in as {user.username}. Use the user's name from "
                f"time to time, as is appropriate.\n\n"
            )

        self._chat = chat
        self._file_cache = {}
        self._path_cache = []
        self._root = Path(__file__).parent.parent.parent
        super().__init__()

    async def create_github_link(self, file_path: str) -> str:
        """Creates a link to the file on GitHub."""
        return f"https://github.com/8ly-dev/flowstate-prototype/blob/main/{file_path}"

    async def list_files(self) -> list[str]:
        """Activate this tool whenever you need to know what documents are available to you to answer the user's
        questions."""
        await self._chat.send_json({"type": "using", "tool_message": "Listing files"})
        files = self._find_files()
        print("LISTING FILES", files)
        return files

    async def read_file(self, file_path: str):
        """Activate this tool whenever you need to read a document. Use the file path to locate the file. If the file
        doesn't exist, you'll get an error message back."""
        print(f"READING: {file_path}")
        await self._chat.send_json({"type": "using", "tool_message": f"Reading {file_path.split('/')[-1]}"})
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        if file_path not in self._find_files():
            print("- Access denied: File not found.")
            return f"Access denied: File {file_path} not found."

        print(f"- {str(self._root)}/{file_path}")
        with open(f"{str(self._root)}/{file_path}", "r") as f:
            file = f.read()

        self._file_cache[file_path] = file
        print(f"- '{file[:20]}...")
        return file

    def _find_files(self, path: Path | None = None) -> list[str]:
        """
        Find all files in the project directory.

        This method recursively searches for files in the project directory,
        excluding hidden files and directories.

        Args:
            path: Optional path to search in, defaults to the project root

        Returns:
            A list of file paths relative to the project root
        """
        if not path and self._path_cache:
            return self._path_cache

        _path = path or self._root
        if _path.name.startswith("."):
            return []

        if _path.is_file():
            return [str(_path).lower().replace(str(self._root).lower(), "").lstrip("/")]

        files = list(chain(*(self._find_files(child) for child in _path.iterdir())))
        if not path:
            self._path_cache = files

        return files