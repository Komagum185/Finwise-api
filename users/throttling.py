from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class LoginRateThrottle(SimpleRateThrottle):
    """
    Custom rate limiter for login endpoints that provides:
    - More lenient limits for legitimate users
    - Stricter limits for suspicious activity
    - Progressive backoff for repeated failures
    """
    
    scope = 'login'
    
    def get_cache_key(self, request, view):
        """Get cache key based on IP address"""
        if request.user.is_authenticated:
            return None  # No rate limiting for authenticated users
        
        # Use IP address for anonymous users
        ident = self.get_ident(request)
        return f"login_attempts:{ident}"
    
    def get_rate(self):
        """Get rate limit - more lenient than default"""
        return '20/minute'  # 20 attempts per minute instead of 10/hour
    
    def allow_request(self, request, view):
        """Custom logic for allowing requests"""
        if request.user.is_authenticated:
            return True
        
        # Check if this IP has been flagged for suspicious activity
        cache_key = self.get_cache_key(request, view)
        if not cache_key:
            return True
        
        # Get current attempt count
        attempts = cache.get(cache_key, 0)
        
        # Progressive backoff: increase delay after multiple failures
        if attempts >= 10:
            # After 10 attempts, require 5 minute wait
            last_attempt = cache.get(f"{cache_key}:last_attempt")
            if last_attempt and timezone.now() - last_attempt < timedelta(minutes=5):
                return False
        elif attempts >= 5:
            # After 5 attempts, require 2 minute wait
            last_attempt = cache.get(f"{cache_key}:last_attempt")
            if last_attempt and timezone.now() - last_attempt < timedelta(minutes=2):
                return False
        
        return super().allow_request(request, view)
    
    def throttle_success(self):
        """Reset rate limiting on successful login - called by DRF"""
        # This method is called by DRF without arguments
        # We'll handle the reset in the view instead
        pass
    
    def throttle_failure(self, request, view):
        """Increment failure counter on failed login"""
        cache_key = self.get_cache_key(request, view)
        if cache_key:
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, 300)  # 5 minutes
            cache.set(f"{cache_key}:last_attempt", timezone.now(), 300)
    
    def reset_login_attempts(self, request, view):
        """Custom method to reset rate limiting on successful login"""
        cache_key = self.get_cache_key(request, view)
        if cache_key:
            cache.delete(cache_key)
            cache.delete(f"{cache_key}:last_attempt")


class APIRateThrottle(SimpleRateThrottle):
    """
    General API rate limiter that's more lenient for development
    but still provides protection
    """
    
    scope = 'api'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f"api_user:{request.user.id}"
        return f"api_anon:{self.get_ident(request)}"
    
    def get_rate(self):
        """More lenient rates for development"""
        return '1000/hour'  # 1000 requests per hour


class BurstRateThrottle(SimpleRateThrottle):
    """
    Burst rate limiter for short-term spikes
    """
    
    scope = 'burst'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f"burst_user:{request.user.id}"
        return f"api_anon:{self.get_ident(request)}"
    
    def get_rate(self):
        """Allow bursts but limit sustained usage"""
        return '100/minute'  # 100 requests per minute
