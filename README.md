# Web-Crawler

This is a Python web crawler project that includes a virtual environment and a basic structure for development and testing.

## Setup Instructions

1. **Create a Virtual Environment**:
   To create a virtual environment, run the following command in your terminal:
   ```
   python -m venv venv
   ```

2. **Activate the Virtual Environment**:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   After activating the virtual environment, install the required dependencies using:
   ```
   pip install -r requirements.txt
   ```

## Usage

The web crawler will be implemented in the `src` directory. Tests will be located in the `tests` directory. Make sure to activate your virtual environment before running any scripts.

## Running the Application

To run the application, execute the `main.py` file. The script accepts several command-line arguments to customize its behavior. Use the following syntax:

```bash
python main.py [options]
```

### Available Arguments

- `--url <URL>`: The starting URL for the web crawler.
- `--map-pages <DEPTH>`: The maximum pages to crawl (default is 100).
- `--concurrency <NUMBER>`: The number of threads to use for crawling (default is 10).

### Example Usage

```bash
python main.py --url https://example.com --max-pages 50 --concurrency 8
```

This command will start crawling from `https://example.com`, will crawl all internal links before reach limit `max-pages`, save the results in postgres db, and use 8 threads for faster crawling. The log will be saved in the `crawler.log` file

This script requires certain environment variables to be set in a `.env` file. 
Make sure to include the following variables:

1. `POSTGRES_USER` - The username for the PostgreSQL database.
2. `POSTGRES_PASSWORD` - The password for the PostgreSQL database.
3. `POSTGRES_DB` - The name of the PostgreSQL database.

Ensure the `.env` file is properly configured before running the script.

Make sure to activate your virtual environment before running the script. 

## Docker Support

**Development with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   # This configuration will create two containers:
   # 1. A Python container with all the necessary dependencies installed.
   # 2. A PostgreSQL container that serves as the database.

   **Access Docker Container Shell**:
      ```bash
      docker exec -it crawler bash
      ```

   This command allows you to:
   - Connect to the running crawler container
   - Access an interactive bash shell
   - Execute commands directly inside the container

Note: Make sure you have Docker and Docker Compose installed on your machine before running these commands.