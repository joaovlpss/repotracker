import os
import git
import sqlite3
import tomllib
import json
from pydantic import BaseModel


class RepositoryManager(BaseModel):
    db_connection: sqlite3.Connection
    repository_list: list[git.Repo]

    def __init__(self):
        self.db_connection = self.get_connection()
        self.repository_list = self.load_tracked_repos()

    def get_connection(self) -> sqlite3.Connection:
        with open("./config.toml", "rb") as config:
            config = tomllib.load(config)

        db_path: str = config["database"]["locale"]
        return sqlite3.connect(db_path)

    def load_tracked_repos(self) -> list[git.Repo]:
        repos: list[git.Repo] = []

        # First, we open our JSON list.
        with open("./tracked_repos/tracked_repos.json") as dictionary:
            data = json.load(dictionary)

        for repo in data["repositories"]:
            repo_name = repo["name"]
            repo_url = repo["ssh_url"]
            repo_path = "./tracked_repos" + repo_name

            # If this repo isn't downloaded yet, we should download it.
            if repo_name not in os.listdir("./tracked_repos"):
                git.Repo.clone_from(repo_url, repo_path, branch="main")

            # We add the path to our repo to our list.
            repos.append(git.Repo(repo_path))

        # Finally, we return all our repos.
        return repos
