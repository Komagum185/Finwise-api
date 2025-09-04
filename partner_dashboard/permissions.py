from rest_framework import permissions


class IsAuthenticatedUser(permissions.BasePermission):
    """
    Simple permission that only requires user to be logged in.
    Once logged in, users can view and change anything based on their role.
    """
    
    def has_permission(self, request, view):
        # Only check if user is authenticated - no role restrictions
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
            return request.user.rights == 'export'
        
        # For all other actions, any authenticated user has access
        return True


class FullAccess(permissions.BasePermission):
    """
    Permission class that ensures any authenticated user has full access.
    This is the main permission class for all dashboard views.
    """
    
    def has_permission(self, request, view):
        # Only check if user is authenticated - no role restrictions
        return request.user.is_authenticated
