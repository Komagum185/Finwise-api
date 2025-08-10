# Registration Approval Workflow API Documentation

This document describes the new registration approval workflow and OTP verification system implemented in the Finwise API.

## Overview

The registration approval workflow allows administrators to review and approve/reject user registrations before they become active users. The system includes OTP verification for email verification and password setup.

## New Endpoints

### 1. Register with Approval

**Endpoint:** `POST /api/auth/register-with-approval/`

**Description:** Creates a pending registration that requires admin approval.

**Request Body:**

```json
{
    "username": "newuser123",
    "email": "newuser123@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "date_of_birth": "1990-01-01",
    "default_currency": "USD",
    "monthly_income": "5000.00"
}
```

**Response (201 Created):**

```json
{
    "message": "Registration submitted for approval. Please verify your email with the OTP sent.",
    "registration_id": "uuid-here",
    "otp_sent": true
}
```

**Notes:**

- An OTP is automatically generated and sent to the user's email
- The registration status is set to "pending"
- User must verify OTP before admin can approve

### 2. View Pending Registrations (Admin Only)

**Endpoint:** `GET /api/auth/pending-registrations/`

**Description:** Retrieves all pending registrations for admin review.

**Query Parameters:**

- `status`: Filter by status (pending, approved, rejected) - defaults to "pending"

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Response (200 OK):**

```json
[
    {
        "id": "uuid-here",
        "username": "newuser123",
        "email": "newuser123@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "date_of_birth": "1990-01-01",
        "default_currency": "USD",
        "monthly_income": "5000.00",
        "status": "pending",
        "submitted_at": "2024-01-15T10:30:00Z",
        "reviewed_at": null,
        "reviewed_by": null,
        "reviewed_by_name": null,
        "rejection_reason": "",
        "otp_verified": true
    }
]
```

### 3. Approve Registration (Admin Only)

**Endpoint:** `POST /api/auth/pending-registrations/{registration_id}/approve/`

**Description:** Approves a pending registration and creates an active user account.

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Response (200 OK):**

```json
{
    "message": "Registration approved successfully",
    "user_id": "user-uuid-here",
    "otp_id": "otp-uuid-here"
}
```

**Notes:**

- Only registrations with verified OTP can be approved
- Creates a new user account with `is_active=False`
- Sends a password setup OTP to the user's email
- User must set their password using the OTP before they can log in

### 4. Reject Registration (Admin Only)

**Endpoint:** `POST /api/auth/pending-registrations/{registration_id}/reject/`

**Description:** Rejects a pending registration.

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Request Body:**

```json
{
    "rejection_reason": "Incomplete information provided"
}
```

**Response (200 OK):**

```json
{
    "message": "Registration rejected successfully",
    "rejection_reason": "Incomplete information provided"
}
```

**Notes:**

- Sends rejection email to the user
- Registration status is set to "rejected"

### 5. Verify OTP

**Endpoint:** `POST /api/auth/verify-otp/`

**Description:** Verifies OTP for various purposes (registration, password reset, etc.).

**Request Body for Registration Verification:**

```json
{
    "otp_code": "123456",
    "purpose": "email_verification",
    "registration_id": "registration-uuid-here"
}
```

**Request Body for Password Reset:**

```json
{
    "otp_code": "123456",
    "purpose": "password_reset",
    "user_id": "user-uuid-here",
    "new_password": "NewSecurePass123!"
}
```

**Request Body for Phone Verification:**

```json
{
    "otp_code": "123456",
    "purpose": "phone_verification",
    "user_id": "user-uuid-here"
}
```

**Response (200 OK):**

```json
{
    "message": "OTP verified successfully",
    "registration_id": "registration-uuid-here"
}
```

**Notes:**

- OTP expires after 15 minutes
- Each OTP can only be used once
- For password reset, the new password is optional in the request (can be set separately)

### 6. Resend OTP

**Endpoint:** `POST /api/auth/resend-otp/`

**Description:** Resends OTP for various purposes.

**Request Body for Registration:**

```json
{
    "purpose": "email_verification",
    "registration_id": "registration-uuid-here"
}
```

**Request Body for User:**

```json
{
    "purpose": "password_reset",
    "user_id": "user-uuid-here"
}
```

**Response (200 OK):**

```json
{
    "message": "OTP sent successfully",
    "registration_id": "registration-uuid-here"
}
```

## Workflow Steps

### For New Users

1. **User Registration**: User submits registration via `/api/auth/register-with-approval/`
2. **OTP Verification**: User receives OTP via email and verifies it via `/api/auth/verify-otp/`
3. **Admin Review**: Admin views pending registrations via `/api/auth/pending-registrations/`
4. **Admin Decision**: Admin approves or rejects via `/api/auth/pending-registrations/{id}/approve/` or `/api/auth/pending-registrations/{id}/reject/`
5. **Password Setup**: If approved, user receives password setup OTP and sets password
6. **Account Activation**: User can now log in with their credentials

### For Existing Users

1. **Request OTP**: User requests OTP for password reset or phone verification
2. **Receive OTP**: User receives OTP via email or SMS
3. **Verify OTP**: User verifies OTP and completes the action (password reset, etc.)

## Error Responses

### Common Error Codes

- **400 Bad Request**: Invalid data, OTP expired, or validation errors
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions (admin access required)
- **404 Not Found**: Registration or user not found
- **500 Internal Server Error**: Server-side errors

### Example Error Response

```json
{
    "error": "Invalid or expired OTP"
}
```

## Security Considerations

1. **OTP Expiration**: OTPs expire after 15 minutes
2. **Single Use**: Each OTP can only be used once
3. **Admin Only**: Approval/rejection endpoints require admin privileges
4. **Password Validation**: New passwords must meet Django's password validation requirements
5. **Email Verification**: Registration requires email verification before approval

## Testing

Use the provided `test_registration_workflow.py` script to test the complete workflow:

```bash
python test_registration_workflow.py
```

**Note**: OTP codes are logged to the console for testing purposes. In production, replace the utility functions in `users/utils.py` with actual email/SMS services.

## Integration Notes

1. **Email Service**: Replace `send_otp_email()` in `users/utils.py` with your email service (SendGrid, AWS SES, etc.)
2. **SMS Service**: Replace `send_otp_sms()` in `users/utils.py` with your SMS service (Twilio, AWS SNS, etc.)
3. **Admin Interface**: Consider building a web interface for admins to manage pending registrations
4. **Notifications**: Implement real-time notifications for new pending registrations

## Database Models

### PendingRegistration

- Stores pending registrations with status tracking
- Includes OTP verification for email confirmation
- Links to admin who reviewed the registration

### OTPVerification

- Manages OTP codes for various purposes
- Handles expiration and single-use validation
- Supports multiple verification purposes

## Migration

The new models are automatically created when you run:

```bash
python manage.py migrate
```

This creates the necessary database tables for the registration approval workflow.
