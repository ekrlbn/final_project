class User:
    def __init__(
        self,
        name_surname: str,
        email: str,
        password: str,
        age: int = None,
        gender: str = None,
        martial_status: str = None,
        number_of_children: int = None,
        education_level: str = None,
        occupation: str = None,
        anual_working_hours: int = None,
        monthly_income: float = None,
        monthly_expenses: float = None,
        debt: float = None,
        assets: float = None,
        location: str = None,
        chronic_diseases: list[str] = None,
        lifestyle_habits: list[str] = None,
        family_health_history: list[str] = None,
        target_retirement_age: int = None,
        target_retirement_income: float = None,
    ):
        self.name_surname = name_surname
        self.email = email
        self.password = password
        self.age = age
        self.gender = gender
        self.martial_status = martial_status
        self.number_of_children = number_of_children
        self.education_level = education_level
        self.occupation = occupation
        self.anual_working_hours = anual_working_hours
        self.monthly_income = monthly_income
        self.monthly_expenses = monthly_expenses
        self.debt = debt
        self.assets = assets
        self.location = location
        self.chronic_diseases = chronic_diseases if chronic_diseases is not None else []
        self.lifestyle_habits = lifestyle_habits if lifestyle_habits is not None else []
        self.family_health_history = (
            family_health_history if family_health_history is not None else []
        )
        self.target_retirement_age = target_retirement_age
        self.target_retirement_income = target_retirement_income

    def to_dict(self):
        return self.__dict__
