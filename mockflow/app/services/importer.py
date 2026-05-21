"""Import functionality for OpenAPI and Postman."""

import json
import re


class OpenAPIImporter:
    """Import endpoints from OpenAPI/Swagger specification."""

    def __init__(self, spec_data):
        self.spec = spec_data if isinstance(spec_data, dict) else json.loads(spec_data)
        self.base_path = self.spec.get("servers", [{}])[0].get("url", "")
        self.paths = self.spec.get("paths", {})

    def import_endpoints(self):
        """Import all endpoints from OpenAPI spec."""
        endpoints = []

        for path, methods in self.paths.items():
            for method, details in methods.items():
                if method.upper() not in [
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                ]:
                    continue

                endpoint = {
                    "path": self.base_path + path,
                    "method": method.upper(),
                    "description": details.get(
                        "summary", details.get("description", "")
                    ),
                    "responses": [],
                }

                for status, response in (
                    details.get("responses", {})
                    .get("200", {})
                    .get("content", {})
                    .items()
                ):
                    content = response.get("schema")
                    if content:
                        endpoint["responses"].append(
                            {
                                "name": f"Status {status}",
                                "status_code": int(status) if status.isdigit() else 200,
                                "body": json.dumps(content, indent=2),
                                "content_type": status,
                                "is_default": len(endpoint["responses"]) == 0,
                            }
                        )

                if not endpoint["responses"]:
                    endpoint["responses"].append(
                        {
                            "name": "Default",
                            "status_code": 200,
                            "body": "{}",
                            "content_type": "application/json",
                            "is_default": True,
                        }
                    )

                endpoints.append(endpoint)

        return endpoints


class PostmanImporter:
    """Import endpoints from Postman collection."""

    def __init__(self, collection_data):
        self.collection = (
            collection_data
            if isinstance(collection_data, dict)
            else json.loads(collection_data)
        )
        self.items = self.collection.get("item", [])

    def import_endpoints(self):
        """Import all endpoints from Postman collection."""
        endpoints = []

        for item in self._flatten_items(self.items):
            request = item.get("request", {})
            url = request.get("url", {})
            method = request.get("method", "GET").upper()

            if isinstance(url, dict):
                path = url.get("raw", "/")
            else:
                path = url

            endpoint = {
                "path": path,
                "method": method,
                "description": item.get("name", ""),
                "responses": [],
            }

            events = request.get("event", [])
            for event in events:
                script = event.get("script", {})
                if script.get("exec"):
                    endpoint["responses"].append(
                        {
                            "name": "Default",
                            "status_code": 200,
                            "body": "{}",
                            "content_type": "application/json",
                            "is_default": True,
                        }
                    )

            if not endpoint["responses"]:
                endpoint["responses"].append(
                    {
                        "name": "Default",
                        "status_code": 200,
                        "body": "{}",
                        "content_type": "application/json",
                        "is_default": True,
                    }
                )

            endpoints.append(endpoint)

        return endpoints

    def _flatten_items(self, items):
        """Flatten nested Postman items."""
        result = []
        for item in items:
            if isinstance(item, dict):
                if "item" in item:
                    result.extend(self._flatten_items(item["item"]))
                else:
                    result.append(item)
        return result


class JSONImporter:
    """Import endpoints from raw JSON definition."""

    def __init__(self, data):
        self.data = data if isinstance(data, dict) else json.loads(data)

    def import_project(self):
        """Import project and endpoints from JSON."""
        project_data = self.data.get("project", {})
        endpoints_data = self.data.get("endpoints", [])

        return project_data, endpoints_data

    def validate(self):
        """Validate JSON structure."""
        if "project" not in self.data:
            return False, "Missing project key"
        if not self.data.get("project", {}).get("name"):
            return False, "Missing project name"
        return True, None


def import_from_openapi(spec_data):
    """Import endpoints from OpenAPI specification."""
    importer = OpenAPIImporter(spec_data)
    return importer.import_endpoints()


def import_from_postman(collection_data):
    """Import endpoints from Postman collection."""
    importer = PostmanImporter(collection_data)
    return importer.import_endpoints()


def import_from_json(json_data):
    """Import from raw JSON definition."""
    importer = JSONImporter(json_data)
    valid, error = importer.validate()
    if not valid:
        return None, error
    return importer.import_project()
