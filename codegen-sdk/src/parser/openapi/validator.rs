use crate::parser::types::*;
use std::fmt;

pub struct OpenApiValidator;

impl OpenApiValidator {
    pub fn validate(spec: &ApiSpec) -> Vec<ValidationError> {
        let mut errors = Vec::new();

        Self::validate_info(&spec.info, &mut errors);
        Self::validate_endpoints(&spec.endpoints, &mut errors);
        Self::validate_schemas(&spec.schemas, &mut errors);

        errors
    }

    fn validate_info(info: &ApiInfo, errors: &mut Vec<ValidationError>) {
        if info.title.is_empty() {
            errors.push(ValidationError {
                path: "/info/title".to_string(),
                message: "Title is required".to_string(),
                severity: Severity::Error,
            });
        }

        if info.version.is_empty() {
            errors.push(ValidationError {
                path: "/info/version".to_string(),
                message: "Version is required".to_string(),
                severity: Severity::Error,
            });
        }
    }

    fn validate_endpoints(endpoints: &[Endpoint], errors: &mut Vec<ValidationError>) {
        let mut operation_ids = std::collections::HashSet::new();

        for endpoint in endpoints {
            if endpoint.path.is_empty() {
                errors.push(ValidationError {
                    path: format!("/paths/{}", endpoint.path),
                    message: "Path is required".to_string(),
                    severity: Severity::Error,
                });
            }

            if let Some(ref op_id) = endpoint.operation_id {
                if op_id.is_empty() {
                    errors.push(ValidationError {
                        path: format!("/paths/{}/operationId", endpoint.path),
                        message: "Operation ID cannot be empty".to_string(),
                        severity: Severity::Warning,
                    });
                } else if operation_ids.contains(op_id) {
                    errors.push(ValidationError {
                        path: format!("/paths/{}/operationId", endpoint.path),
                        message: format!("Duplicate operation ID: {}", op_id),
                        severity: Severity::Warning,
                    });
                }
                operation_ids.insert(op_id.clone());
            }

            if endpoint.responses.is_empty() {
                errors.push(ValidationError {
                    path: format!(
                        "/paths/{}/{}/responses",
                        endpoint.path,
                        format!("{:?}", endpoint.method)
                    ),
                    message: "At least one response is required".to_string(),
                    severity: Severity::Warning,
                });
            }
        }
    }

    fn validate_schemas(schemas: &[Schema], errors: &mut Vec<ValidationError>) {
        for schema in schemas {
            Self::validate_schema(schema, errors);
        }
    }

    fn validate_schema(schema: &Schema, errors: &mut Vec<ValidationError>) {
        if let Some(ref name) = schema.name {
            if name.is_empty() {
                errors.push(ValidationError {
                    path: "/components/schemas".to_string(),
                    message: "Schema name cannot be empty".to_string(),
                    severity: Severity::Warning,
                });
            }
        }

        if schema.ref_path.is_none() && schema.schema_type.is_none() && schema.properties.is_none()
        {
            errors.push(ValidationError {
                path: format!(
                    "/components/schemas/{}",
                    schema.name.as_deref().unwrap_or("unknown")
                ),
                message: "Schema has no type, properties, or reference".to_string(),
                severity: Severity::Warning,
            });
        }
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ValidationError {
    pub path: String,
    pub message: String,
    pub severity: Severity,
}

#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize)]
pub enum Severity {
    Error,
    Warning,
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{:?}] {}: {}", self.severity, self.path, self.message)
    }
}
