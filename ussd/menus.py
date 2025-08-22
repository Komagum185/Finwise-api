# menu.py

# Welcome menu
WELCOME_MENU = {
    'welcome_to_finwise': {
        'text': '{header}\n1. Individual\n2. Organisation\n0. Back',
        'callback': 'continue_menu'
    }
}

# Main user menu
USER_MENU = {
    'menu_0_0': {
        'text': 'Welcome {name}!\n1. Wallet\n2. Products\n3. Loans\n4. Contacts\n0. Exit',
        'callback': 'main_menu'
    },
    'menu_wallet': {
        'text': 'Wallet Menu:\n1. Deposit\n2. Withdraw\n3. Check Balance\n0. Back',
        'callback': 'wallet_menu'
    },
    'menu_loans': {
        'text': 'Loans Menu:\n1. Request Loan\n2. Repay Loan\n3. Loan Status\n0. Back',
        'callback': 'loan_menu'
    },
    'menu_products': {
        'text': 'Products Menu:\n1. List Products\n2. Buy Product\n0. Back',
        'callback': 'product_menu'
    },
    'menu_contacts': {
        'text': 'Contacts Menu:\n1. Customers\n2. Suppliers\n0. Back',
        'callback': 'contact_menu'
    }
}

# Merge WELCOME_MENU into USER_MENU if you want a single dict
MENUS = {**WELCOME_MENU, **USER_MENU}
