from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        ready = not pending
    except DatabaseError:
        ready = False
    response = JsonResponse(
        {"status": "ok" if ready else "unavailable"}, status=200 if ready else 503
    )
    response["Cache-Control"] = "no-store"
    return response
