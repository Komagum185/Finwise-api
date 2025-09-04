# 🔄 Flexible Role System for Finwise

## 🎯 Overview

The new flexible role system allows users to have **multiple roles simultaneously**, making login and permissions much easier and more realistic. Users are no longer restricted to a single role and can have various combinations of capabilities.

## 🔑 Key Changes

### **Before (Rigid System):**
- Users had **one role** (`super_admin`, `agent`, `mse`, `partner`)
- Users had **one rights level** (`viewer`, `editor`, `export`, `admin`)
- **No flexibility** - users couldn't be both agent and MSE

### **After (Flexible System):**
- Users can have **multiple roles** at the same time
- Users have **capabilities** (granular permissions)
- **Full flexibility** - users can be agent + MSE, super admin + agent, etc.

## 🏗️ New Model Structure

### **Role Fields (Boolean):**
```python
is_super_admin = models.BooleanField(default=False)  # Full system access
is_agent = models.BooleanField(default=False)        # Can manage assigned MSEs
is_mse = models.BooleanField(default=False)          # Micro/Small Enterprise user
is_partner = models.BooleanField(default=False)      # Partner institution user
```

### **Capabilities (JSON List):**
```python
capabilities = models.JSONField(default=list)  # List of user capabilities
```

## 🎭 Role Combinations Examples

### **1. Super Admin + Agent**
- **User:** `adminuser`
- **Roles:** `is_super_admin=True`, `is_agent=True`
- **Can:** Everything + manage assigned MSEs
- **Use Case:** System administrator who also manages specific MSEs

### **2. Agent + MSE**
- **User:** `john_farmer`
- **Roles:** `is_agent=True`, `is_mse=True`
- **Can:** Manage assigned users + access own MSE data
- **Use Case:** Farmer who also helps other farmers

### **3. Partner + MSE**
- **User:** `partner_mse_user`
- **Roles:** `is_partner=True`, `is_mse=True`
- **Can:** Access partner dashboard + own MSE data
- **Use Case:** Institution staff who also runs a business

### **4. Pure Partner**
- **User:** `partner_viewer`
- **Roles:** `is_partner=True`
- **Can:** Access partner dashboard only
- **Use Case:** Institution staff who only views reports

## 🔐 Capability System

### **Core Capabilities:**
```python
CAPABILITY_CHOICES = [
    'can_manage_users',           # Create/update/delete users
    'can_manage_mse',             # Manage MSE operations
    'can_view_reports',           # View system reports
    'can_export_data',            # Export data to files
    'can_approve_loans',          # Approve loan applications
    'can_manage_wallets',         # Manage wallet operations
    'can_access_partner_dashboard',   # Access partner dashboard
    'can_access_admin_dashboard',     # Access admin dashboard
    'can_access_agent_dashboard',     # Access agent dashboard
    'can_access_mse_dashboard',       # Access MSE dashboard
    # MSE Business Operations
    'can_manage_products',        # Manage own products
    'can_manage_inventory',       # Manage own inventory
    'can_manage_customers',       # Manage own customers
    'can_manage_suppliers',       # Manage own suppliers
    'can_manage_transactions',    # Manage own transactions
    'can_view_market_data',       # View market information
    'can_manage_loans',           # Manage own loans
    'can_manage_wallet',          # Manage own wallet
]
```

## 🏪 MSE Business Operations

### **Product Management:**
- **`can_manage_products`**: MSE users can create, update, and manage their own products
- **Access to:** `/api/markets/products/` (own products only)
- **Use Case:** Farmers managing their crop listings, traders managing product catalogs

### **Inventory Management:**
- **`can_manage_inventory`**: MSE users can track and manage their inventory levels
- **Access to:** `/api/inventory/items/` (own inventory only)
- **Use Case:** Tracking stock levels, managing product quantities, inventory movements

### **Customer Management:**
- **`can_manage_customers`**: MSE users can manage their customer relationships
- **Access to:** `/api/markets/customers/` (own customers only)
- **Use Case:** Managing customer lists, tracking sales, customer relationships

### **Supplier Management:**
- **`can_manage_suppliers`**: MSE users can manage their supplier relationships
- **Access to:** `/api/markets/suppliers/` (own suppliers only)
- **Use Case:** Managing supplier lists, tracking purchases, supplier relationships

### **Transaction Management:**
- **`can_manage_transactions`**: MSE users can manage their business transactions
- **Access to:** `/api/markets/transactions/` (own transactions only)
- **Use Case:** Tracking sales, purchases, payment records, business transactions

### **Market Data Access:**
- **`can_view_market_data`**: MSE users can view market information and trends
- **Access to:** Market reports, price trends, demand analysis
- **Use Case:** Making informed business decisions, understanding market conditions

### **Loan Management:**
- **`can_manage_loans`**: MSE users can manage their own loan applications and repayments
- **Access to:** `/api/loans/` (own loans only)
- **Use Case:** Tracking loan status, managing repayments, loan history

### **Wallet Management:**
- **`can_manage_wallet`**: MSE users can manage their financial transactions
- **Access to:** `/api/wallet/` (own wallet only)
- **Use Case:** Tracking income, expenses, balance management

## 🌐 Dashboard Access

### **Multiple Dashboard Access:**
Users can access **multiple dashboards** based on their roles:

```python
def get_accessible_dashboards(self):
    """Get list of dashboards user can access"""
    dashboards = []
    if self.can_access_dashboard('admin'):
        dashboards.append('admin')
    if self.can_access_dashboard('agent'):
        dashboards.append('agent')
    if self.can_access_dashboard('mse'):
        dashboards.append('mse')
    if self.can_access_dashboard('partner'):
        dashboards.append('partner')
    return dashboards
```

### **Example Dashboard Access:**
- **Super Admin + Agent:** `['admin', 'agent', 'mse', 'partner']`
- **Agent + MSE:** `['agent', 'mse']`
- **Partner + MSE:** `['partner', 'mse']`
- **Pure MSE:** `['mse']`

## 🚀 Benefits of New System

### **1. Realistic User Roles**
- Users can have multiple responsibilities
- No need to create duplicate accounts
- Reflects real-world organizational structures

### **2. Easier Login**
- Single login for multiple roles
- No role switching required
- Consistent user experience

### **3. Flexible Permissions**
- Granular capability control
- Easy to add new permissions
- Role-based capability inheritance

### **4. Better User Management**
- Agents can be MSEs too
- Super admins can have specific assignments
- Partners can run businesses

### **5. Complete Business Operations**
- MSE users can manage their entire business
- Access to markets, inventory, customers, suppliers
- Full business workflow support

## 🔄 Migration Process

### **Step 1: Run Migration Script**
```bash
python migrate_roles.py
```

### **Step 2: Verify Migration**
The script automatically verifies that all users are properly migrated.

### **Step 3: Test New System**
- Login with existing users
- Check dashboard access
- Verify capabilities

## 📱 API Changes

### **Login Response:**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "adminuser",
        "is_super_admin": true,
        "is_agent": true,
        "is_mse": false,
        "is_partner": false,
        "accessible_dashboards": ["admin", "agent", "mse", "partner"],
        "capabilities": ["can_manage_users", "can_manage_mse", ...],
        "has_multiple_roles": true,
        "primary_role": "super_admin"
    },
    "tokens": {
        "access": "...",
        "refresh": "..."
    }
}
```

### **Dashboard Data Endpoint:**
```json
GET /api/auth/dashboard-data/
{
    "user": {...},
    "accessible_dashboards": ["admin", "agent"],
    "capabilities": [...],
    "has_multiple_roles": true,
    "primary_role": "super_admin"
}
```

## 🎯 Use Cases

### **1. Multi-Role Super Admin**
- **Login:** Single account
- **Access:** All dashboards
- **Use Case:** System administrator who also manages specific areas

### **2. Agent + MSE**
- **Login:** Single account
- **Access:** Agent + MSE dashboards
- **Use Case:** Farmer who helps other farmers

### **3. Partner + MSE**
- **Login:** Single account
- **Access:** Partner + MSE dashboards
- **Use Case:** Institution staff who runs a business

### **4. Pure MSE**
- **Login:** Single account
- **Access:** MSE dashboard + business operations
- **Use Case:** Farmer managing crops, inventory, customers, and transactions

## 🔧 Technical Implementation

### **Model Methods:**
```python
# Check capabilities
user.has_capability('can_manage_users')
user.has_any_capability(['can_export_data', 'can_view_reports'])
user.has_all_capabilities(['can_view_reports', 'can_export_data'])

# Check dashboard access
user.can_access_dashboard('admin')
user.get_accessible_dashboards()

# Check role combinations
user.has_multiple_roles
user.primary_role

# Check MSE business operations
user.can_manage_own_products()
user.can_manage_own_inventory()
user.can_manage_own_customers()
user.can_manage_own_suppliers()
user.can_manage_own_transactions()
user.can_view_market_data()
user.can_manage_own_loans()
user.can_manage_own_wallet()
```

### **Permission Checking:**
```python
# Check if user can manage another user
user.can_manage_user(target_user)

# Check if user can view MSE data
user.can_view_mse_data(mse_user)

# Check if user can manage business operations
if user.can_manage_own_products():
    # Allow product management
if user.can_manage_own_inventory():
    # Allow inventory management
```

## 🚨 Important Notes

### **1. Backward Compatibility**
- Existing users are automatically migrated
- Old role fields are preserved during migration
- API responses include both old and new fields

### **2. Database Changes**
- New boolean role fields added
- New capabilities field added
- Existing data preserved

### **3. Permission Updates**
- All views updated to use new system
- Permissions based on capabilities, not roles
- Flexible access control

### **4. MSE Business Access**
- MSE users get full access to their business operations
- Products, inventory, customers, suppliers, transactions
- Market data and financial management

## 🎉 Summary

The new flexible role system provides:
- **Multiple roles per user**
- **Granular capabilities**
- **Multiple dashboard access**
- **Realistic user management**
- **Easier login experience**
- **Better organizational flexibility**
- **Complete MSE business operations**

This makes Finwise much more user-friendly and realistic for real-world business scenarios where people often have multiple responsibilities and roles, and MSE users can fully manage their business operations including markets and inventory.
