# String Analysis API

A FastAPI-based REST API that analyzes strings and stores their computed properties in a PostgreSQL database. The API provides endpoints for creating, retrieving, filtering, and deleting string analyses with support for natural language queries.

## Features

- 🔍 **String Analysis**: Automatically computes properties like length, palindrome status, character frequency, and more
- 🗃️ **Database Storage**: Persistent storage using PostgreSQL with SQLAlchemy ORM
- 🔎 **Advanced Filtering**: Filter strings by multiple criteria (palindrome, length, word count, character containment)
- 💬 **Natural Language Queries**: Filter strings using plain English queries
- 📚 **Interactive Documentation**: Auto-generated API docs with Swagger UI
- ✅ **Full CRUD Operations**: Create, Read, Update, and Delete string records

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Python Version**: 3.13+

## Installation

### Prerequisites

- Python 3.13 or higher
- PostgreSQL database
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/zinsu-moni/stage_1.git
   cd stage_1
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database_name
   ```

5. **Initialize the database**
   ```bash
   python db_setup.py init
   ```

## Running the Application

### Start the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Access the interactive documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## API Endpoints

### 1. Create String Analysis

**POST** `/strings`

Analyzes a string and stores its properties.

**Request Body:**
```json
{
  "value": "racecar"
}
```

**Response (201 Created):**
```json
{
  "id": "473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8",
  "value": "racecar",
  "properties": {
    "length": 7,
    "is_palindrome": true,
    "unique_characters": 4,
    "word_count": 1,
    "word_hash": "473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8",
    "character_frequency_map": {
      "r": 2,
      "a": 2,
      "c": 2,
      "e": 1
    }
  },
  "created_at": "2025-10-20T21:41:00Z"
}
```

**Error Response (409 Conflict):**
```json
{
  "detail": "String already exists in the system"
}
```

---

### 2. Get Specific String

**GET** `/strings/{string_value}`

Retrieves a specific string analysis by its value.

**Example:**
```
GET /strings/racecar
```

**Response (200 OK):**
```json
{
  "id": "473287f8...",
  "value": "racecar",
  "properties": { ... },
  "created_at": "2025-10-20T21:41:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "String does not exist in the system"
}
```

---

### 3. List All Strings with Filters

**GET** `/strings`

Retrieves all strings with optional filtering.

**Query Parameters:**
- `is_palindrome` (boolean): Filter by palindrome status
- `min_length` (integer): Minimum string length
- `max_length` (integer): Maximum string length
- `word_count` (integer): Exact word count
- `contains_character` (string): Single character to search for

**Example:**
```
GET /strings?is_palindrome=true&min_length=5
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "473287f8...",
      "value": "racecar",
      "properties": { ... },
      "created_at": "2025-10-20T21:41:00Z"
    }
  ],
  "count": 1,
  "filters_applied": {
    "is_palindrome": true,
    "min_length": 5
  }
}
```

---

### 4. Natural Language Filtering

**GET** `/strings/filter-by-natural-language`

Filter strings using plain English queries.

**Query Parameter:**
- `query` (required): Natural language query string

**Supported Query Patterns:**

| Query Example | Parsed Filters |
|--------------|----------------|
| "all single word palindromic strings" | `word_count=1, is_palindrome=true` |
| "strings longer than 10 characters" | `min_length=11` |
| "strings shorter than 5 characters" | `max_length=4` |
| "strings containing the letter z" | `contains_character=z` |
| "palindromic strings that contain the first vowel" | `is_palindrome=true, contains_character=a` |
| "strings at least 15 characters" | `min_length=15` |

**Example:**
```
GET /strings/filter-by-natural-language?query=all single word palindromic strings
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "473287f8...",
      "value": "racecar",
      "properties": { ... },
      "created_at": "2025-10-20T21:41:00Z"
    }
  ],
  "count": 1,
  "interpreted_query": {
    "original": "all single word palindromic strings",
    "parsed_filters": {
      "word_count": 1,
      "is_palindrome": true
    }
  }
}
```

**Error Responses:**
- **400 Bad Request**: Unable to parse natural language query
- **422 Unprocessable Entity**: Query parsed but resulted in conflicting filters

---

### 5. Delete String

**DELETE** `/strings/{string_value}`

Deletes a string analysis by its value.

**Example:**
```
DELETE /strings/racecar
```

**Response (204 No Content):**
```
(Empty response body)
```

**Error Response (404 Not Found):**
```json
{
  "detail": "String does not exist in the system"
}
```

---

## Database Management

### Initialize Database
```bash
python db_setup.py init
```

### Reset Database (Warning: Deletes all data)
```bash
python db_setup.py reset
```

### Check Database Connection
```bash
python db_setup.py check
```

## String Properties Explained

Each analyzed string includes the following computed properties:

| Property | Description |
|----------|-------------|
| `length` | Total number of characters in the string |
| `is_palindrome` | Whether the string reads the same forwards and backwards (case-insensitive, ignoring spaces) |
| `unique_characters` | Count of unique characters in the string |
| `word_count` | Number of words (space-separated) in the string |
| `word_hash` | SHA-256 hash of the string (used as unique identifier) |
| `character_frequency_map` | Dictionary mapping each character to its occurrence count |

## Testing

### Using cURL

**Create a string:**
```bash
curl -X POST "http://127.0.0.1:8000/strings" \
  -H "Content-Type: application/json" \
  -d '{"value": "hello world"}'
```

**Get all strings:**
```bash
curl "http://127.0.0.1:8000/strings"
```

**Filter palindromes:**
```bash
curl "http://127.0.0.1:8000/strings?is_palindrome=true"
```

**Natural language query:**
```bash
curl "http://127.0.0.1:8000/strings/filter-by-natural-language?query=single%20word%20palindromic%20strings"
```

**Delete a string:**
```bash
curl -X DELETE "http://127.0.0.1:8000/strings/hello%20world"
```

### Using the Interactive Docs

1. Navigate to `http://127.0.0.1:8000/docs`
2. Expand any endpoint
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

## Project Structure

```
stage_1/
├── main.py              # FastAPI application and route handlers
├── database.py          # SQLAlchemy models and database configuration
├── db_setup.py          # Database initialization and management scripts
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
└── README.md           # This file
```

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Successful GET request
- **201 Created**: Successful POST request
- **204 No Content**: Successful DELETE request
- **400 Bad Request**: Invalid request or unable to parse query
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Valid request but conflicting parameters
- **500 Internal Server Error**: Server error

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Author

**zinsu-moni**
- GitHub: [@zinsu-moni](https://github.com/zinsu-moni)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database powered by [PostgreSQL](https://www.postgresql.org/)
- ORM by [SQLAlchemy](https://www.sqlalchemy.org/)
