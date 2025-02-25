from configparser import ConfigParser
from aiohttp import ClientSession
from typing import Optional, Tuple

__all__: Tuple[str, ...] = (
    "find_app_by_name",
    "read_discloud_app_name",
    "read_app_logs",
)


async def find_app_by_name(name: str, api_token: str) -> Optional[str]:

    async with ClientSession() as session:
        async with session.get(
            "https://api.discloud.app/v2/app/all", headers={"api-token": api_token}
        ) as resp:
            json_resp = await resp.json()
            app_id = next(
                (app["id"] for app in json_resp["apps"] if app["name"] == name),
                None,
            )
            if app_id is None:
                return None

            return app_id
        
def read_discloud_app_name() -> str:
    with open("discloud.config", "r") as fp:
        content = f"[MAIN]\n{fp.read()}"

    config = ConfigParser()
    config.read_string(content)
    return config.get("MAIN", {}).get("NAME", None)

async def read_app_logs(app_id: str, api_token: str): 
    async with ClientSession() as session:
        async with session.get(
            f"https://api.discloud.app/v2/app/{app_id}/logs", headers={"api-token": api_token}
        ) as resp:
            json_resp = await resp.json()
            big_logs = json_resp.get("apps", {}).get("terminal", {}).get("big", "")
            return big_logs
