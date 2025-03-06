import os
import tomllib
from src.objects.RepositoryManager import RepositoryManager
from src.objects.DataGatherer import DataGatherer


def get_resource_from_config(key: str, value: str):
    """
    Use the config.toml file to get any resource, provided
    that the key-value pair exists.
    """

    with open("./config.toml", "rb") as config:
        config = tomllib.load(config)

    # First, check if key-value pair exists.
    if not config[key][value]:
        raise ValueError("Key-value pair doest not exist in config.toml.")

    return config[key][value]


def main():
    db_file_path = get_resource_from_config("database", "locale")
    repo_json_path = get_resource_from_config("json", "locale")
    csv_dump_path = get_resource_from_config("csv_dump", "locale")

    repo_manager = RepositoryManager(db_file_path, repo_json_path)

    # Update all tracked repositories
    for repo in repo_manager.repository_list:
        repo_manager.update_repository(repo)
        print(f"Updated repository: {os.path.basename(repo.working_dir)}")

    data_gatherer = DataGatherer(db_file_path, csv_dump_path)

    # Dump all commits to a CSV file
    data_gatherer.dump_commits("commits_dump.csv")
    print("Commits data dumped to commits_dump.csv")


if __name__ == "__main__":
    main()
