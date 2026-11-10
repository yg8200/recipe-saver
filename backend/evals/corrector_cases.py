"""Hand-written Hebrew recipes for measuring the OCR-correction guardrail.

Each case has the text as an OCR engine might return it ("ocr") and the text it should end up as
("gold"). Typos are the visually-similar-letter mistakes OCR really makes (ר/ד, ח/ה, ם/ס, ח/ת...).
Cases whose ocr == gold check that a correct recipe is left alone.
The examples here are deliberately different from the ones shown to the model in its prompt.
"""

PIZZA_GOLD = {
    "title": "בצק פיצה ביתי",
    "ingredients": ["3 כוסות קמח", "1 כף שמרים יבשים", "1 כפית מלח", "1 כוס מים פושרים", "2 כפות שמן זית"],
    "instructions": [
        "1. מערבבים את הקמח והמלח בקערה",
        "2. מוסיפים את המים והשמן ולשים עשר דקות",
        "3. מכסים ומשאירים להתפחה לשעה",
        "4. משטחים ואופים בתנור חם",
    ],
}
PIZZA_OCR = {
    "title": "בצק פיצה ביתי",
    "ingredients": ["3 כוסות קמה", "1 כף שמרים יבשים", "1 כפית מלח", "1 כוס מים פושדים", "2 כפות שמן זית"],
    "instructions": [
        "1. מערבבים את הקמח והמלח בקערה",
        "2. מוסיפים את המים והשמן ולשיס עשר דקות",
        "3. מכסים ומשאירים להתפתה לשעה",
        "4. משטחים ואופים בתנור חם",
    ],
}

CHEESECAKE_GOLD = {
    "title": "עוגת גבינה אפויה",
    "ingredients": [
        "--- לבסיס ---", "200 גרם ביסקוויטים טחונים", "100 גרם חמאה מומסת",
        "--- למילוי ---", "500 גרם גבינת שמנת", "3 ביצים", "1/2 כוס סוכר", "1 כפית תמצית וניל",
    ],
    "instructions": [
        "--- הבסיס ---",
        "1. מערבבים את הביסקוויטים עם החמאה ומהדקים בתבנית",
        "--- המילוי ---",
        "2. מקציפים את הגבינה עם הסוכר והביצים",
        "3. יוצקים על הבסיס ואופים 45 דקות ב-160 מעלות",
    ],
}
CHEESECAKE_OCR = {
    **CHEESECAKE_GOLD,
    "instructions": [
        "--- הבסיס ---",
        "1. מערבבים את הביסקוויטים עם החמאה ומהדקים בתבנית",
        "--- המילוי ---",
        "2. מקציפים את הגבינה עם הסוכד והביצים",
        "3. יוצקים על הבסיס ואופים 45 דקות ב-160 מעלות",
    ],
}

# Uncommon but valid words, fractions and decimals. Nothing here should be touched.
UNUSUAL_GOLD = {
    "title": "חריימה של סבתא",
    "ingredients": ["1 ק״ג דג נסיכת הנילוס", "3.5 כוסות מים", "1/2 כוס שמן", "5 שיני שום כתושות", "1 כפית כורכום", "פפריקה חריפה"],
    "instructions": [
        "1. מטגנים את השום בשמן עד להזהבה",
        "2. מוסיפים תבלינים ומים ומביאים לרתיחה",
        "3. מכניסים את הדג ומבשלים 20 דקות",
    ],
}

# Correct but casual, vague home-cooking Hebrew. An overeager editor "improves" these by adding
# quantities, reordering words or rewriting; none of it should change.
CASUAL_GOLD = {
    "title": "פשטידת ירקות",
    "ingredients": ["קצת מלח ופלפל", "כמה שצריך מים", "2-3 גזרים", "בצל אחד גדול", "גבינה צהובה לפי הטעם", "מעט שמן"],
    "instructions": [
        "1. חותכים את הירקות לקוביות קטנות",
        "2. מטגנים קצת עד שמתרכך",
        "3. מוסיפים ביצים ומערבבים",
        "4. שמים בתנור עד שמוכן",
    ],
}

# Two typos next to short lines that are fine as they are and must not be expanded.
TERSE_GOLD = {
    "title": "סלט טחינה",
    "ingredients": ["טחינה גולמית", "מיץ לימון", "שן שום", "מלח", "מים קרים"],
    "instructions": ["1. מערבבים הכל", "2. מוסיפים מים עד לקבלת מרקם חלק", "3. מגישים עם פיתה חמה"],
}
TERSE_OCR = {
    **TERSE_GOLD,
    "ingredients": ["טחינה גולמית", "מיץ לימון", "שן שוס", "מלח", "מים קרים"],
    "instructions": ["1. מערבבים הכל", "2. מוסיפים מים עד לקבלת מרקס חלק", "3. מגישים עם פיתה חמה"],
}

# Title is the name of a website, not a dish.
JUNK_TITLE_OCR = {
    "title": "אתר המתכונים של דנה",
    "ingredients": ["4 תפוחי אדמה", "2 כפות שמן", "מלח ופלפל"],
    "instructions": ["1. חותכים את תפוחי האדמה לפרוסות", "2. מתבלים ואופים 40 דקות"],
}

# (name, ocr_recipe, gold_recipe)
CASES = [
    ("4 typos in ingredients and steps", PIZZA_OCR, PIZZA_GOLD),
    ("section headers + 1 typo", CHEESECAKE_OCR, CHEESECAKE_GOLD),
    ("2 typos among terse lines", TERSE_OCR, TERSE_GOLD),
    ("correct: unusual words and numbers", UNUSUAL_GOLD, UNUSUAL_GOLD),
    ("correct: casual vague wording", CASUAL_GOLD, CASUAL_GOLD),
    ("correct: plain recipe", PIZZA_GOLD, PIZZA_GOLD),
]
