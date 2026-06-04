"""
Middleware to capture 404 errors and send them to Sentry/GlitchTip
"""
import logging

logger = logging.getLogger('django.request')


class Capture404Middleware:
    """Capture 404 errors and send them to Sentry/GlitchTip"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if response.status_code == 404:
            # Log as WARNING so Sentry picks it up
            logger.warning(
                f"Not Found: {request.path}",
                extra={
                    'status_code': 404,
                    'request': request,
                }
            )
            
            # Also try to send directly to Sentry if available
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"404 Not Found: {request.path}",
                    level="warning"
                )
            except (ImportError, RuntimeError):
                pass
        
        return response
