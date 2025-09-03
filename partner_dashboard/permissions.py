from rest_framework import permissions


class IsPartner(permissions.BasePermission):
    """
    Custom permission to only allow partner users to access the dashboard.
    All partners have full viewing access to all dashboard data.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and has partner role
        return (
            request.user.is_authenticated and 
            request.user.role == 'partner'
        )


class CanExport(permissions.BasePermission):
    """
    Custom permission to only allow users with export rights to export data.
    All partners can view data, but only those with export rights can export.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.role != 'partner':
            return False
        
        # Check if the action requires export rights
        if hasattr(view, 'action') and view.action in ['export_csv', 'export_pdf']:
            return request.user.rights == 'export'
        
        # For viewing actions, all partners have access
        return True


class PartnerDashboardPermission(permissions.BasePermission):
    """
    Combined permission class for partner dashboard.
    All partners can view everything, export rights only needed for exports.
    """
    
    def has_permission(self, request, view):
        # Basic partner role check
        if not request.user.is_authenticated or request.user.role != 'partner':
            return False
        
        # Check export rights for export actions
        if hasattr(view, 'action') and view.action in ['export_csv', 'export_pdf']:
            return request.user.rights == 'export'
        
        # For all other actions (viewing), all partners have access
        return True


class FullPartnerAccess(permissions.BasePermission):
    """
    Permission class that ensures all partners have full access to view dashboard data.
    This is the main permission class for partner dashboard views.
    """
    
    def has_permission(self, request, view):
        # Only partners can access
        if not request.user.is_authenticated or request.user.role != 'partner':
            return False
        
        # All partners have full viewing access
        return True
