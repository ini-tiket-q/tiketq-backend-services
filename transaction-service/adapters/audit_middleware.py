"""
FastAPI Middleware for Audit Logging

This middleware automatically logs all API requests and responses with
comprehensive audit information including:
- Request/response timing
- User context
- Security events
- Error tracking
- Performance monitoring
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json

from adapters.audit_logger import audit_logger, AuditEventType, extract_request_context


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive audit logging of all API requests"""
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Extract request context
        request_context = extract_request_context(request)
        
        # Extract user context from authorization header
        user_context = await self._extract_user_context(request)
        
        # Log request details
        await self._log_request_start(request, request_id, request_context, user_context)
        
        # Process request
        response = None
        error_occurred = False
        
        try:
            response = await call_next(request)
            
        except HTTPException as http_error:
            error_occurred = True
            
            # Log HTTP exceptions
            audit_logger.log_security_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS if http_error.status_code == 401 
                         else AuditEventType.PERMISSION_DENIED if http_error.status_code == 403
                         else AuditEventType.ERROR_OCCURRED,
                email=user_context.get("email"),
                user_role=user_context.get("user_role"),
                message=f"HTTP {http_error.status_code}: {http_error.detail}",
                details={
                    "status_code": http_error.status_code,
                    "error_detail": http_error.detail,
                    "request_id": request_id
                },
                request_context=request_context
            )
            
            response = JSONResponse(
                status_code=http_error.status_code,
                content={"detail": http_error.detail, "request_id": request_id}
            )
            
        except Exception as error:
            error_occurred = True
            
            # Log unexpected errors
            audit_logger.log_error(
                error=error,
                context={
                    "request_id": request_id,
                    "endpoint": request_context.get("endpoint"),
                    "method": request_context.get("method")
                },
                email=user_context.get("email"),
                endpoint=request_context.get("endpoint")
            )
            
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id}
            )
        
        finally:
            # Calculate response time
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response details
            await self._log_request_complete(
                request, response, request_id, duration_ms, 
                request_context, user_context, error_occurred
            )
        
        return response
    
    async def _extract_user_context(self, request: Request) -> Dict[str, Any]:
        """Extract user context from request"""
        user_context = {"email": None, "user_role": None}
        
        try:
            # Try to extract from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would typically decode JWT token to get user info
                # For now, we'll mark it as authenticated but unknown user
                user_context.update({
                    "authenticated": True,
                    "auth_method": "Bearer"
                })
        except Exception:
            # If user extraction fails, continue with empty context
            pass
        
        return user_context
    
    async def _log_request_start(
        self, 
        request: Request, 
        request_id: str, 
        request_context: Dict[str, str],
        user_context: Dict[str, Any]
    ):
        """Log the start of request processing"""
        
        # Calculate request size
        request_size = 0
        if hasattr(request, '_body'):
            request_size = len(request._body) if request._body else 0
        
        details = {
            "request_id": request_id,
            "request_size_bytes": request_size,
            "content_type": request.headers.get("content-type"),
            "query_params": dict(request.query_params) if request.query_params else None,
            "path_params": dict(request.path_params) if request.path_params else None
        }
        
        # Check for suspicious patterns
        await self._check_suspicious_activity(request, request_context, user_context)
    
    async def _log_request_complete(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration_ms: float,
        request_context: Dict[str, str],
        user_context: Dict[str, Any],
        error_occurred: bool
    ):
        """Log the completion of request processing"""
        
        status_code = response.status_code if response else 500
        
        # Calculate response size
        response_size = 0
        if hasattr(response, 'body') and response.body:
            response_size = len(response.body)
        
        # Log API request metrics
        audit_logger.log_api_request(
            method=request_context.get("method", "UNKNOWN"),
            endpoint=request_context.get("endpoint", "UNKNOWN"),
            email=user_context.get("email"),
            user_role=user_context.get("user_role"),
            request_id=request_id,
            duration_ms=duration_ms,
            status_code=status_code,
            response_size=response_size,
            ip_address=request_context.get("ip_address"),
            user_agent=request_context.get("user_agent")
        )
        
        # Log slow requests for performance monitoring
        if duration_ms > 5000:  # 5 seconds threshold
            audit_logger.log_api_request(
                method=request_context.get("method", "UNKNOWN"),
                endpoint=request_context.get("endpoint", "UNKNOWN"),
                email=user_context.get("email"),
                duration_ms=duration_ms,
                status_code=status_code,
                ip_address=request_context.get("ip_address"),
                user_agent=request_context.get("user_agent")
            )
    
    async def _check_suspicious_activity(
        self,
        request: Request,
        request_context: Dict[str, str], 
        user_context: Dict[str, Any]
    ):
        """Check for suspicious activity patterns"""
        
        suspicious_indicators = []
        
        # Check for suspicious user agents
        user_agent = request_context.get("user_agent", "").lower()
        suspicious_agents = ["sqlmap", "nikto", "nessus", "burp", "scanner"]
        if any(agent in user_agent for agent in suspicious_agents):
            suspicious_indicators.append("suspicious_user_agent")
        
        # Check for SQL injection patterns in query parameters
        query_string = str(request.query_params)
        sql_patterns = ["'", "union", "select", "drop", "insert", "delete", "--", "/*"]
        if any(pattern in query_string.lower() for pattern in sql_patterns):
            suspicious_indicators.append("potential_sql_injection")
        
        # Check for excessive parameters (potential DoS)
        if len(request.query_params) > 50:
            suspicious_indicators.append("excessive_parameters")
        
        # Check for unusual request size
        if hasattr(request, 'headers') and request.headers.get('content-length'):
            try:
                content_length = int(request.headers.get('content-length', 0))
                if content_length > 10 * 1024 * 1024:  # 10MB threshold
                    suspicious_indicators.append("large_request_body")
            except ValueError:
                pass
        
        # Log suspicious activity if found
        if suspicious_indicators:
            audit_logger.log_security_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                email=user_context.get("email"),
                user_role=user_context.get("user_role"),
                message=f"Suspicious activity detected: {', '.join(suspicious_indicators)}",
                details={
                    "indicators": suspicious_indicators,
                    "severity": "high" if len(suspicious_indicators) > 2 else "medium"
                },
                request_context=request_context
            )


class TransactionContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject transaction context into requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract transaction ID from URL path if present
        transaction_id = None
        path_parts = request.url.path.split('/')
        
        try:
            # Look for transaction ID in path like /transactions/123
            if 'transactions' in path_parts:
                idx = path_parts.index('transactions')
                if idx + 1 < len(path_parts) and path_parts[idx + 1].isdigit():
                    transaction_id = int(path_parts[idx + 1])
        except (ValueError, IndexError):
            pass
        
        # Store transaction context in request state
        request.state.transaction_id = transaction_id
        
        response = await call_next(request)
        return response
