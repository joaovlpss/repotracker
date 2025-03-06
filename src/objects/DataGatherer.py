import pandas as pd
import sqlite3


class DataGatherer:
    db_connection: sqlite3.Connection
    dump_path: str
    query_result: pd.DataFrame

    def __init__(self, db_path: str, dump_path: str):
        self.db_connection = sqlite3.connect(db_path)
        self.dump_path = dump_path

    def dump_commits(self, file_name: str) -> None:
        """
        Dump all commits data into a .csv file.
        """
        cursor = self.db_connection.cursor()

        cursor.execute(
            """
            SELECT 
                s.Name AS AuthorName, 
                b.Name AS BranchName, 
                c.Comment, 
                c.Date, 
                c.FileChanges
            FROM commits c
            JOIN staff s ON c.AuthorID = s.ID
            JOIN branch b ON c.BranchID = b.ID
            """
        )

        result = cursor.fetchall()

        result_df = pd.DataFrame(
            result, columns=["Author", "Branch", "Comment", "Date", "FileChanges"]
        )

        file_path = self.dump_path + "/" + file_name
        result_df.to_csv(file_path, sep=",")
