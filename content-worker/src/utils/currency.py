"""
Currency conversion utilities using Exchange Rate API.

API: https://www.exchangerate-api.com/
Key: 04a70949baa5efdd987cd84f

Default display order:
1. USD (global default)
2. GBP (secondary)
3. EUR (European context)
4. Local currency (destination country)
5. Home currency (for nationality-specific callouts)
"""

import os
import httpx
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import asyncio

# Exchange Rate API configuration
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "04a70949baa5efdd987cd84f")
EXCHANGE_RATE_API_BASE = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}"

# Country to currency code mapping
COUNTRY_CURRENCIES = {
    # Europe
    'portugal': 'EUR', 'spain': 'EUR', 'france': 'EUR', 'germany': 'EUR',
    'italy': 'EUR', 'greece': 'EUR', 'netherlands': 'EUR', 'belgium': 'EUR',
    'austria': 'EUR', 'ireland': 'EUR', 'finland': 'EUR', 'slovakia': 'EUR',
    'slovenia': 'EUR', 'estonia': 'EUR', 'latvia': 'EUR', 'lithuania': 'EUR',
    'malta': 'EUR', 'cyprus': 'EUR', 'luxembourg': 'EUR', 'montenegro': 'EUR',
    # Non-Euro Europe
    'uk': 'GBP', 'united kingdom': 'GBP', 'england': 'GBP',
    'switzerland': 'CHF', 'norway': 'NOK', 'sweden': 'SEK', 'denmark': 'DKK',
    'poland': 'PLN', 'czechia': 'CZK', 'czech republic': 'CZK',
    'hungary': 'HUF', 'romania': 'RON', 'bulgaria': 'BGN', 'croatia': 'EUR',
    'iceland': 'ISK', 'turkey': 'TRY',
    # Asia
    'japan': 'JPY', 'south korea': 'KRW', 'china': 'CNY',
    'thailand': 'THB', 'vietnam': 'VND', 'indonesia': 'IDR', 'bali': 'IDR',
    'malaysia': 'MYR', 'singapore': 'SGD', 'philippines': 'PHP',
    'india': 'INR', 'pakistan': 'PKR', 'bangladesh': 'BDT',
    'sri lanka': 'LKR', 'nepal': 'NPR', 'cambodia': 'KHR',
    'taiwan': 'TWD', 'hong kong': 'HKD',
    # Middle East
    'uae': 'AED', 'dubai': 'AED', 'saudi arabia': 'SAR',
    'qatar': 'QAR', 'bahrain': 'BHD', 'oman': 'OMR',
    'kuwait': 'KWD', 'israel': 'ILS', 'jordan': 'JOD',
    # Americas
    'usa': 'USD', 'canada': 'CAD', 'mexico': 'MXN',
    'brazil': 'BRL', 'argentina': 'ARS', 'colombia': 'COP',
    'chile': 'CLP', 'peru': 'PEN', 'costa rica': 'CRC',
    'panama': 'USD', 'ecuador': 'USD',
    # Oceania
    'australia': 'AUD', 'new zealand': 'NZD', 'fiji': 'FJD',
    # Africa
    'south africa': 'ZAR', 'egypt': 'EGP', 'morocco': 'MAD',
    'kenya': 'KES', 'nigeria': 'NGN', 'ghana': 'GHS',
    'mauritius': 'MUR',
}

# Nationality to home currency (for callout sections)
NATIONALITY_HOME_CURRENCIES = {
    'us': 'USD', 'american': 'USD', 'usa': 'USD',
    'uk': 'GBP', 'british': 'GBP', 'english': 'GBP',
    'indian': 'INR', 'india': 'INR',
    'pakistani': 'PKR', 'pakistan': 'PKR',
    'bangladeshi': 'BDT', 'bangladesh': 'BDT',
    'singaporean': 'SGD', 'singapore': 'SGD',
    'malaysian': 'MYR', 'malaysia': 'MYR',
    'filipino': 'PHP', 'philippine': 'PHP', 'philippines': 'PHP',
    'australian': 'AUD', 'australia': 'AUD',
    'canadian': 'CAD', 'canada': 'CAD',
    'south african': 'ZAR', 'south africa': 'ZAR',
    'irish': 'EUR', 'ireland': 'EUR',
    'german': 'EUR', 'germany': 'EUR',
    'french': 'EUR', 'france': 'EUR',
    'dutch': 'EUR', 'netherlands': 'EUR',
    'emirati': 'AED', 'uae': 'AED',
    'chinese': 'CNY', 'china': 'CNY',
    'japanese': 'JPY', 'japan': 'JPY',
    'korean': 'KRW', 'south korea': 'KRW',
    'thai': 'THB', 'thailand': 'THB',
    'vietnamese': 'VND', 'vietnam': 'VND',
    'indonesian': 'IDR', 'indonesia': 'IDR',
    'new zealander': 'NZD', 'kiwi': 'NZD', 'new zealand': 'NZD',
}

# Currency symbols for display
CURRENCY_SYMBOLS = {
    'USD': '$', 'GBP': '£', 'EUR': '€', 'INR': '₹',
    'AUD': 'A$', 'CAD': 'C$', 'SGD': 'S$', 'HKD': 'HK$',
    'JPY': '¥', 'CNY': '¥', 'KRW': '₩', 'THB': '฿',
    'PHP': '₱', 'MYR': 'RM', 'IDR': 'Rp', 'VND': '₫',
    'PKR': '₨', 'BDT': '৳', 'LKR': 'Rs', 'NPR': 'Rs',
    'AED': 'د.إ', 'SAR': '﷼', 'QAR': '﷼',
    'CHF': 'CHF', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr',
    'PLN': 'zł', 'CZK': 'Kč', 'HUF': 'Ft', 'RON': 'lei',
    'ZAR': 'R', 'BRL': 'R$', 'MXN': 'MX$', 'COP': 'COL$',
}


def get_country_currency(country_name: str) -> str:
    """Get the local currency code for a country."""
    return COUNTRY_CURRENCIES.get(country_name.lower().strip(), 'EUR')


def get_nationality_currency(nationality: str) -> str:
    """Get the home currency for a nationality (for callout sections)."""
    return NATIONALITY_HOME_CURRENCIES.get(nationality.lower().strip(), 'USD')


def get_currency_symbol(currency_code: str) -> str:
    """Get the display symbol for a currency."""
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)


@lru_cache(maxsize=50)
def _fetch_rates_sync(base_currency: str) -> Dict[str, float]:
    """Fetch exchange rates synchronously (cached)."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{EXCHANGE_RATE_API_BASE}/latest/{base_currency}")
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    return data.get("conversion_rates", {})
    except Exception as e:
        print(f"Exchange rate API error: {e}")
    return {}


async def fetch_exchange_rates(base_currency: str = "USD") -> Dict[str, float]:
    """
    Fetch current exchange rates from the API.

    Args:
        base_currency: Base currency code (default USD)

    Returns:
        Dict mapping currency codes to exchange rates
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{EXCHANGE_RATE_API_BASE}/latest/{base_currency}")
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    return data.get("conversion_rates", {})
    except Exception as e:
        print(f"Exchange rate API error: {e}")
    return {}


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: Optional[Dict[str, float]] = None
) -> Optional[float]:
    """
    Convert an amount from one currency to another.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        rates: Pre-fetched rates (optional, will fetch if not provided)

    Returns:
        Converted amount or None if conversion fails
    """
    if from_currency.upper() == to_currency.upper():
        return amount

    if rates is None:
        rates = _fetch_rates_sync(from_currency.upper())

    if not rates:
        return None

    # If rates are based on from_currency, direct lookup
    if to_currency.upper() in rates:
        return amount * rates[to_currency.upper()]

    return None


def format_multi_currency(
    amount_usd: float,
    country_name: str,
    nationality: Optional[str] = None,
    rates: Optional[Dict[str, float]] = None
) -> str:
    """
    Format an amount in multiple currencies for display.

    Order: USD (default) | GBP | EUR | Local | Home (if nationality specified)

    Args:
        amount_usd: Amount in USD
        country_name: Destination country (for local currency)
        nationality: Reader's nationality (for home currency callout)
        rates: Pre-fetched rates

    Returns:
        Formatted string like "$1,500 (£1,180 / €1,380 / €1,380 local)"
    """
    if rates is None:
        rates = _fetch_rates_sync("USD")

    parts = [f"${amount_usd:,.0f}"]

    # Add GBP
    if "GBP" in rates:
        gbp = amount_usd * rates["GBP"]
        parts.append(f"£{gbp:,.0f}")

    # Add EUR
    if "EUR" in rates:
        eur = amount_usd * rates["EUR"]
        parts.append(f"€{eur:,.0f}")

    # Add local currency if different from EUR/GBP/USD
    local_currency = get_country_currency(country_name)
    if local_currency not in ["USD", "GBP", "EUR"] and local_currency in rates:
        local_amount = amount_usd * rates[local_currency]
        symbol = get_currency_symbol(local_currency)
        parts.append(f"{symbol}{local_amount:,.0f}")

    # Add home currency for nationality if specified and different
    if nationality:
        home_currency = get_nationality_currency(nationality)
        if home_currency not in ["USD", "GBP", "EUR", local_currency] and home_currency in rates:
            home_amount = amount_usd * rates[home_currency]
            symbol = get_currency_symbol(home_currency)
            parts.append(f"{symbol}{home_amount:,.0f}")

    return " / ".join(parts)


def get_currency_display_guidance(country_name: str) -> str:
    """
    Get prompt guidance for displaying costs in multiple currencies.

    Args:
        country_name: Destination country

    Returns:
        String with currency display instructions for prompts
    """
    local_currency = get_country_currency(country_name)
    local_symbol = get_currency_symbol(local_currency)

    guidance = f"""
===== CURRENCY DISPLAY (CRITICAL FOR INTERNATIONAL READERS) =====
Display ALL costs in MULTIPLE currencies for global accessibility:

**Default Display Order:**
1. **USD** ($) - Global default, understood worldwide
2. **GBP** (£) - Secondary, large expat source
3. **EUR** (€) - European context
4. **{local_currency}** ({local_symbol}) - Local currency for {country_name}

**For Nationality-Specific Callouts:**
- 📍 For Indian readers: Also show INR (₹)
- 📍 For Pakistani readers: Also show PKR (₨)
- 📍 For Singaporean readers: Also show SGD (S$)
- 📍 For Filipino readers: Also show PHP (₱)
- 📍 For Australian readers: Also show AUD (A$)

**Example Format:**
"Monthly rent: $1,500 / £1,180 / €1,380 / {local_symbol}X,XXX"
"For Indian nationals: ₹125,000/month equivalent"

Use real-time or recent exchange rates. When in doubt, use approximate conversions.
This helps readers from ANY country understand costs in familiar terms.
"""
    return guidance
