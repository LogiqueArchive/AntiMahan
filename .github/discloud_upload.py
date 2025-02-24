import logging
from asyncio import run
from pathlib import Path
from sys import exit as sys_exit
from typing import Any, Dict, Optional
from configparser import ConfigParser
from uuid import uuid4
from datetime import datetime as dt
import shutil

import os
import discloud
from aiohttp import ClientSession

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

API_TOKEN = os.environ.get("API_TOKEN")

if not API_TOKEN:
    raise ValueError("API_TOKEN not found in environment variables.")

client = discloud.Client(API_TOKEN)



async def find_app_by_name(name: str) -> Optional[discloud.discloud.Application]:

    async with ClientSession() as session:
        async with session.get(
            "https://api.discloud.app/v2/app/all", headers={"api-token": API_TOKEN}
        ) as resp:
            json_resp = await resp.json()
            app_id = next(
                (app["id"] for app in json_resp["apps"] if app["name"] == name),
                None,
            )
            if app_id is None:
                return None

            app_object = await client.app_info(app_id)
            
            setattr(app_object, "name", name)
            setattr(app_object, "app_id", app_id)
            return app_object

async def upload_app(zipfile_path: Path, app_id: Optional[str]) -> discloud.discloud.Action:
    
    discloud_file: discloud.File = discloud.File(zipfile_path.__fspath__())

    if app_id is not None:
        return await client.commit(app_id, discloud_file)
    
    return await client.upload_app(discloud_file)

def read_discloud_config(filepath: Path) -> ConfigParser:
    with open(filepath, "r") as fp:
        content = f"[MAIN]\n{fp.read()}"
    
    config = ConfigParser()
    config.read_string(content)
    return config

def generate_zip_archive(source_path: Path, config_path: Path) -> Path:
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S_%f")
    unique_id = uuid4().hex
    workdir_name = f"dsc_archive_{timestamp}_{unique_id}"
    os.makedirs(workdir_name)
    workdir_path = Path(workdir_name)
    logger.info("Copying files to %s", workdir_name)
    for file in source_path.glob("*"):
        logger.info("Copied %s -> %s", file, workdir_path)
        shutil.copy2(file, workdir_path)
    
    shutil.copy2(config_path, workdir_path)
    logger.info("Copied config file -> %s", workdir_path)

    shutil.make_archive(workdir_name, "zip", workdir_path)

    os.remove(workdir_path)
    return Path(f"{workdir_name}.zip")
    


async def main():

    level: str = os.environ.get("LOG_LEVEL", "INFO")
    logger.setLevel(level)

    try:
        user = await client.user_info()
        async with ClientSession() as session:
            async with session.get(
                "https://api.discloud.app/v2/user", headers={"api-token": API_TOKEN}
            ) as resp:
                user_json_resp = await resp.json()

    except discloud.InvalidToken:
        logger.error("Failed to fetch user data, user token is fucked")
        sys_exit(1)

    logger.info("Total apps: %d", len(user_json_resp.get("user", {}).get("apps", [])))
    logger.info("Plan: %s", user.plan)
    logger.info("Used RAM: %d/%d", user.total_ram, user.using_ram)

    config_file_path: Path = Path(os.environ.get("CONFIG_PATH", "./discloud.config"))
    config = read_discloud_config(config_file_path)
    app_name: str = config["MAIN"]["NAME"]

    source_path: Path = Path(os.environ.get("SOURCE_PATH", "."))
    logger.debug("Source path: %s", source_path.__fspath__())
    zipfile_path = generate_zip_archive(source_path, config_file_path)
    logger.info("Finding app: %s", app_name)
    app = await find_app_by_name(app_name)
    app_id: Optional[str] = getattr(app, "app_id", None)
    if app:
        logger.info("App %s found with id: %s", app.name, app.app_id)    
        logger.info("Commiting files to app: %s", app.name)
        
    else:
        logger.info("App doesn't exists")
        logger.info("Uploading them to discloud")

    await upload_app(zipfile_path, app_id)


if __name__ == "__main__":
    run(main())
