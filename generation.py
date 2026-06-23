#
# Used to represent people generation
#
from datetime import datetime
GENERATION_TO_YEAR = {
    "Elders": 1960,
    "1970s": 1979,
    "1980s": 1989,
    "1990s": 1999,
    "2000s": 2009,
    "2010s": 2019,
    "Adults": ( datetime.now().year ) - 18,
    "Teenagers": ( datetime.now().year ) - 13,
    "Youngers": ( ( datetime.now().year // 10 ) * 10 ) + 9
}
