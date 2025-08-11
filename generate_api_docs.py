#!/usr/bin/env python3
"""
API Documentation Generator for Finwise API
Generates comprehensive API documentation in multiple formats
"""

import os
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.urls import reverse
from django.conf import settings


class APIDocumentationGenerator:
    """Generate comprehensive API documentation"""
    
    def __init__(self):
        self.api_endpoints = []
        self.base_url = "http://localhost:8000"
        
    def generate_documentation(self):
        """Generate complete API documentation"""
        print("🔍 Generating API Documentation...")
        
        # Get all URL patterns
        resolver = get_resolver()
        self._extract_url_patterns(resolver.url_patterns, "")
        
        # Generate documentation in different formats
        self._generate_markdown_docs()
        self._generate_postman_collection()
        self._generate_openapi_spec()
        self._generate_insomnia_collection()
        
        print("✅ API Documentation generated successfully!")
    
    def _extract_url_patterns(self, patterns, base_path=""):
        """Extract URL patterns recursively"""
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                self._process_url_pattern(pattern, base_path)
            elif isinstance(pattern, URLResolver):
                new_base = f"{base_path}{pattern.pattern.regex.pattern}"
                self._extract_url_patterns(pattern.url_patterns, new_base)
    
    def _process_url_pattern(self, pattern, base_path):
        """Process individual URL pattern"""
        if not hasattr(pattern.callback, 'view_class'):
            return
        
        view_class = pattern.callback.view_class
        
        # Skip non-API views
        if not issubclass(view_class, (APIView, ViewSet)):
            return
        
        endpoint = {
            'url': f"{base_path}{pattern.pattern.regex.pattern}",
            'name': pattern.name or '',
            'view_class': view_class.__name__,
            'methods': self._get_supported_methods(view_class),
            'description': self._get_view_description(view_class),
            'permissions': self._get_view_permissions(view_class),
            'actions': self._get_view_actions(view_class),
            'serializers': self._get_view_serializers(view_class),
            'filters': self._get_view_filters(view_class),
            'examples': self._generate_examples(view_class)
        }
        
        self.api_endpoints.append(endpoint)
    
    def _get_supported_methods(self, view_class):
        """Get supported HTTP methods for a view"""
        methods = []
        
        if hasattr(view_class, 'get'):
            methods.append('GET')
        if hasattr(view_class, 'post'):
            methods.append('POST')
        if hasattr(view_class, 'put'):
            methods.append('PUT')
        if hasattr(view_class, 'patch'):
            methods.append('PATCH')
        if hasattr(view_class, 'delete'):
            methods.append('DELETE')
        
        return methods
    
    def _get_view_description(self, view_class):
        """Get view description from docstring"""
        if hasattr(view_class, '__doc__') and view_class.__doc__:
            return view_class.__doc__.strip()
        return f"{view_class.__name__} API endpoint"
    
    def _get_view_permissions(self, view_class):
        """Get view permission classes"""
        permissions = []
        if hasattr(view_class, 'permission_classes'):
            for permission in view_class.permission_classes:
                permissions.append(permission.__name__)
        return permissions
    
    def _get_view_actions(self, view_class):
        """Get custom actions for ViewSets"""
        actions = []
        if hasattr(view_class, 'get_extra_actions'):
            for action_name, action_func in view_class.get_extra_actions():
                actions.append({
                    'name': action_name,
                    'methods': action_func.methods if hasattr(action_func, 'methods') else ['GET'],
                    'description': action_func.__doc__ or f"{action_name} action"
                })
        return actions
    
    def _get_view_serializers(self, view_class):
        """Get view serializers"""
        serializers = []
        if hasattr(view_class, 'serializer_class'):
            serializers.append(view_class.serializer_class.__name__)
        if hasattr(view_class, 'get_serializer_class'):
            # This is more complex, just note it
            serializers.append("Dynamic serializer")
        return serializers
    
    def _get_view_filters(self, view_class):
        """Get view filter backends"""
        filters = []
        if hasattr(view_class, 'filter_backends'):
            for filter_backend in view_class.filter_backends:
                filters.append(filter_backend.__name__)
        return filters
    
    def _generate_examples(self, view_class):
        """Generate example requests/responses"""
        examples = {}
        
        # Example request for POST
        if 'POST' in self._get_supported_methods(view_class):
            examples['request'] = {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer <your_token>'
                },
                'body': self._get_example_request_body(view_class)
            }
        
        # Example response
        examples['response'] = {
            'status': 200,
            'body': self._get_example_response_body(view_class)
        }
        
        return examples
    
    def _get_example_request_body(self, view_class):
        """Get example request body based on view class"""
        # This is a simplified example - in a real implementation,
        # you'd analyze the serializer fields
        return {
            "example_field": "example_value",
            "required_field": "required_value"
        }
    
    def _get_example_response_body(self, view_class):
        """Get example response body"""
        return {
            "success": True,
            "data": "Response data here",
            "message": "Operation completed successfully"
        }
    
    def _generate_markdown_docs(self):
        """Generate Markdown documentation"""
        markdown_content = f"""# Finwise API Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

The Finwise API provides comprehensive financial management, user authentication, and MSE (Micro and Small Enterprise) management capabilities.

## Base URL

```
{self.base_url}
```

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

"""
        
        # Group endpoints by app
        endpoints_by_app = {}
        for endpoint in self.api_endpoints:
            app_name = endpoint['url'].split('/')[1] if len(endpoint['url'].split('/')) > 1 else 'root'
            if app_name not in endpoints_by_app:
                endpoints_by_app[app_name] = []
            endpoints_by_app[app_name].append(endpoint)
        
        # Generate documentation for each app
        for app_name, endpoints in endpoints_by_app.items():
            markdown_content += f"\n### {app_name.upper()}\n\n"
            
            for endpoint in endpoints:
                markdown_content += self._generate_endpoint_markdown(endpoint)
        
        # Write to file
        with open('API_DOCUMENTATION_COMPLETE.md', 'w') as f:
            f.write(markdown_content)
        
        print("📝 Markdown documentation generated: API_DOCUMENTATION_COMPLETE.md")
    
    def _generate_endpoint_markdown(self, endpoint):
        """Generate Markdown for a single endpoint"""
        markdown = f"#### {endpoint['name'] or endpoint['view_class']}\n\n"
        markdown += f"**URL:** `{endpoint['url']}`\n\n"
        markdown += f"**Methods:** {', '.join(endpoint['methods'])}\n\n"
        markdown += f"**Description:** {endpoint['description']}\n\n"
        
        if endpoint['permissions']:
            markdown += f"**Permissions:** {', '.join(endpoint['permissions'])}\n\n"
        
        if endpoint['serializers']:
            markdown += f"**Serializers:** {', '.join(endpoint['serializers'])}\n\n"
        
        if endpoint['filters']:
            markdown += f"**Filters:** {', '.join(endpoint['filters'])}\n\n"
        
        if endpoint['actions']:
            markdown += "**Custom Actions:**\n"
            for action in endpoint['actions']:
                markdown += f"- `{action['name']}` ({', '.join(action['methods'])}): {action['description']}\n"
            markdown += "\n"
        
        # Example request/response
        if endpoint['examples']:
            markdown += "**Example Request:**\n"
            markdown += "```json\n"
            markdown += json.dumps(endpoint['examples']['request'], indent=2)
            markdown += "\n```\n\n"
            
            markdown += "**Example Response:**\n"
            markdown += "```json\n"
            markdown += json.dumps(endpoint['examples']['response'], indent=2)
            markdown += "\n```\n\n"
        
        markdown += "---\n\n"
        return markdown
    
    def _generate_postman_collection(self):
        """Generate Postman collection"""
        collection = {
            "info": {
                "name": "Finwise API",
                "description": "Complete API collection for Finwise financial management system",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        # Group by app
        endpoints_by_app = {}
        for endpoint in self.api_endpoints:
            app_name = endpoint['url'].split('/')[1] if len(endpoint['url'].split('/')) > 1 else 'root'
            if app_name not in endpoints_by_app:
                endpoints_by_app[app_name] = []
            endpoints_by_app[app_name].append(endpoint)
        
        for app_name, endpoints in endpoints_by_app.items():
            app_folder = {
                "name": app_name.upper(),
                "item": []
            }
            
            for endpoint in endpoints:
                request_item = self._create_postman_request(endpoint)
                app_folder["item"].append(request_item)
            
            collection["item"].append(app_folder)
        
        # Write to file
        with open('Finwise_API_Postman_Collection.json', 'w') as f:
            json.dump(collection, f, indent=2)
        
        print("📦 Postman collection generated: Finwise_API_Postman_Collection.json")
    
    def _create_postman_request(self, endpoint):
        """Create Postman request item"""
        request_item = {
            "name": endpoint['name'] or endpoint['view_class'],
            "request": {
                "method": endpoint['methods'][0] if endpoint['methods'] else 'GET',
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    },
                    {
                        "key": "Authorization",
                        "value": "Bearer {{jwt_token}}",
                        "disabled": True
                    }
                ],
                "url": {
                    "raw": f"{{base_url}}{endpoint['url']}",
                    "host": ["{{base_url}}"],
                    "path": endpoint['url'].split('/')[1:]
                }
            }
        }
        
        # Add body for POST/PUT/PATCH
        if request_item["request"]["method"] in ['POST', 'PUT', 'PATCH']:
            request_item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(endpoint['examples']['request']['body'], indent=2)
            }
        
        return request_item
    
    def _generate_openapi_spec(self):
        """Generate OpenAPI specification"""
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Finwise API",
                "description": "Financial management and MSE management API",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": self.base_url,
                    "description": "Development server"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }
        
        # Add paths
        for endpoint in self.api_endpoints:
            path = endpoint['url']
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            for method in endpoint['methods']:
                method_lower = method.lower()
                openapi_spec["paths"][path][method_lower] = {
                    "summary": endpoint['description'],
                    "tags": [endpoint['url'].split('/')[1] if len(endpoint['url'].split('/')) > 1 else 'root'],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Successful operation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "data": {"type": "object"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
        
        # Write to file
        with open('openapi_spec.json', 'w') as f:
            json.dump(openapi_spec, f, indent=2)
        
        print("🔓 OpenAPI specification generated: openapi_spec.json")
    
    def _generate_insomnia_collection(self):
        """Generate Insomnia collection"""
        insomnia_collection = {
            "_type": "export",
            "__export_format": 4,
            "__export_date": datetime.now().isoformat(),
            "__export_source": "insomnia.desktop.app:v2023.5.8",
            "resources": [
                {
                    "_id": "req_root",
                    "parentId": "wrk_finwise",
                    "modified": int(datetime.now().timestamp() * 1000),
                    "created": int(datetime.now().timestamp() * 1000),
                    "url": "{{ _.base_url }}",
                    "name": "Base URL",
                    "description": "Finwise API base URL",
                    "method": "GET",
                    "body": {},
                    "parameters": [],
                    "headers": [],
                    "authentication": {},
                    "metaSortKey": -1000000000000,
                    "isPrivate": False,
                    "settingStoreCookies": True,
                    "settingSendCookies": True,
                    "settingDisableRenderRequestBody": False,
                    "settingEncodeUrl": True,
                    "settingRebuildPath": True,
                    "settingFollowRedirects": "global",
                    "_type": "request"
                }
            ]
        }
        
        # Add workspace
        workspace = {
            "_id": "wrk_finwise",
            "parentId": None,
            "modified": int(datetime.now().timestamp() * 1000),
            "created": int(datetime.now().timestamp() * 1000),
            "name": "Finwise API",
            "description": "Complete API collection for Finwise",
            "scope": "collection",
            "_type": "workspace"
        }
        
        insomnia_collection["resources"].append(workspace)
        
        # Write to file
        with open('Finwise_API_Insomnia_Collection.json', 'w') as f:
            json.dump(insomnia_collection, f, indent=2)
        
        print("🌙 Insomnia collection generated: Finwise_API_Insomnia_Collection.json")


def main():
    """Main function to generate API documentation"""
    generator = APIDocumentationGenerator()
    generator.generate_documentation()
    
    print("\n🎉 API Documentation Generation Complete!")
    print("\nGenerated files:")
    print("- API_DOCUMENTATION_COMPLETE.md (Comprehensive Markdown docs)")
    print("- Finwise_API_Postman_Collection.json (Postman collection)")
    print("- openapi_spec.json (OpenAPI specification)")
    print("- Finwise_API_Insomnia_Collection.json (Insomnia collection)")
    print("\nYou can now:")
    print("1. Import the Postman collection into Postman")
    print("2. Use the OpenAPI spec with Swagger UI")
    print("3. Import the Insomnia collection into Insomnia")
    print("4. Share the Markdown documentation with your team")


if __name__ == "__main__":
    main()
