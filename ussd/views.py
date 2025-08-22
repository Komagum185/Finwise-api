from django.db import transaction
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import (
    USSDSession, USSDUser, Wallet, Transaction, Product, Loan,
    Contact, WalletAuditLog, USSDMenu
)

User = get_user_model()


class USSDAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        msisdn = request.data.get('msisdn') or ''
        session_id = request.data.get('sessionId') or ''
        text = (request.data.get('text') or '').strip()

        if not msisdn or not session_id:
            return Response('END Invalid request', status=status.HTTP_400_BAD_REQUEST)

        # Get or create session
        session, _ = USSDSession.objects.get_or_create(
            msisdn=msisdn,
            session_id=session_id,
            defaults={'current_step': 'login'}
        )

        # Check timeout
        if session.has_timed_out():
            session.is_active = False
            session.save(update_fields=['is_active'])
            return Response('END Session timed out. Please dial again.', status=status.HTTP_200_OK)

        inputs = [i for i in text.split('*') if i]

        # ------------------------------
        # Login step
        # ------------------------------
        if session.current_step == 'login':
            if not inputs:
                return Response('CON Welcome to FinWise\nEnter PIN:', status=status.HTTP_200_OK)
            
            pin = inputs[0]
            try:
                main_user = User.objects.get(
                    phone_number=msisdn,
                    is_active=True,
                    status='active',
                    ussd_enabled=True
                )
            except User.DoesNotExist:
                return Response('END Phone not registered. Please contact support.', status=status.HTTP_200_OK)

            # First-time USSD PIN setup
            if not main_user.ussd_pin_hash:
                main_user.ussd_pin_hash = make_password(pin)
                main_user.save(update_fields=['ussd_pin_hash'])
                ussd_user, created = USSDUser.objects.get_or_create(
                    phone=msisdn,
                    defaults={'name': main_user.get_full_name() or main_user.username,
                              'pin_hash': main_user.ussd_pin_hash}
                )
                Wallet.objects.get_or_create(owner=ussd_user)
                session.current_step = 'menu'
                session.state_data = {'user_id': ussd_user.id, 'main_user_id': main_user.id}
                session.save(update_fields=['current_step', 'state_data'])
                return Response(self.get_menu_response(), status=status.HTTP_200_OK)

            # Verify PIN
            if not check_password(pin, main_user.ussd_pin_hash):
                return Response('END Invalid PIN', status=status.HTTP_200_OK)

            # Get or create USSD user
            ussd_user, _ = USSDUser.objects.get_or_create(
                phone=msisdn,
                defaults={'name': main_user.get_full_name() or main_user.username,
                          'pin_hash': main_user.ussd_pin_hash}
            )
            Wallet.objects.get_or_create(owner=ussd_user)
            session.current_step = 'menu'
            session.state_data = {'user_id': ussd_user.id, 'main_user_id': main_user.id}
            session.save(update_fields=['current_step', 'state_data'])
            return Response(self.get_menu_response(), status=status.HTTP_200_OK)

        # ------------------------------
        # Authenticated step
        # ------------------------------
        ussd_user = USSDUser.objects.filter(id=session.state_data.get('user_id')).first()
        main_user = User.objects.filter(id=session.state_data.get('main_user_id')).first()
        if not ussd_user or not main_user:
            session.current_step = 'login'
            session.state_data = {}
            session.save(update_fields=['current_step', 'state_data'])
            return Response('END Session error. Please dial again.', status=status.HTTP_200_OK)

        # Determine the current menu
        parent_menu_code = '*'.join(inputs[:-1]) if len(inputs) > 1 else None
        current_choice = inputs[-1]

        menu_qs = USSDMenu.objects.filter(parent__code=parent_menu_code).order_by('order')
        menu_item = menu_qs.filter(code=current_choice).first()

        if not menu_item:
            return Response(self.get_menu_response(parent_menu_code), status=status.HTTP_200_OK)

        # Terminal actions
        if menu_item.is_terminal:
            action_name = menu_item.action
            response_text = self.execute_action(action_name, inputs, session, ussd_user)
            return Response(response_text, status=status.HTTP_200_OK)

        # Non-terminal: display submenu
        return Response(self.get_menu_response(menu_item.code), status=status.HTTP_200_OK)

    # ------------------------------
    # Helpers
    # ------------------------------
    def get_menu_response(self, parent_code=None):
        menus = USSDMenu.objects.filter(parent__code=parent_code).order_by('order')
        if not menus.exists():
            return 'END No options available'
        lines = ['CON ' + (menus.first().parent.title if parent_code else 'Select option:')]
        for m in menus:
            lines.append(f"{m.code}. {m.title}")
        return '\n'.join(lines)

    def execute_action(self, action_name, inputs, session, ussd_user):
        wallet, _ = Wallet.objects.get_or_create(owner=ussd_user)

        try:
            if action_name == 'balance':
                return f'END Your balance: {wallet.balance}'

            elif action_name == 'deposit':
                if len(inputs) < 2:
                    return 'CON Enter amount to deposit:'
                amount_val = Decimal(inputs[-1])
                with transaction.atomic():
                    before = wallet.balance
                    wallet.balance += amount_val
                    wallet.save(update_fields=['balance'])
                    Transaction.objects.create(wallet=wallet, amount=amount_val, type='deposit', status='completed')
                    WalletAuditLog.objects.create(wallet=wallet, action='deposit', amount=amount_val,
                                                balance_before=before, balance_after=wallet.balance)
                return 'END Deposit successful'

            elif action_name == 'withdraw':
                if len(inputs) < 2:
                    return 'CON Enter amount to withdraw:'
                amount_val = Decimal(inputs[-1])
                if wallet.balance < amount_val:
                    return 'END Insufficient balance'
                with transaction.atomic():
                    before = wallet.balance
                    wallet.balance -= amount_val
                    wallet.save(update_fields=['balance'])
                    Transaction.objects.create(wallet=wallet, amount=amount_val, type='withdrawal', status='completed')
                    WalletAuditLog.objects.create(wallet=wallet, action='withdrawal', amount=amount_val,
                                                balance_before=before, balance_after=wallet.balance)
                return 'END Withdrawal successful'

            elif action_name == 'buy_products':
                if len(inputs) < 2:
                    products = Product.objects.filter(stock__gt=0)[:5]
                    lines = ['CON Select product ID:']
                    for p in products:
                        lines.append(f"{p.id}:{p.name}-{p.price}")
                    return '\n'.join(lines)
                elif len(inputs) == 2:
                    session.state_data['product_id'] = inputs[-1]
                    session.save(update_fields=['state_data'])
                    return 'CON Enter quantity:'
                else:
                    product_id = session.state_data.get('product_id')
                    qty = int(inputs[-1])
                    product = Product.objects.filter(id=product_id).first()
                    if not product or qty <= 0:
                        return 'END Invalid product or quantity'
                    total = product.price * Decimal(qty)
                    if wallet.balance < total:
                        return 'END Insufficient balance'
                    with transaction.atomic():
                        before = wallet.balance
                        wallet.balance -= total
                        wallet.save(update_fields=['balance'])
                        product.stock = max(0, product.stock - qty)
                        product.save(update_fields=['stock'])
                        Transaction.objects.create(wallet=wallet, amount=total, type='purchase',
                                                reference=str(product.id), status='completed')
                        WalletAuditLog.objects.create(wallet=wallet, action='purchase', amount=total,
                                                    balance_before=before, balance_after=wallet.balance,
                                                    reference=str(product.id))
                    return 'END Purchase successful'

            elif action_name == 'request_loan':
                if len(inputs) < 2:
                    return 'CON Enter loan amount:'
                amount_val = Decimal(inputs[-1])
                Loan.objects.create(borrower=ussd_user, amount_requested=amount_val)
                return 'END Loan request submitted'

            elif action_name == 'contacts_add':
                if len(inputs) < 3:
                    return 'CON Enter contact name:'
                if len(inputs) < 4:
                    session.state_data['contact_name'] = inputs[-1]
                    session.save(update_fields=['state_data'])
                    return 'CON Enter contact phone:'
                name = session.state_data.get('contact_name')
                phone = inputs[-1]
                Contact.objects.create(owner=ussd_user, name=name, phone=phone)
                return 'END Contact added'

            elif action_name == 'contacts_view':
                contacts = Contact.objects.filter(owner=ussd_user)[:5]
                lines = ['END Contacts:'] + [f"{c.name}-{c.phone}" for c in contacts]
                return '\n'.join(lines)

            return 'END Action not implemented'
        except Exception as e:
            return f'END Error: {str(e)}'
