from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import drop_db, init_db, Stringsanalysis, get_db
import hashlib
import re


app = FastAPI(title="String Analysis API", version="1.0.0")


@app.on_event("startup")
def startup_event():
    init_db()


class StringInput(BaseModel):
    value: str = Field(..., description="String to analyze")
    
    @validator('value')
    def validate_value(cls, v):
        if not isinstance(v, str):
            raise ValueError('value must be a string')
        return v


class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    word_hash: str
    character_frequency_map: Dict[str, int]


class StringResponse(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: str


class StringListResponse(BaseModel):
    data: List[StringResponse]
    count: int
    filters_applied: Dict


class NaturalLanguageResponse(BaseModel):
    data: List[StringResponse]
    count: int
    interpreted_query: Dict


def string_properties(value: str) -> StringProperties:
    length = len(value)
    normalized = value.lower().replace(" ", "")
    is_palindrome = normalized == normalized[::-1] if normalized else False
    

    unique_characters = len(set(value))
    word_count = len(value.split())
    word_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
    

    character_frequency_map = {}
    for char in value:
        character_frequency_map[char] = character_frequency_map.get(char, 0) + 1
    
    return StringProperties(
        length=length,
        is_palindrome=is_palindrome,
        unique_characters=unique_characters,
        word_count=word_count,
        word_hash=word_hash,
        character_frequency_map=character_frequency_map
    )


@app.post("/strings", status_code=201, response_model=StringResponse)
async def create_string(string_input: StringInput, db: Session = Depends(get_db)):
    value = string_input.value
    properties = string_properties(value)
    word_hash = properties.word_hash

    existing = db.query(Stringsanalysis).filter(Stringsanalysis.id == word_hash).first()
    if existing:
        raise HTTPException(status_code=409, detail="String already exists in the system")
    
    
    created_at = datetime.now(timezone.utc)

    db_string = Stringsanalysis(
        id=word_hash,
        value=value,
        length=properties.length,
        is_palindrome=properties.is_palindrome,
        unique_characters=properties.unique_characters,
        word_count=properties.word_count,
        word_hash=properties.word_hash,
        character_frequency_map=properties.character_frequency_map,
        created_at=created_at
    )
    
    try:
        db.add(db_string)
        db.commit()
        db.refresh(db_string)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="String already exists in the Database")
        
    return StringResponse(
            id=db_string.id,
            value=db_string.value,
            properties=StringProperties(
                length=db_string.length,
                is_palindrome=db_string.is_palindrome,
                unique_characters=db_string.unique_characters,
                word_count=db_string.word_count,
                word_hash=db_string.word_hash,
                character_frequency_map=db_string.character_frequency_map
            ),
            created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
    ) 


@app.get("/strings/filter-by-natural-language", response_model=NaturalLanguageResponse)
async def filter_by_natural_language(
    query: str = Query(..., description="Natural language query"),
    db: Session = Depends(get_db)
):
 
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")
    
    query_lower = query.lower()
    parsed_filters = {}
    
    try:
        if "palindrom" in query_lower:
            parsed_filters["is_palindrome"] = True
        
       
        if "single word" in query_lower:
            parsed_filters["word_count"] = 1
        elif "two word" in query_lower or "2 word" in query_lower:
            parsed_filters["word_count"] = 2
        elif "three word" in query_lower or "3 word" in query_lower:
            parsed_filters["word_count"] = 3
        
       
        length_pattern = r"longer than (\d+)"
        match = re.search(length_pattern, query_lower)
        if match:
            parsed_filters["min_length"] = int(match.group(1)) + 1
        
        shorter_pattern = r"shorter than (\d+)"
        match = re.search(shorter_pattern, query_lower)
        if match:
            parsed_filters["max_length"] = int(match.group(1)) - 1
        
        at_least_pattern = r"at least (\d+) characters"
        match = re.search(at_least_pattern, query_lower)
        if match:
            parsed_filters["min_length"] = int(match.group(1))
        
        
        char_patterns = [
            r"contain(?:ing|s)? (?:the letter |the character )?([a-z])",
            r"with (?:the letter |the character )?([a-z])",
            r"that (?:have|has) (?:the letter |the character )?([a-z])"
        ]
        
        for pattern in char_patterns:
            match = re.search(pattern, query_lower)
            if match:
                parsed_filters["contains_character"] = match.group(1)
                break
        
       
        if "first vowel" in query_lower:
            parsed_filters["contains_character"] = "a"
        
        
        if "min_length" in parsed_filters and "max_length" in parsed_filters:
            if parsed_filters["min_length"] > parsed_filters["max_length"]:
                raise HTTPException(
                    status_code=422,
                    detail="Query parsed but resulted in conflicting filters"
                )
        
      
        if not parsed_filters:
            raise HTTPException(
                status_code=400,
                detail="Unable to parse natural language query"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")
    
    
    db_query = db.query(Stringsanalysis)
    
    if "is_palindrome" in parsed_filters:
        db_query = db_query.filter(Stringsanalysis.is_palindrome == parsed_filters["is_palindrome"])
    if "min_length" in parsed_filters:
        db_query = db_query.filter(Stringsanalysis.length >= parsed_filters["min_length"])
    if "max_length" in parsed_filters:
        db_query = db_query.filter(Stringsanalysis.length <= parsed_filters["max_length"])
    if "word_count" in parsed_filters:
        db_query = db_query.filter(Stringsanalysis.word_count == parsed_filters["word_count"])
    if "contains_character" in parsed_filters:
        db_query = db_query.filter(Stringsanalysis.value.contains(parsed_filters["contains_character"]))
    
    
    results = db_query.all()
    

    filtered_strings = []
    for db_string in results:
        filtered_strings.append(StringResponse(
            id=db_string.id,
            value=db_string.value,
            properties=StringProperties(
                length=db_string.length,
                is_palindrome=db_string.is_palindrome,
                unique_characters=db_string.unique_characters,
                word_count=db_string.word_count,
                word_hash=db_string.word_hash,
                character_frequency_map=db_string.character_frequency_map
            ),
            created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
        ))
    
    return NaturalLanguageResponse(
        data=filtered_strings,
        count=len(filtered_strings),
        interpreted_query={
            "original": query,
            "parsed_filters": parsed_filters
        }
    )


@app.get("/strings/{string_value}", response_model=StringResponse)
async def get_specific_string(string_value: str, db: Session = Depends(get_db)):

    word_hash = hashlib.sha256(string_value.encode('utf-8')).hexdigest()
    
    db_string = db.query(Stringsanalysis).filter(Stringsanalysis.id == word_hash).first()
    
    if not db_string:
        raise HTTPException(status_code=404, detail="String does not exist in the system")

    return StringResponse(
        id=db_string.id,
        value=db_string.value,
        properties=StringProperties(
            length=db_string.length,
            is_palindrome=db_string.is_palindrome,
            unique_characters=db_string.unique_characters,
            word_count=db_string.word_count,
            word_hash=db_string.word_hash,
            character_frequency_map=db_string.character_frequency_map
        ),
        created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
    )

@app.get("/strings", response_model=StringListResponse)
async def get_strings(
    is_palindrome: Optional[bool] = Query(None, description="Filter by palindrome status"),
    min_length: Optional[int] = Query(None, description="Minimum string length", ge=0),
    max_length: Optional[int] = Query(None, description="Maximum string length", ge=0),
    word_count: Optional[int] = Query(None, description="Exact word count", ge=0),
    contains_character: Optional[str] = Query(None, description="Single character to search for", max_length=1),
    db: Session = Depends(get_db)
):
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(status_code=400, detail="min_length cannot be greater than max_length")
    

    filters_applied = {}
    if is_palindrome is not None:
        filters_applied["is_palindrome"] = is_palindrome
    if min_length is not None:
        filters_applied["min_length"] = min_length
    if max_length is not None:
        filters_applied["max_length"] = max_length
    if word_count is not None:
        filters_applied["word_count"] = word_count
    if contains_character is not None:
        filters_applied["contains_character"] = contains_character

    query = db.query(Stringsanalysis)

    if is_palindrome is not None:
        query = query.filter(Stringsanalysis.is_palindrome == is_palindrome)
    if min_length is not None:
        query = query.filter(Stringsanalysis.length >= min_length)
    if max_length is not None:
        query = query.filter(Stringsanalysis.length <= max_length)
    if word_count is not None:
        query = query.filter(Stringsanalysis.word_count == word_count)
    if contains_character is not None:
        query = query.filter(Stringsanalysis.value.contains(contains_character))

    db_strings = query.all()

    strings_filtered = [
        StringResponse(
            id=db_string.id,
            value=db_string.value,
            properties=StringProperties(
                length=db_string.length,
                is_palindrome=db_string.is_palindrome,
                unique_characters=db_string.unique_characters,
                word_count=db_string.word_count,
                word_hash=db_string.word_hash,
                character_frequency_map=db_string.character_frequency_map
            ),
            created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
        )
        for db_string in db_strings
    ]

    return StringListResponse(
        data=strings_filtered,
        count=len(strings_filtered),
        filters_applied=filters_applied
    )


@app.delete("/strings/{string_value}", status_code=204)
async def delete_string(string_value: str, db: Session = Depends(get_db)):
    word_hash = hashlib.sha256(string_value.encode('utf-8')).hexdigest()
    
    db_string = db.query(Stringsanalysis).filter(Stringsanalysis.id == word_hash).first()
    
    if not db_string:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    
    db.delete(db_string)
    db.commit()
    
    return None


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "String Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /strings": "Create a new string analysis",
            "GET /strings/{string_value}": "Retrieve a specific string",
            "GET /strings": "List all strings with optional filters",
            "GET /strings/filter-by-natural-language": "Filter strings using natural language",
            "DELETE /strings/{string_value}": "Delete a string",
            "GET /docs": "API documentation"
        }
    }

