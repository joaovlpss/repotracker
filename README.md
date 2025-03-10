# Repotracker - A simple github repository data tracking system.

Repotracker is a simple data engineering system for collecting data on github repositories.
It stores data in a local SQLite database and makes it avaliable through a CSV file dump (or simply querying the database directly).

Repotracker is powered by UV project manager.

## Installation

Currently, repotracker does not support automatic installation. To install manually, follow
the steps below:

  0. Clone this repository.
  1. Install all requirements in `requirements.txt`
  2. Create a `config.toml` file in the top folder of the repository.
  3. Create a SQLite3 database in `./database/<file_name>`.
  4. Create a JSON file in `./tracked_repos/<file_name>` for storing
  the repositories to be tracked.
  5. Inside `./config.toml`, create three sections for the database,
  CSV dump and JSON file's paths, relative to the main folder of this
  repository. Below is an example of such a file:

  ```
```[database]
locale= "./database/database"

[csv_dump]
locale= "./dump"

[json]
locale= "./tracked_repos/repositories.json"
```

  6. Create a JSON object for each repository inside your repository file.
  It should have a field for the name, and another for the SSH connection
  link:

```{
  "repositories": [
    {
      "name": "repotracker",
      "ssh_url": "git@github.com:joaovlpss/repotracker.git"
    }
  ]
}```

  7. Copy the database schema from repodb_schema.sql into your SQLite3
  database.
  8. Finally, run `main.py`.

## Contributing

Currently, many augmentations to the main functionality of repotracker are
desired, such as:

  1. Repository deletion after cloning for less memory consumption.
  2. More comprehensive data collection.
  3. More robust error handling.
  4. More robust date checking for collecting the latest commits.

Any contributions are welcome. For major changes, please open an issue
first to discuss what you would like to change. For smaller fixes or 
features, open a pull request with a descriptive name.


