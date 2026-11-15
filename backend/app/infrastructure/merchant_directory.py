"""Built-in merchant directory consumed by :class:`MerchantRuleHandler`.

Keys are canonical merchant names; aliases are how they appear on bank
statements. This is configuration data, injected in the composition root.
"""

from app.domain.categorization import MerchantProfile

DEFAULT_MERCHANTS: dict[str, MerchantProfile] = {
    "Amazon": MerchantProfile("Shopping", ("amazon", "amzn", "amzn mktp")),
    "Flipkart": MerchantProfile("Shopping", ("flipkart", "fkrt")),
    "Myntra": MerchantProfile("Shopping", ("myntra",)),
    "IKEA": MerchantProfile("Shopping", ("ikea",)),
    "Swiggy": MerchantProfile("Food & Dining", ("swiggy", "swgy", "instamart")),
    "Zomato": MerchantProfile("Food & Dining", ("zomato", "zmt", "blinkit")),
    "Starbucks": MerchantProfile("Food & Dining", ("starbucks", "sbux")),
    "BigBasket": MerchantProfile("Food & Dining", ("bigbasket", "bbnow")),
    "Domino's": MerchantProfile("Food & Dining", ("dominos", "domino's")),
    "IRCTC": MerchantProfile("Transport", ("irctc",)),
    "IndiGo": MerchantProfile("Transport", ("indigo",)),
    "Indian Oil": MerchantProfile("Transport", ("iocl", "indian oil", "hpcl", "bpcl")),
    "BookMyShow": MerchantProfile("Entertainment", ("bookmyshow", "bms")),
    "PVR INOX": MerchantProfile("Entertainment", ("pvr", "inox")),
    "Steam": MerchantProfile("Entertainment", ("steam", "steampowered")),
    "Apollo Pharmacy": MerchantProfile("Health", ("apollo",)),
    "PharmEasy": MerchantProfile("Health", ("pharmeasy",)),
    "Tata 1mg": MerchantProfile("Health", ("1mg",)),
    "Airtel": MerchantProfile("Utilities", ("airtel",)),
    "Jio": MerchantProfile("Utilities", ("jio", "reliance jio")),
    "BESCOM": MerchantProfile("Utilities", ("bescom", "tata power", "adani electricity")),
    "YouTube Premium": MerchantProfile("Subscriptions", ("youtube premium", "yt premium")),
    "Prime Video": MerchantProfile("Subscriptions", ("prime video", "amazon prime")),
    "JioHotstar": MerchantProfile("Subscriptions", ("hotstar", "jiohotstar")),
    "Apple": MerchantProfile("Subscriptions", ("apple.com/bill", "icloud")),
}
