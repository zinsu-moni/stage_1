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
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input must be a string")
        return v


class StringProperties(BaseModel):
    length: int
    palindrome: bool
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
    palindrome = normalized == normalized[::-1] if normalized else False
    

    unique_characters = len(set(value))
    word_count = len(value.split())
    word_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
    

    character_frequency_map = {}
    for char in value:
        character_frequency_map[char] = character_frequency_map.get(char, 0) + 1
    
    return StringProperties(
        length=length,
        palindrome=palindrome,
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
        palindrome=properties.palindrome,
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
                palindrome=db_string.palindrome,
                unique_characters=db_string.unique_characters,
                word_count=db_string.word_count,
                word_hash=db_string.word_hash,
                character_frequency_map=db_string.character_frequency_map
            ),
            created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
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
            palindrome=db_string.palindrome,
            unique_characters=db_string.unique_characters,
            word_count=db_string.word_count,
            word_hash=db_string.word_hash,
            character_frequency_map=db_string.character_frequency_map
        ),
        created_at=db_string.created_at.isoformat().replace("+00:00", "Z")
    )

@app.get("/strings", response_model=StringListResponse)
async def get_strings(
    palindrome: Optional[bool] = Query(None, description="Filter by palindrome status"),
    min_length: Optional[int] = Query(None, description="Minimum string length", ge=0),
    max_length: Optional[int] = Query(None, description="Maximum string length", ge=0),
    word_count: Optional[int] = Query(None, description="Exact word count", ge=0),
    contains_character: Optional[str] = Query(None, description="Single character to search for", max_length=1),
    db: Session = Depends(get_db)
):
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(status_code=400, detail="min_length cannot be greater than max_length")
    

    filters_applied = {}
    if palindrome is not None:
        filters_applied["palindrome"] = palindrome
    if min_length is not None:
        filters_applied["min_length"] = min_length
    if max_length is not None:
        filters_applied["max_length"] = max_length
    if word_count is not None:
        filters_applied["word_count"] = word_count
    if contains_character is not None:
        filters_applied["contains_character"] = contains_character

    query = db.query(Stringsanalysis)

    if palindrome is not None:
        query = query.filter(Stringsanalysis.palindrome == palindrome)
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
                palindrome=db_string.palindrome,
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

