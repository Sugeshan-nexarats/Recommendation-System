from pydantic import BaseModel,field_validator
from datetime import datetime
from typing import List

class StartupProfile(BaseModel):

    startup_id:int
    startup_name:str
    started_date:datetime
    funding:int
    employee_count:int
    country:str
    stage:str
    technology:List[str]
    description:str

    @field_validator("started_date",mode="before")
    @classmethod
    def parse_date(cls,value):
        
        if isinstance(value,datetime.date):
            return value
        
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            raise ValueError("Date must be in format dd/mm/yyyy")

class InvestorProfile(BaseModel):

    investor_id:int
    investor_name:str
    preferred_industries:List[str]
    preferred_stages:List[str]
    countries:List[str]
    min_ticket:int
    max_ticket:int
    investment_thesis:str