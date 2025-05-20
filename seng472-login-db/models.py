from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name_surname: str
    email: str
    password: str
    age: Optional[int] = None
    gender: Optional[str] = None
    martial_status: Optional[str] = None
    number_of_children: Optional[int] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    anual_working_hours: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    debt: Optional[float] = None
    assets: Optional[float] = None
    location: Optional[str] = None
    chronic_diseases: Optional[list[str]] = None
    lifestyle_habits: Optional[list[str]] = None
    family_health_history: Optional[list[str]] = None
    target_retirement_age: Optional[int] = None
    target_retirement_income: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert User object to dictionary for MongoDB storage"""
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User object from MongoDB document"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__}) 