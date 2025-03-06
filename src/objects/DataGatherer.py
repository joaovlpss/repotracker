import pandas as pd
import sqlite3
import tomllib

from pydantic import BaseModel, ConfigDict


class DataGatherer(BaseModel):
    db_connection: sqlite3.Connection
    dump_path: str
    query_result: pd.DataFrame

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )  # Allow arbitrary types for sqlite3 Connection.

    def __init__(self):
        self.db_connection = self.get_connection()
        self.dump_path = self.get_dump_path()

    def get_connection(self) -> sqlite3.Connection:
        """
        Use the config.toml file to initialize the database connection.
        """
        with open("./config.toml", "rb") as config:
            config = tomllib.load(config)

        db_path: str = config["database"]["locale"]
        return sqlite3.connect(db_path)

    def get_dump_path(self) -> str:
        """
        Use the config.toml file to initialize the database connection.
        """
        with open("./config.toml", "rb") as config:
            config = tomllib.load(config)

        dump_path: str = config["csv_dump"]["locale"]
        return dump_path

    def dump_commits(self, file_name: str) -> None:
        """
        Dump all commits data into a .csv file.
        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT AuthorID, BranchID, Comment, Date, FileChanges FROM commit"
        )

        result = cursor.fetchall()

        result_df = pd.DataFrame(
            result, columns=["AuthorID", "BranchID", "Comment", "Date", "FileChanges"]
        )

        file_path = self.dump_path + "/" + file_name
        result_df.to_csv(file_path, sep=",")
