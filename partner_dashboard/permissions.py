from rest_framework import permissions
from django.db.models import Q


class RoleBasedPermission(permissions.BasePermission):
    """
    Base permission class for role-based access control.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get the required role from the view
        required_role = getattr(view, 'required_role', None)
        if required_role:
            return request.user.role == required_role
        
        # Get the allowed roles from the view
        allowed_roles = getattr(view, 'allowed_roles', None)
        if allowed_roles:
            return request.user.role in allowed_roles
        
        return True


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class that only allows super admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'super_admin' and
            request.user.is_superuser
        )


class IsAgent(permissions.BasePermission):
    """
    Permission class that only allows agent users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'agent'
        )


class IsMSE(permissions.BasePermission):
    """
    Permission class that only allows MSE users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'mse'
        )


class IsPartner(permissions.BasePermission):
    """
    Permission class that only allows partner users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'partner'
        )


class CanManageUsers(permissions.BasePermission):
    """
    Permission class that allows users who can manage other users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_manage_users
        )


class CanManageMSE(permissions.BasePermission):
    """
    Permission class that allows users who can manage MSEs.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_manage_mse
        )


class CanViewReports(permissions.BasePermission):
    """
    Permission class that allows users who can view reports.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_view_reports
        )


class CanExportData(permissions.BasePermission):
    """
    Permission class that allows users who can export data.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_export_data
        )


class IsOwnerOrAssigned(permissions.BasePermission):
    """
    Permission class that allows users to access data they own or are assigned to manage.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Super admin can access everything
        if user.role == 'super_admin' and user.is_superuser:
            return True
        
        # Agent can access assigned MSEs and their data
        if user.role == 'agent':
            if hasattr(obj, 'mse') and obj.mse.assigned_agent == user:
                return True
            if hasattr(obj, 'assigned_agent') and obj.assigned_agent == user:
                return True
            if hasattr(obj, 'owner') and obj.owner.assigned_agent == user:
                return True
        
        # MSE can access their own data
        if user.role == 'mse':
            if hasattr(obj, 'mse') and obj.mse.owner == user:
                return True
            if hasattr(obj, 'owner') and obj.owner == user:
                return True
            if hasattr(obj, 'wallet') and obj.wallet.mse.owner == user:
                return True
        
        # Partner can access partner-linked data
        if user.role == 'partner':
            if hasattr(obj, 'mse') and obj.mse.owner.assigned_agent == user.assigned_agent:
                return True
            if hasattr(obj, 'owner') and obj.owner.assigned_agent == user.assigned_agent:
                return True
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows users to read everything but only modify their own data.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        user = request.user
        
        # Super admin can modify everything
        if user.role == 'super_admin' and user.is_superuser:
            return True
        
        # Check ownership
        if hasattr(obj, 'owner'):
            return obj.owner == user
        elif hasattr(obj, 'mse'):
            return obj.mse.owner == user
        elif hasattr(obj, 'user'):
            return obj.user == user
        
        return False


class AgentAccessPermission(permissions.BasePermission):
    """
    Permission class for agent-specific access control.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'agent'
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Agent can access assigned MSEs and their data
        if hasattr(obj, 'mse') and obj.mse.assigned_agent == user:
            return True
        if hasattr(obj, 'assigned_agent') and obj.assigned_agent == user:
            return True
        if hasattr(obj, 'owner') and obj.owner.assigned_agent == user:
            return True
        
        return False


class MSEAccessPermission(permissions.BasePermission):
    """
    Permission class for MSE-specific access control.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'mse'
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # MSE can only access their own data
        if hasattr(obj, 'mse') and obj.mse.owner == user:
            return True
        if hasattr(obj, 'owner') and obj.owner == user:
            return True
        if hasattr(obj, 'wallet') and obj.wallet.mse.owner == user:
            return True
        
        return False


class PartnerAccessPermission(permissions.BasePermission):
    """
    Permission class for partner-specific access control.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'partner'
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Partner can access partner-linked data
        if hasattr(obj, 'mse') and obj.mse.owner.assigned_agent == user.assigned_agent:
            return True
        if hasattr(obj, 'owner') and obj.owner.assigned_agent == user.assigned_agent:
            return True
        
        return False


# Legacy permissions for backward compatibility
class IsAuthenticatedUser(permissions.BasePermission):
    """
    Simple permission that only requires user to be logged in.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated


class CanExport(permissions.BasePermission):
    """
    Permission for export actions - only users with export rights can export.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the action requires export rights
        if hasattr(view, 'action') and view.action in ['export_csv', 'export_pdf']:
            return request.user.can_export_data
        
        # For all other actions, any authenticated user has access
        return True


class FullAccess(permissions.BasePermission):
    """
    Permission class that ensures any authenticated user has full access.
    This is the main permission class for all dashboard views.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
