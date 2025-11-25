# Budget Proposal Statistics API

FastAPI application that generates budget proposal statistics from the Keystone GraphQL API.

## Features

- 📊 Generate statistics organized by legislator
- 🏛️ Generate statistics organized by department (government)
- 🔍 Filter by specific budget year
- 📈 Includes overall statistics and detailed breakdowns
- 🚀 Async GraphQL queries with retry logic
- ☁️ Upload generated JSON to Google Cloud Storage

## Setup

### Prerequisites

- Python 3.11 or higher
- Access to the Keystone GraphQL API

### Installation

1. Clone the repository:
```bash
cd /Users/hcchien/readr/budget-data
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# GraphQL API Configuration
GRAPHQL_ENDPOINT=https://ly-budget-gql-dev-1075249966777.asia-east1.run.app/api/graphql

# Authentication (if required)
# API_KEY=your_api_key_here
# BEARER_TOKEN=your_bearer_token_here

# API Settings
API_TIMEOUT=30
API_MAX_RETRIES=3

# GCS Settings (for uploading JSON files)
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=/path/to/your/service-account-key.json
GCS_OUTPUT_PREFIX=budget-statistics
```

> **Note**: GCS settings are optional. If not configured, the upload endpoints will return an error.

## Running the Application

### Development Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Root
- **GET** `/`
- Returns API information and available endpoints

### Statistics by Legislator
- **GET** `/api/statistics/by-legislator`
- **Query Parameters:**
  - `year` (optional): Filter by specific budget year (e.g., `114`)

**Response Format:**
```json
[
  {
    "yearInfo": {
      "budgetYearId": "1",
      "year": 114
    },
    "overall": {
      "reductionAmount": 123456789,
      "reductionCount": 42,
      "freezeAmount": 987654321,
      "freezeCount": 35,
      "otherCount": 20
    },
    "legislators": [
      {
        "peopleId": "724",
        "name": "李柏毅",
        "proposerOnly": {
          "reductionAmount": 1000000,
          "reductionCount": 3,
          "freezeAmount": 500000,
          "freezeCount": 2,
          "otherCount": 1
        },
        "allInvolved": {
          "reductionAmount": 1500000,
          "reductionCount": 4,
          "freezeAmount": 700000,
          "freezeCount": 3,
          "otherCount": 2
        }
      }
    ]
  }
]
```

### Statistics by Department
- **GET** `/api/statistics/by-department`
- **Query Parameters:**
  - `year` (optional): Filter by specific budget year (e.g., `114`)

**Response Format:**
```json
[
  {
    "yearInfo": {
      "budgetYearId": "1",
      "year": 114
    },
    "overall": {
      "reductionAmount": 123456789,
      "reductionCount": 42,
      "freezeAmount": 987654321,
      "freezeCount": 35,
      "otherCount": 20
    },
    "departments": [
      {
        "governmentId": "1",
        "name": "教育部",
        "reductionAmount": 10000000,
        "reductionCount": 5,
        "freezeAmount": 5000000,
        "freezeCount": 3,
        "otherCount": 2
      }
    ]
  }
]
```

### Upload Statistics to GCS

#### Upload by Legislator
- **POST** `/api/upload/by-legislator`
- **Query Parameters:**
  - `year` (optional): Filter by specific budget year
  - `use_latest` (optional, default: `true`): Use 'latest' filename instead of timestamp

**Response:**
```json
{
  "status": "success",
  "gcs_path": "gs://your-bucket/budget-statistics/by-legislator_latest.json",
  "years_count": 1
}
```

#### Upload by Department
- **POST** `/api/upload/by-department`
- **Query Parameters:**
  - `year` (optional): Filter by specific budget year
  - `use_latest` (optional, default: `true`): Use 'latest' filename instead of timestamp

**Response:**
```json
{
  "status": "success",
  "gcs_path": "gs://your-bucket/budget-statistics/by-department_latest.json",
  "years_count": 1
}
```

### Health Check
- **GET** `/health`
- Returns service health status

## Data Filtering

The API automatically filters proposals based on the following criteria:

- ✅ `publishStatus = "published"` - Only published proposals
- ✅ `result = "passed"` - Only passed proposals
- ✅ `mergedParentProposals = null` - Excludes child proposals (merged)
- ✅ `historicalParentProposals = null` - Excludes child proposals (historical)

## Statistics Breakdown

### Proposal Types
- **reduce** (刪減): Reduction proposals
- **freeze** (凍結): Freeze proposals
- **other** (其他建議): Other proposals

### Legislator Statistics
- **proposerOnly**: Only counts proposals where the legislator is listed as a proposer
- **allInvolved**: Counts proposals where the legislator is either a proposer or co-signer

## Example Usage

### Get all statistics by legislator
```bash
curl http://localhost:8000/api/statistics/by-legislator
```

### Get statistics for a specific year
```bash
curl http://localhost:8000/api/statistics/by-legislator?year=114
```

### Get statistics by department
```bash
curl http://localhost:8000/api/statistics/by-department
```

### Upload statistics to GCS
```bash
# Upload latest legislator statistics
curl -X POST http://localhost:8000/api/upload/by-legislator

# Upload with timestamp
curl -X POST "http://localhost:8000/api/upload/by-legislator?use_latest=false"

# Upload department statistics
curl -X POST http://localhost:8000/api/upload/by-department
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

```
budget-data/
├── main.py              # FastAPI application and endpoints
├── graphql_client.py    # GraphQL client for Keystone API
├── gcs_client.py        # GCS client for uploading JSON files
├── statistics.py        # Statistics calculation logic
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .env                 # Your environment variables (not in git)
└── README.md           # This file
```

## Development

### Code Style
The project follows standard Python conventions and uses type hints for better code clarity.

### Error Handling
- GraphQL errors are caught and logged
- HTTP errors include appropriate status codes
- Retry logic for transient failures

## Deployment

### Docker

Build the image:
```bash
docker build -t budget-data-api .
```

Run the container:
```bash
docker run -p 8080:8080 --env-file .env budget-data-api
```

### Google Cloud Platform

The project includes a `cloudbuild.yaml` file for deployment to Cloud Run via Cloud Build.

1. Enable required APIs:
   - Cloud Build API
   - Cloud Run API
   - Container Registry API

2. Submit the build:
```bash
gcloud builds submit --config cloudbuild.yaml .
```

3. Configure environment variables in Cloud Run:
   - Go to Cloud Run console
   - Select the `budget-data-api` service
   - Edit & Deploy New Revision
   - Add environment variables (GCS_BUCKET_NAME, GCS_CREDENTIALS_PATH, etc.)
   - If using a service account key file for GCS, you'll need to mount it as a secret or use Workload Identity.

## License

See LICENSE file for details.
