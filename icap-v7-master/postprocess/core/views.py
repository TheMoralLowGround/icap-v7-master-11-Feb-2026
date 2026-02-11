from django.http import JsonResponse
from django.db import connection
from .models import PostProcess


def health_check(request):
    """Health check endpoint for monitoring and load balancers"""
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check if we can access the database
        PostProcess.objects.count()

        return JsonResponse(
            {"status": "healthy", "database": "connected", "service": "postprocess"}
        )
    except Exception as e:
        return JsonResponse(
            {"status": "unhealthy", "error": str(e), "service": "postprocess"},
            status=503,
        )


def index(request):
    """Root endpoint to confirm app is running"""
    return JsonResponse(
        {
            "message": "Postprocess service is running",
            "service": "postprocess",
            "communication": "rabbitmq",
        }
    )
