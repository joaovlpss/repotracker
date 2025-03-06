import sqlite3
import os
from src.objects.RepositoryManager import RepositoryManager
from src.objects.DataGatherer import DataGatherer


def main():
    db_file_path = "./database/repodb.sqlite3"
    repo_json_path = "./tracked_repos/repositories.json"

    repo_manager = RepositoryManager(db_file_path, repo_json_path)

    # Update all tracked repositories
    for repo in repo_manager.repository_list:
        repo_manager.update_repository(repo)
        print(f"Updated repository: {os.path.basename(repo.working_dir)}")

    data_gatherer = DataGatherer()

    # Dump all commits to a CSV file
    data_gatherer.dump_commits("commits_dump.csv")
    print("Commits data dumped to commits_dump.csv")


if __name__ == "__main__":
    main()
