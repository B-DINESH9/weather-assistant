from app.fast_api_app import app
for route in app.routes:
    print(f"Path: {route.path}, Name: {route.name}, Methods: {getattr(route, 'methods', None)}")
