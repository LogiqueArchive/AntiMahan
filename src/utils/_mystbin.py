from typing import Any, Dict, List, Optional
from aiohttp import ClientResponseError, ClientSession
import logging

logger = logging.getLogger(__name__)



async def paste_files(
    files_dict: List[Dict[str, str]], password: Optional[str] = None
) -> str:
    """
    Upload files to Mystbin and return the URL of the paste.

    Args:
        files_dict (List[Dict[str, str]]): A list of dictionaries with 'filename' & 'content' keys.
        password (Optional[str]): An optional password for the paste.

    Returns:
        str: The URL of the created paste.
    """
    if len(files_dict) > 5:
        merged_content = "\n\n".join(
            f"--- {file['filename']} ---\n{file['content']}" for file in files_dict[4:]
        )
        files_dict = files_dict[:4] + [{"filename": "merged_files.txt", "content": merged_content}]

    paste_contents: Dict[str, Any] = {"files": files_dict}
    if password is not None:
        paste_contents["password"] = password

    async with ClientSession() as session:
        async with session.post("https://mystb.in/api/paste", json=paste_contents) as resp:
            if resp.status == 200:
                paste_id: str = (await resp.json())["id"]
                return f"https://mystb.in/{paste_id}"

            raise ClientResponseError(
                resp.request_info, resp.history, status=resp.status, message=(await resp.text())
            )