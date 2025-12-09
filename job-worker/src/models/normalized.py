"""
Normalized Pydantic models with AI-powered validation.

Uses Pydantic AI for intelligent normalization of job data from
different sources (Ashby, Greenhouse, Lever, LinkedIn/Apify).
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_ai import Agent
from typing import Optional, List, Literal
from enum import Enum
import re


# =============================================================================
# ENUMS - Standardized categories
# =============================================================================

class Country(str, Enum):
    """ISO country codes for job locations"""
    UK = "GB"
    US = "US"
    GERMANY = "DE"
    FRANCE = "FR"
    NETHERLANDS = "NL"
    IRELAND = "IE"
    SPAIN = "ES"
    ITALY = "IT"
    CANADA = "CA"
    AUSTRALIA = "AU"
    SINGAPORE = "SG"
    UAE = "AE"
    REMOTE = "REMOTE"
    UNKNOWN = "UNKNOWN"


class UKCity(str, Enum):
    """Major UK cities for filtering"""
    LONDON = "London"
    MANCHESTER = "Manchester"
    BIRMINGHAM = "Birmingham"
    BRISTOL = "Bristol"
    LEEDS = "Leeds"
    LIVERPOOL = "Liverpool"
    EDINBURGH = "Edinburgh"
    GLASGOW = "Glasgow"
    CARDIFF = "Cardiff"
    BELFAST = "Belfast"
    CAMBRIDGE = "Cambridge"
    OXFORD = "Oxford"
    READING = "Reading"
    OTHER = "Other UK"


class USCity(str, Enum):
    """Major US cities for filtering"""
    NEW_YORK = "New York"
    SAN_FRANCISCO = "San Francisco"
    LOS_ANGELES = "Los Angeles"
    SEATTLE = "Seattle"
    AUSTIN = "Austin"
    BOSTON = "Boston"
    CHICAGO = "Chicago"
    DENVER = "Denver"
    MIAMI = "Miami"
    OTHER = "Other US"


class Department(str, Enum):
    """Standardized department categories"""
    FINANCE = "Finance"
    MARKETING = "Marketing"
    ENGINEERING = "Engineering"
    OPERATIONS = "Operations"
    HUMAN_RESOURCES = "Human Resources"
    SALES = "Sales"
    PRODUCT = "Product"
    LEGAL = "Legal"
    STRATEGY = "Strategy"
    DATA = "Data"
    DESIGN = "Design"
    CUSTOMER_SUCCESS = "Customer Success"
    GENERAL_MANAGEMENT = "General Management"
    OTHER = "Other"


class ExecutiveRole(str, Enum):
    """C-suite and executive role categories"""
    CEO = "CEO"
    CFO = "CFO"
    CTO = "CTO"
    CMO = "CMO"
    COO = "COO"
    CHRO = "CHRO"
    CPO = "CPO"  # Chief Product Officer
    CRO = "CRO"  # Chief Revenue Officer
    CDO = "CDO"  # Chief Data Officer
    CIO = "CIO"  # Chief Information Officer
    VP_FINANCE = "VP Finance"
    VP_ENGINEERING = "VP Engineering"
    VP_MARKETING = "VP Marketing"
    VP_SALES = "VP Sales"
    VP_PRODUCT = "VP Product"
    VP_OPERATIONS = "VP Operations"
    VP_HR = "VP HR"
    DIRECTOR = "Director"
    HEAD_OF = "Head of"
    NON_EXECUTIVE = "Non-Executive"


class EmploymentType(str, Enum):
    """Employment arrangement types"""
    FRACTIONAL = "Fractional"
    PART_TIME = "Part-Time"
    CONTRACT = "Contract"
    INTERIM = "Interim"
    TEMPORARY = "Temporary"
    FULL_TIME = "Full-Time"
    FREELANCE = "Freelance"
    UNKNOWN = "Unknown"


class SeniorityLevel(str, Enum):
    """Job seniority levels"""
    C_SUITE = "C-Suite"
    VP = "VP"
    DIRECTOR = "Director"
    HEAD = "Head"
    SENIOR_MANAGER = "Senior Manager"
    MANAGER = "Manager"
    SENIOR = "Senior"
    MID = "Mid"
    JUNIOR = "Junior"
    ENTRY = "Entry"
    UNKNOWN = "Unknown"


class WorkplaceType(str, Enum):
    """Workplace arrangement"""
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "On-site"
    FLEXIBLE = "Flexible"
    UNKNOWN = "Unknown"


class Industry(str, Enum):
    """Company industry categories"""
    TECHNOLOGY = "Technology"
    FINTECH = "Fintech"
    HEALTHTECH = "Healthtech"
    ECOMMERCE = "E-commerce"
    SAAS = "SaaS"
    AI_ML = "AI/ML"
    CYBERSECURITY = "Cybersecurity"
    CONSULTING = "Consulting"
    FINANCIAL_SERVICES = "Financial Services"
    HEALTHCARE = "Healthcare"
    MANUFACTURING = "Manufacturing"
    RETAIL = "Retail"
    MEDIA = "Media"
    EDUCATION = "Education"
    REAL_ESTATE = "Real Estate"
    ENERGY = "Energy"
    OTHER = "Other"


class CompanyStage(str, Enum):
    """Company funding/growth stage"""
    PRE_SEED = "Pre-Seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    SERIES_D_PLUS = "Series D+"
    GROWTH = "Growth"
    PUBLIC = "Public"
    PRIVATE_EQUITY = "Private Equity"
    BOOTSTRAPPED = "Bootstrapped"
    UNKNOWN = "Unknown"


# =============================================================================
# NORMALIZED MODELS
# =============================================================================

class NormalizedLocation(BaseModel):
    """Normalized location with city, region, country"""

    city: Optional[str] = None
    region: Optional[str] = None
    country: Country = Country.UNKNOWN
    country_name: Optional[str] = None
    is_remote: bool = False
    raw_location: Optional[str] = None  # Original string for reference

    @field_validator('city', mode='before')
    @classmethod
    def normalize_city(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None

        # UK city normalization
        uk_city_map = {
            'london': 'London',
            'greater london': 'London',
            'city of london': 'London',
            'manchester': 'Manchester',
            'birmingham': 'Birmingham',
            'bristol': 'Bristol',
            'leeds': 'Leeds',
            'liverpool': 'Liverpool',
            'edinburgh': 'Edinburgh',
            'glasgow': 'Glasgow',
            'cardiff': 'Cardiff',
            'belfast': 'Belfast',
            'cambridge': 'Cambridge',
            'oxford': 'Oxford',
            'reading': 'Reading',
        }

        # US city normalization
        us_city_map = {
            'new york': 'New York',
            'nyc': 'New York',
            'new york city': 'New York',
            'san francisco': 'San Francisco',
            'sf': 'San Francisco',
            'bay area': 'San Francisco',
            'los angeles': 'Los Angeles',
            'la': 'Los Angeles',
            'seattle': 'Seattle',
            'austin': 'Austin',
            'boston': 'Boston',
            'chicago': 'Chicago',
            'denver': 'Denver',
            'miami': 'Miami',
        }

        v_lower = v.lower().strip()

        if v_lower in uk_city_map:
            return uk_city_map[v_lower]
        if v_lower in us_city_map:
            return us_city_map[v_lower]

        # Title case for unknown cities
        return v.strip().title()

    @field_validator('country', mode='before')
    @classmethod
    def normalize_country(cls, v) -> Country:
        if isinstance(v, Country):
            return v
        if not v:
            return Country.UNKNOWN

        v_lower = str(v).lower().strip()

        country_map = {
            'uk': Country.UK,
            'united kingdom': Country.UK,
            'england': Country.UK,
            'scotland': Country.UK,
            'wales': Country.UK,
            'northern ireland': Country.UK,
            'gb': Country.UK,
            'great britain': Country.UK,
            'us': Country.US,
            'usa': Country.US,
            'united states': Country.US,
            'america': Country.US,
            'germany': Country.GERMANY,
            'de': Country.GERMANY,
            'france': Country.FRANCE,
            'fr': Country.FRANCE,
            'netherlands': Country.NETHERLANDS,
            'nl': Country.NETHERLANDS,
            'holland': Country.NETHERLANDS,
            'ireland': Country.IRELAND,
            'ie': Country.IRELAND,
            'spain': Country.SPAIN,
            'es': Country.SPAIN,
            'italy': Country.ITALY,
            'it': Country.ITALY,
            'canada': Country.CANADA,
            'ca': Country.CANADA,
            'australia': Country.AUSTRALIA,
            'au': Country.AUSTRALIA,
            'singapore': Country.SINGAPORE,
            'sg': Country.SINGAPORE,
            'uae': Country.UAE,
            'dubai': Country.UAE,
            'remote': Country.REMOTE,
        }

        return country_map.get(v_lower, Country.UNKNOWN)

    @classmethod
    def from_string(cls, location_str: Optional[str]) -> "NormalizedLocation":
        """Parse a location string into normalized components"""
        if not location_str:
            return cls(is_remote=False, raw_location=location_str)

        raw = location_str
        loc_lower = location_str.lower()

        # Check for remote
        is_remote = any(r in loc_lower for r in ['remote', 'anywhere', 'distributed', 'work from home', 'wfh'])

        # Try to extract city and country
        # Common patterns: "London, UK", "San Francisco, CA", "London", "Remote - UK"
        parts = re.split(r'[,\-/]', location_str)
        parts = [p.strip() for p in parts if p.strip()]

        city = None
        country = Country.UNKNOWN

        if len(parts) >= 2:
            city = parts[0]
            # Last part is usually country/state
            country_str = parts[-1]
            country = cls.model_fields['country'].annotation  # Get validator
            # Re-validate country
            try:
                country = NormalizedLocation.normalize_country(country_str)
            except:
                country = Country.UNKNOWN
        elif len(parts) == 1:
            # Single value - could be city or country
            val = parts[0].lower()
            if val in ['uk', 'us', 'usa', 'remote', 'germany', 'france']:
                country = NormalizedLocation.normalize_country(val)
            else:
                city = parts[0]
                # Infer country from city
                uk_cities = ['london', 'manchester', 'birmingham', 'bristol', 'leeds', 'edinburgh', 'glasgow']
                us_cities = ['new york', 'san francisco', 'los angeles', 'seattle', 'austin', 'boston', 'chicago']

                if val in uk_cities:
                    country = Country.UK
                elif val in us_cities:
                    country = Country.US

        return cls(
            city=city,
            country=country,
            is_remote=is_remote,
            raw_location=raw
        )


class NormalizedCompany(BaseModel):
    """Normalized company information"""

    name: str
    slug: str = ""
    website: Optional[str] = None
    industry: Industry = Industry.OTHER
    stage: CompanyStage = CompanyStage.UNKNOWN
    size: Optional[str] = None  # "1-10", "11-50", "51-200", etc.
    founded_year: Optional[int] = None
    headquarters: Optional[NormalizedLocation] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None

    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug(cls, v, info) -> str:
        if v:
            return v
        # Generate from name if not provided
        name = info.data.get('name', '')
        if name:
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
            slug = slug.strip('-')
            return slug
        return ''

    @model_validator(mode='after')
    def ensure_slug(self):
        if not self.slug and self.name:
            self.slug = re.sub(r'[^a-z0-9]+', '-', self.name.lower()).strip('-')
        return self


class NormalizedSalary(BaseModel):
    """Normalized salary/compensation information"""

    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    currency: str = "GBP"
    period: Literal["hourly", "daily", "weekly", "monthly", "yearly"] = "yearly"
    is_equity_included: bool = False
    equity_description: Optional[str] = None
    raw_salary: Optional[str] = None

    @field_validator('currency', mode='before')
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        if not v:
            return "GBP"

        currency_map = {
            '£': 'GBP',
            'gbp': 'GBP',
            'pound': 'GBP',
            'pounds': 'GBP',
            '$': 'USD',
            'usd': 'USD',
            'dollar': 'USD',
            'dollars': 'USD',
            '€': 'EUR',
            'eur': 'EUR',
            'euro': 'EUR',
            'euros': 'EUR',
        }

        return currency_map.get(v.lower().strip(), v.upper())

    @classmethod
    def from_string(cls, salary_str: Optional[str]) -> Optional["NormalizedSalary"]:
        """Parse a salary string into normalized components"""
        if not salary_str:
            return None

        # Common patterns:
        # "£100,000 - £150,000"
        # "$200k - $300k"
        # "£800/day"
        # "Competitive + equity"

        raw = salary_str
        s = salary_str.lower()

        # Detect currency
        currency = "GBP"
        if '$' in s or 'usd' in s or 'dollar' in s:
            currency = "USD"
        elif '€' in s or 'eur' in s:
            currency = "EUR"

        # Detect period
        period = "yearly"
        if '/day' in s or 'per day' in s or 'daily' in s:
            period = "daily"
        elif '/hour' in s or 'per hour' in s or 'hourly' in s:
            period = "hourly"
        elif '/week' in s or 'per week' in s or 'weekly' in s:
            period = "weekly"
        elif '/month' in s or 'per month' in s or 'monthly' in s:
            period = "monthly"

        # Extract numbers
        numbers = re.findall(r'[\d,]+(?:\.\d+)?k?', s)
        amounts = []
        for n in numbers:
            n = n.replace(',', '')
            if n.endswith('k'):
                amounts.append(int(float(n[:-1]) * 1000))
            else:
                try:
                    amounts.append(int(float(n)))
                except:
                    pass

        min_amount = amounts[0] if len(amounts) >= 1 else None
        max_amount = amounts[1] if len(amounts) >= 2 else min_amount

        # Check for equity
        is_equity = any(e in s for e in ['equity', 'stock', 'options', 'shares'])

        return cls(
            min_amount=min_amount,
            max_amount=max_amount,
            currency=currency,
            period=period,
            is_equity_included=is_equity,
            raw_salary=raw
        )


class NormalizedJob(BaseModel):
    """
    Fully normalized job listing.

    This is the canonical schema that all scrapers should output.
    AI normalization is applied via validators and the from_raw() method.
    """

    # Identifiers
    id: Optional[str] = None
    external_id: Optional[str] = None
    source: Optional[str] = None  # ashby, greenhouse, lever, linkedin, etc.
    url: str

    # Core job info
    title: str
    title_normalized: Optional[str] = None  # AI-normalized title
    executive_role: Optional[ExecutiveRole] = None

    # Company
    company: NormalizedCompany

    # Classification
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    seniority_level: SeniorityLevel = SeniorityLevel.UNKNOWN
    department: Department = Department.OTHER
    is_fractional: bool = False

    # Location
    location: NormalizedLocation
    workplace_type: WorkplaceType = WorkplaceType.UNKNOWN

    # Compensation
    salary: Optional[NormalizedSalary] = None

    # Time commitment (for fractional/part-time)
    hours_per_week: Optional[str] = None
    days_per_week: Optional[str] = None
    duration_months: Optional[int] = None  # For contract roles

    # Description
    description_snippet: Optional[str] = None
    full_description: Optional[str] = None
    description_html: Optional[str] = None

    # Structured content
    responsibilities: List[str] = []
    requirements: List[str] = []
    qualifications: List[str] = []
    nice_to_have: List[str] = []
    benefits: List[str] = []
    skills_required: List[str] = []

    # Company context
    about_company: Optional[str] = None
    about_team: Optional[str] = None

    # Dates
    posted_date: Optional[str] = None
    application_deadline: Optional[str] = None

    # Classification metadata
    classification_confidence: float = 0.0
    classification_reasoning: Optional[str] = None

    # Site targeting
    site_tags: List[str] = []  # ["fractional", "startup-jobs", "fintech"]

    @field_validator('employment_type', mode='before')
    @classmethod
    def normalize_employment_type(cls, v) -> EmploymentType:
        if isinstance(v, EmploymentType):
            return v
        if not v:
            return EmploymentType.UNKNOWN

        v_lower = str(v).lower().strip().replace('-', '_').replace(' ', '_')

        type_map = {
            'fractional': EmploymentType.FRACTIONAL,
            'part_time': EmploymentType.PART_TIME,
            'part time': EmploymentType.PART_TIME,
            'parttime': EmploymentType.PART_TIME,
            'contract': EmploymentType.CONTRACT,
            'contractor': EmploymentType.CONTRACT,
            'interim': EmploymentType.INTERIM,
            'temporary': EmploymentType.TEMPORARY,
            'temp': EmploymentType.TEMPORARY,
            'full_time': EmploymentType.FULL_TIME,
            'full time': EmploymentType.FULL_TIME,
            'fulltime': EmploymentType.FULL_TIME,
            'permanent': EmploymentType.FULL_TIME,
            'freelance': EmploymentType.FREELANCE,
        }

        return type_map.get(v_lower, EmploymentType.UNKNOWN)

    @field_validator('seniority_level', mode='before')
    @classmethod
    def normalize_seniority(cls, v) -> SeniorityLevel:
        if isinstance(v, SeniorityLevel):
            return v
        if not v:
            return SeniorityLevel.UNKNOWN

        v_lower = str(v).lower().strip().replace('-', '_').replace(' ', '_')

        level_map = {
            'c_suite': SeniorityLevel.C_SUITE,
            'csuite': SeniorityLevel.C_SUITE,
            'c_level': SeniorityLevel.C_SUITE,
            'chief': SeniorityLevel.C_SUITE,
            'vp': SeniorityLevel.VP,
            'vice_president': SeniorityLevel.VP,
            'director': SeniorityLevel.DIRECTOR,
            'head': SeniorityLevel.HEAD,
            'head_of': SeniorityLevel.HEAD,
            'senior_manager': SeniorityLevel.SENIOR_MANAGER,
            'manager': SeniorityLevel.MANAGER,
            'senior': SeniorityLevel.SENIOR,
            'mid': SeniorityLevel.MID,
            'mid_level': SeniorityLevel.MID,
            'junior': SeniorityLevel.JUNIOR,
            'entry': SeniorityLevel.ENTRY,
            'entry_level': SeniorityLevel.ENTRY,
        }

        return level_map.get(v_lower, SeniorityLevel.UNKNOWN)

    @field_validator('department', mode='before')
    @classmethod
    def normalize_department(cls, v) -> Department:
        if isinstance(v, Department):
            return v
        if not v:
            return Department.OTHER

        v_lower = str(v).lower().strip()

        # Keywords to department mapping
        if any(k in v_lower for k in ['finance', 'accounting', 'cfo', 'financial']):
            return Department.FINANCE
        if any(k in v_lower for k in ['marketing', 'cmo', 'brand', 'growth']):
            return Department.MARKETING
        if any(k in v_lower for k in ['engineering', 'cto', 'development', 'software', 'tech']):
            return Department.ENGINEERING
        if any(k in v_lower for k in ['operations', 'coo', 'ops']):
            return Department.OPERATIONS
        if any(k in v_lower for k in ['hr', 'human resources', 'people', 'talent', 'chro']):
            return Department.HUMAN_RESOURCES
        if any(k in v_lower for k in ['sales', 'cro', 'revenue', 'business development']):
            return Department.SALES
        if any(k in v_lower for k in ['product', 'cpo']):
            return Department.PRODUCT
        if any(k in v_lower for k in ['legal', 'compliance', 'general counsel']):
            return Department.LEGAL
        if any(k in v_lower for k in ['strategy', 'corporate development']):
            return Department.STRATEGY
        if any(k in v_lower for k in ['data', 'analytics', 'cdo']):
            return Department.DATA
        if any(k in v_lower for k in ['design', 'ux', 'ui', 'creative']):
            return Department.DESIGN
        if any(k in v_lower for k in ['customer success', 'customer service', 'support']):
            return Department.CUSTOMER_SUCCESS
        if any(k in v_lower for k in ['ceo', 'general manager', 'managing director']):
            return Department.GENERAL_MANAGEMENT

        return Department.OTHER

    @field_validator('workplace_type', mode='before')
    @classmethod
    def normalize_workplace(cls, v) -> WorkplaceType:
        if isinstance(v, WorkplaceType):
            return v
        if not v:
            return WorkplaceType.UNKNOWN

        v_lower = str(v).lower().strip()

        if any(k in v_lower for k in ['remote', 'work from home', 'wfh', 'anywhere']):
            return WorkplaceType.REMOTE
        if any(k in v_lower for k in ['hybrid', 'mixed']):
            return WorkplaceType.HYBRID
        if any(k in v_lower for k in ['onsite', 'on-site', 'office', 'in-person']):
            return WorkplaceType.ONSITE
        if any(k in v_lower for k in ['flexible']):
            return WorkplaceType.FLEXIBLE

        return WorkplaceType.UNKNOWN

    def detect_executive_role(self) -> Optional[ExecutiveRole]:
        """Detect executive role from title"""
        title_lower = self.title.lower()

        role_patterns = {
            ExecutiveRole.CEO: ['ceo', 'chief executive', 'managing director'],
            ExecutiveRole.CFO: ['cfo', 'chief financial', 'finance director'],
            ExecutiveRole.CTO: ['cto', 'chief technology', 'chief technical'],
            ExecutiveRole.CMO: ['cmo', 'chief marketing'],
            ExecutiveRole.COO: ['coo', 'chief operating', 'chief operations'],
            ExecutiveRole.CHRO: ['chro', 'chief human resources', 'chief people'],
            ExecutiveRole.CPO: ['cpo', 'chief product'],
            ExecutiveRole.CRO: ['cro', 'chief revenue'],
            ExecutiveRole.CDO: ['cdo', 'chief data'],
            ExecutiveRole.CIO: ['cio', 'chief information'],
            ExecutiveRole.VP_FINANCE: ['vp finance', 'vp of finance', 'vice president finance'],
            ExecutiveRole.VP_ENGINEERING: ['vp engineering', 'vp of engineering', 'vice president engineering'],
            ExecutiveRole.VP_MARKETING: ['vp marketing', 'vp of marketing', 'vice president marketing'],
            ExecutiveRole.VP_SALES: ['vp sales', 'vp of sales', 'vice president sales'],
            ExecutiveRole.VP_PRODUCT: ['vp product', 'vp of product', 'vice president product'],
            ExecutiveRole.VP_OPERATIONS: ['vp operations', 'vp of operations', 'vice president operations'],
            ExecutiveRole.VP_HR: ['vp hr', 'vp of hr', 'vp people', 'vice president hr'],
            ExecutiveRole.DIRECTOR: ['director'],
            ExecutiveRole.HEAD_OF: ['head of'],
        }

        for role, patterns in role_patterns.items():
            if any(p in title_lower for p in patterns):
                return role

        return None

    @model_validator(mode='after')
    def post_process(self):
        """Post-processing after all fields are set"""
        # Detect executive role if not set
        if not self.executive_role:
            self.executive_role = self.detect_executive_role()

        # Auto-detect fractional from title
        title_lower = self.title.lower()
        if any(k in title_lower for k in ['fractional', 'part-time', 'interim']):
            self.is_fractional = True
            if 'fractional' in title_lower:
                self.employment_type = EmploymentType.FRACTIONAL
            elif 'interim' in title_lower:
                self.employment_type = EmploymentType.INTERIM
            elif 'part-time' in title_lower or 'part time' in title_lower:
                self.employment_type = EmploymentType.PART_TIME

        # Set seniority from executive role
        if self.executive_role and self.seniority_level == SeniorityLevel.UNKNOWN:
            if self.executive_role in [ExecutiveRole.CEO, ExecutiveRole.CFO, ExecutiveRole.CTO,
                                        ExecutiveRole.CMO, ExecutiveRole.COO, ExecutiveRole.CHRO,
                                        ExecutiveRole.CPO, ExecutiveRole.CRO, ExecutiveRole.CDO,
                                        ExecutiveRole.CIO]:
                self.seniority_level = SeniorityLevel.C_SUITE
            elif 'VP' in self.executive_role.value:
                self.seniority_level = SeniorityLevel.VP
            elif self.executive_role == ExecutiveRole.DIRECTOR:
                self.seniority_level = SeniorityLevel.DIRECTOR
            elif self.executive_role == ExecutiveRole.HEAD_OF:
                self.seniority_level = SeniorityLevel.HEAD

        # Set department from executive role if not set
        if self.department == Department.OTHER and self.executive_role:
            role_to_dept = {
                ExecutiveRole.CFO: Department.FINANCE,
                ExecutiveRole.VP_FINANCE: Department.FINANCE,
                ExecutiveRole.CMO: Department.MARKETING,
                ExecutiveRole.VP_MARKETING: Department.MARKETING,
                ExecutiveRole.CTO: Department.ENGINEERING,
                ExecutiveRole.VP_ENGINEERING: Department.ENGINEERING,
                ExecutiveRole.COO: Department.OPERATIONS,
                ExecutiveRole.VP_OPERATIONS: Department.OPERATIONS,
                ExecutiveRole.CHRO: Department.HUMAN_RESOURCES,
                ExecutiveRole.VP_HR: Department.HUMAN_RESOURCES,
                ExecutiveRole.CRO: Department.SALES,
                ExecutiveRole.VP_SALES: Department.SALES,
                ExecutiveRole.CPO: Department.PRODUCT,
                ExecutiveRole.VP_PRODUCT: Department.PRODUCT,
                ExecutiveRole.CDO: Department.DATA,
                ExecutiveRole.CEO: Department.GENERAL_MANAGEMENT,
            }
            if self.executive_role in role_to_dept:
                self.department = role_to_dept[self.executive_role]

        # Add site tags based on classification
        if self.is_fractional and 'fractional' not in self.site_tags:
            self.site_tags.append('fractional')

        return self

    @classmethod
    def from_raw(cls, raw_data: dict, source: str = "unknown") -> "NormalizedJob":
        """
        Create a NormalizedJob from raw scraped data.

        This handles the conversion from various scraper formats
        (Ashby, Greenhouse, Lever, LinkedIn) to our normalized schema.
        """
        # Extract location
        location_str = raw_data.get('location') or raw_data.get('locations', [{}])[0].get('name') if isinstance(raw_data.get('locations'), list) else None
        location = NormalizedLocation.from_string(location_str)

        # Extract company
        company = NormalizedCompany(
            name=raw_data.get('company_name', 'Unknown'),
            description=raw_data.get('about_company'),
        )

        # Extract salary
        salary = None
        if raw_data.get('compensation') or raw_data.get('salary_info'):
            salary = NormalizedSalary.from_string(
                raw_data.get('compensation') or raw_data.get('salary_info')
            )

        return cls(
            id=raw_data.get('id'),
            external_id=raw_data.get('external_id'),
            source=source,
            url=raw_data.get('url', ''),
            title=raw_data.get('title', 'Unknown'),
            company=company,
            location=location,
            employment_type=raw_data.get('employment_type'),
            seniority_level=raw_data.get('seniority_level'),
            department=raw_data.get('department'),
            workplace_type=raw_data.get('workplace_type'),
            salary=salary,
            hours_per_week=raw_data.get('hours_per_week'),
            description_snippet=raw_data.get('description_snippet') or raw_data.get('overview'),
            full_description=raw_data.get('full_description') or raw_data.get('description_plain'),
            description_html=raw_data.get('description_html'),
            responsibilities=raw_data.get('responsibilities', []),
            requirements=raw_data.get('requirements', []),
            qualifications=raw_data.get('qualifications', []),
            nice_to_have=raw_data.get('nice_to_have', []),
            benefits=raw_data.get('benefits', []),
            skills_required=raw_data.get('skills_required', []),
            about_company=raw_data.get('about_company'),
            about_team=raw_data.get('about_team'),
            posted_date=raw_data.get('posted_date') or raw_data.get('published_date'),
            application_deadline=raw_data.get('application_deadline'),
            is_fractional=raw_data.get('is_fractional', False),
            classification_confidence=raw_data.get('classification_confidence', 0.0),
            classification_reasoning=raw_data.get('classification_reasoning'),
            site_tags=raw_data.get('site_tags', []),
        )


# =============================================================================
# PYDANTIC AI AGENT FOR ADVANCED NORMALIZATION
# =============================================================================

def get_job_normalizer_agent() -> Agent:
    """
    Lazy-load the AI agent for complex normalization.
    Requires ANTHROPIC_API_KEY environment variable.
    """
    return Agent(
        'anthropic:claude-3-5-haiku-latest',
        result_type=NormalizedJob,
        system_prompt="""You are a job data normalizer. Given raw job data,
        extract and normalize all fields into the standard schema.

        Pay special attention to:
        - Detecting fractional/part-time executive roles
        - Normalizing locations to city + country
        - Extracting salary ranges and currency
        - Categorizing departments and seniority levels
        - Identifying C-suite and VP roles
        """
    )
