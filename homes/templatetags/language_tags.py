from django import template
from homes.utils import is_malayalam as is_ml_util

register = template.Library()

@register.filter
def is_legacy_malayalam(text):
    return is_ml_util(text)

@register.filter
def font_class(text):
    if is_legacy_malayalam(text):
        return "malayalam-text"
    return ""

@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0

@register.filter
def trans_finance(text, lang):
    if lang != 'ml':
        return text
    
    translations = {
        # Dashboard
        "Total Finance Overview": "ആകെ സാമ്പത്തിക വിവരം",
        "Total Income (Main Fund)": "ആകെ വരുമാനം (പ്രധാന ഫണ്ട്)",
        "Total Expense (Main Fund)": "ആകെ ചിലവ് (പ്രധാന ഫണ്ട്)",
        "Available Balance": "ബാക്കി തുക",
        "Recent Transactions (Main Fund)": "സമീപകാല ഇടപാടുകൾ",
        "Date": "തിയതി",
        "Type": "തരം",
        "Category": "വിഭാഗം",
        "Amount": "തുക",
        "Method": "രീതി",
        "From/To": "ആരിൽ നിന്ന്/ആർക്ക്",
        "Income": "വരുമാനം",
        "Expense": "ചിലവ്",
        "Fee Collection": "ഫീസുകൾ",
        
        # Fee Collection
        "Total Outstanding Dues": "ആകെ കിട്ടാനുള്ള ഫീസുകൾ",
        "Overall balance to be collected.": "ആകെ പിരിച്ചെടുക്കാനുള്ള തുക.",
        "Homes & Collections": "വീടുകളും കളക്ഷനും",
        "Home / Head": "വീട് / കാരണവർ",
        "House Name": "വീട്ടുപേര്",
        "Students": "വിദ്യാർത്ഥികൾ",
        "Advance Balance": "അഡ്വാൻസ് തുക",
        "Actions": "നടപടികൾ",
        "View Finance": "സാമ്പത്തിക വിവരം",
        "Latest Global Invoices": "ഏറ്റവും പുതിയ ഇൻവോയിസുകൾ",
        "Month": "മാസം",
        "Total": "ആകെ",
        "Paid": "അടച്ചത്",
        "Balance": "ബാക്കി",
        "Status": "സ്ഥിതി",
        "Due": "ബാക്കിയുണ്ട്",
        "Search ID, name, area, house...": "ID, പേര്, സ്ഥലം തിരയുക...",
        "Search": "തിരയുക",
        "Clear": "ഒഴിവാക്കുക",
        
        # Reports
        "Financial Reports": "സാമ്പത്തിക റിപ്പോർട്ടുകൾ",
        "Summary": "ചുരുക്കം",
        "Daily Accounts": "ദിവസേനയുള്ള കണക്ക്",
        "Monthly Accounts": "മാസേനയുള്ള കണക്ക്",
        "Item-wise Accounts": "വിഭാഗം തിരിച്ചുള്ള കണക്ക്",
        "Net Total": "മൊത്തം ബാക്കി",
        "Income Breakdown": "വരുമാന വിവരം",
        "Expense Breakdown": "ചിലവ് വിവരം",
        "Opening Balance": "തുടക്കത്തിലെ ബാക്കി",
        "Closing Balance": "അവസാനത്തെ ബാക്കി",
        "Monthly Net": "ഈ മാസത്തെ ബാക്കി",
        "Net Balance": "ആകെ ബാക്കി",
        "Transactions": "ഇടപാടുകൾ",
        "Remarks": "കുറിപ്പുകൾ",
        "Print Report": "റിപ്പോർട്ട് പ്രിന്റ് ചെയ്യുക",
        "Start Date": "തുടക്കം",
        "End Date": "അവസാനം",
        "All Categories": "എല്ലാ വിഭാഗങ്ങളും",
        "All Types": "എല്ലാ തരങ്ങളും",
        "Filter": "ഫിൽട്ടർ",
        
        # Detail & Collect
        "Individual Finance": "വ്യക്തിഗത കണക്ക്",
        "Current Wallet Balance": "നിലവിലെ വാലറ്റ് ബാലൻസ്",
        "Record Payment": "പണം രേഖപ്പെടുത്തുക",
        "Invoices & Dues": "ബില്ലുകളും കുടിശ്ശികകളും",
        "Title": "വിവരണം",
        "Record Collection": "കളക്ഷൻ രേഖപ്പെടുത്തുക",
        "Cancel": "റദ്ദാക്കുക",
        "Payment Method": "പണം നൽകുന്ന രീതി",
        "Date Received": "ലഭിച്ച തിയതി",
        "Amount to Pay (₹)": "അടയ്ക്കാനുള്ള തുക (₹)",
        "Full Due": "പൂർണ്ണമായ കുടിശ്ശിക",
        "Collect Money": "പണം വാങ്ങുക",
        "Title / Month": "വിവരണം / മാസം",
        "Total Amount": "ആകെ തുക",
        "Amount Paid": "അടച്ച തുക",
        "Partial": "ഭാഗികം",
        "Category Name": "വിഭാഗത്തിന്റെ പേര്",
        "By Category": "വിഭാഗം തിരിച്ചുള്ളത്",
        "Total Outstanding": "ആകെ ബാക്കിയുള്ളത്",
        "Wallet Balance": "വാലറ്റ് ബാക്കി",
        "Add Previous Balance": "പഴയ ബാക്കി ചേർക്കുക",
        "Total Monthly Income": "ഈ മാസത്തെ ആകെ വരുമാനം",
        "Total Monthly Expense": "ഈ മാസത്തെ ആകെ ചിലവ്",
        "Category / Program": "വിഭാഗം / പ്രോഗ്രാം",
    }
    
    return translations.get(text, text)
