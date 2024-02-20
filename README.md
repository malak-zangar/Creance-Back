# Project Execution

## Setup

1. Create a `.env` file in the root of the project.
2. Copy the variables from `.env.example` to the newly created `.env` file and assign their values. Note: For the database, you can obtain the connection string credentials from the `docker-compose.yml` file.

## Running the Project

To run the project, follow these steps:

1. Open a terminal and navigate to the project directory.
2. Run the following command to build and start the Docker containers:

   ```bash
   docker-compose up --build -d
