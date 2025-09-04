from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import MSECategory, MSE, Wallet
from .serializers import MSECategorySerializer, MSESerializer, WalletSerializer


class MSECategoryViewSet(viewsets.ModelViewSet):
    queryset = MSECategory.objects.all()
    serializer_class = MSECategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class MSEViewSet(viewsets.ModelViewSet):
    queryset = MSE.objects.all()
    serializer_class = MSESerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated users can see all MSEs
        return super().get_queryset()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        mse = self.get_object()
        mse.status = 'approved'
        mse.save(update_fields=['status'])
        return Response({'detail': 'MSE approved'}, status=200)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        mse = self.get_object()
        mse.status = 'rejected'
        mse.save(update_fields=['status'])
        return Response({'detail': 'MSE rejected'}, status=200)

    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        mse = self.get_object()
        with transaction.atomic():
            wallet = mse.wallet
            wallet.balance = wallet.balance + amount
            wallet.save(update_fields=['balance'])
        return Response({'detail': 'Deposit successful', 'balance': wallet.balance}, status=200)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        mse = self.get_object()
        with transaction.atomic():
            wallet = mse.wallet
            if wallet.balance < amount:
                return Response({'detail': 'Insufficient balance'}, status=400)
            wallet.balance = wallet.balance - amount
            wallet.save(update_fields=['balance'])
        return Response({'detail': 'Withdrawal successful', 'balance': wallet.balance}, status=200)


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated users can see all wallets
        return super().get_queryset()


class SelfRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # email optional; accept local 07… phones and normalize
        required_fields = ['username', 'first_name', 'last_name', 'nin', 'phone', 'category']
        errors = {}
        for f in required_fields:
            if not request.data.get(f):
                errors[f] = 'This field is required.'

        # Basic phone normalization/validation
        raw_phone = (request.data.get('phone') or '').strip()
        normalized_phone = raw_phone
        if raw_phone.startswith('07') and len(raw_phone) == 10:
            normalized_phone = '+256' + raw_phone[1:]
        elif raw_phone.startswith('+256') and len(raw_phone) == 13:
            normalized_phone = raw_phone
        elif raw_phone.startswith('256') and len(raw_phone) == 12:
            normalized_phone = '+' + raw_phone
        else:
            if 'phone' not in errors:
                errors['phone'] = 'Enter a valid phone. Accepted: 07xxxxxxxx, +256xxxxxxxxx, or 256xxxxxxxxx.'

        # Category validation (case-insensitive)
        raw_category = (request.data.get('category') or '').strip().lower()
        if not raw_category:
            errors['category'] = 'This field is required.'
        else:
            allowed_categories = {'input', 'producer', 'output'}
            if raw_category not in allowed_categories:
                errors['category'] = 'Invalid category. Use one of: input, producer, output'

        User = get_user_model()
        username = request.data.get('username') or ''
        if not username:
            # Auto-generate username if missing: first.last.last4phone
            first = (request.data.get('first_name') or 'user').strip().lower()
            last = (request.data.get('last_name') or 'mse').strip().lower()
            tail = normalized_phone[-4:] if normalized_phone and normalized_phone[-4:].isdigit() else '0000'
            base = f"{first}.{last}.{tail}"
            candidate = base
            suffix = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base}{suffix}"
                suffix += 1
            username = candidate
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists.'

        if errors:
            return Response({'errors': errors}, status=400)

        # Ensure category exists (bootstrap if missing)
        category, _ = MSECategory.objects.get_or_create(name=raw_category, defaults={'description': raw_category.title()})

        temp_password = User.objects.make_random_password()

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=request.data.get('email', ''),
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                phone_number=normalized_phone,
                NIN=request.data.get('nin', ''),
                role='mse',
                is_approved=False,
                password=temp_password,
            )

            mse = MSE.objects.create(
                owner=user,
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                nin=request.data.get('nin', ''),
                phone=normalized_phone,
                email=request.data.get('email', ''),
                category=category,
                location=request.data.get('location', ''),
                status='pending',
            )
            Wallet.objects.create(mse=mse)

        # TODO: send SMS with provisional login details
        return Response({
            'detail': 'Registration submitted. Await admin approval.',
            'username': user.username,
            'provisional_password': temp_password
        }, status=201)


