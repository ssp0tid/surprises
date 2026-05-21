use crate::parser::types::*;
use anyhow::Result;
use std::collections::HashMap;
use std::path::Path;

pub struct OpenApiParser;

impl OpenApiParser {
    pub fn parse(input: &str) -> Result<ApiSpec> {
        if let Ok(spec) = serde_json::from_str::<OpenApiDocument>(input) {
            return Ok(convert_document(spec));
        }
        if let Ok(spec) = serde_yaml::from_str::<OpenApiDocument>(input) {
            return Ok(convert_document(spec));
        }
        anyhow::bail!("Failed to parse as JSON or YAML")
    }

    pub fn parse_file(path: &Path) -> Result<ApiSpec> {
        let content = std::fs::read_to_string(path)?;
        Self::parse(&content)
    }
}

fn convert_document(doc: OpenApiDocument) -> ApiSpec {
    let info = ApiInfo {
        title: doc.info.title,
        version: doc.info.version,
        description: doc.info.description,
        contact: doc.info.contact.map(|c| Contact {
            name: c.name,
            url: c.url,
            email: c.email,
        }),
        license: doc.info.license.map(|l| License {
            name: l.name,
            url: l.url,
        }),
    };

    let servers: Vec<Server> = doc
        .servers
        .unwrap_or_default()
        .into_iter()
        .map(|s| Server {
            url: s.url,
            description: s.description,
            variables: s
                .variables
                .unwrap_or_default()
                .into_iter()
                .map(|(k, v)| {
                    (
                        k,
                        ServerVariable {
                            default: v.default,
                            enum_values: v.enum_values,
                            description: v.description,
                        },
                    )
                })
                .collect(),
        })
        .collect();

    let mut endpoints = Vec::new();
    let mut schemas = Vec::new();

    if let Some(paths) = doc.paths {
        for (path, path_item) in paths {
            let methods = vec![
                (HttpMethod::Get, path_item.get),
                (HttpMethod::Post, path_item.post),
                (HttpMethod::Put, path_item.put),
                (HttpMethod::Patch, path_item.patch),
                (HttpMethod::Delete, path_item.delete),
                (HttpMethod::Head, path_item.head),
                (HttpMethod::Options, path_item.options),
            ];

            for (method, operation) in methods {
                if let Some(op) = operation {
                    let endpoint = convert_operation(path.clone(), method, op);
                    endpoints.push(endpoint);
                }
            }

            if let Some(schema_obj) = path_item.schema {
                for (name, schema) in schema_obj {
                    let mut s = schema;
                    s.name = Some(name);
                    schemas.push(s);
                }
            }
        }
    }

    if let Some(components) = doc.components {
        if let Some(schemas_obj) = components.schemas {
            for (name, schema) in schemas_obj {
                let mut s = schema;
                s.name = Some(name);
                schemas.push(s);
            }
        }
    }

    let security = Vec::new();

    ApiSpec {
        info,
        servers,
        endpoints,
        schemas,
        security,
        extensions: HashMap::new(),
    }
}

fn convert_operation(path: String, method: HttpMethod, op: Operation) -> Endpoint {
    let mut parameters = Vec::new();
    if let Some(params) = op.parameters {
        for p in params {
            parameters.push(Parameter {
                name: p.name,
                location: p.location,
                required: p.required.unwrap_or(false),
                schema: p.schema,
                description: p.description,
                deprecated: p.deprecated.unwrap_or(false),
            });
        }
    }

    let request_body = op.request_body.map(|rb| RequestBody {
        required: rb.required.unwrap_or(false),
        content: rb.content.unwrap_or_default(),
        description: rb.description,
    });

    let mut responses = Vec::new();
    if let Some(resp_map) = op.responses {
        for (code, resp) in resp_map {
            let status_code = if code == "default" || code.starts_with('1') {
                200
            } else {
                code.replace("XX", "00").parse().unwrap_or(200)
            };
            responses.push(Response {
                status_code,
                description: resp.description.unwrap_or_default(),
                headers: resp.headers.unwrap_or_default(),
                content: resp.content.unwrap_or_default(),
            });
        }
    }

    let security: Vec<Vec<String>> = op
        .security
        .unwrap_or_default()
        .into_iter()
        .map(|vec| {
            vec.into_iter()
                .flat_map(|sr| sr.schemes.into_values().flatten().collect::<Vec<_>>())
                .collect()
        })
        .collect();

    Endpoint {
        path,
        method,
        operation_id: op.operation_id,
        summary: op.summary,
        description: op.description,
        deprecated: op.deprecated.unwrap_or(false),
        tags: op.tags.unwrap_or_default(),
        parameters,
        request_body,
        responses,
        security,
    }
}

#[derive(Debug, Clone, serde::Deserialize)]
struct OpenApiDocument {
    #[serde(rename = "openapi")]
    pub openapi: String,
    pub info: OpenApiInfo,
    #[serde(default)]
    pub servers: Option<Vec<OpenApiServer>>,
    #[serde(default)]
    pub paths: Option<HashMap<String, PathItem>>,
    #[serde(default)]
    pub components: Option<Components>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct OpenApiInfo {
    pub title: String,
    pub version: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub contact: Option<ContactInfo>,
    #[serde(default)]
    pub license: Option<LicenseInfo>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct ContactInfo {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub email: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct LicenseInfo {
    pub name: String,
    #[serde(default)]
    pub url: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct OpenApiServer {
    pub url: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub variables: Option<HashMap<String, ServerVar>>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct ServerVar {
    #[serde(default)]
    pub default: Option<String>,
    #[serde(default)]
    pub enum_values: Option<Vec<String>>,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct PathItem {
    #[serde(default)]
    pub get: Option<Operation>,
    #[serde(default)]
    pub post: Option<Operation>,
    #[serde(default)]
    pub put: Option<Operation>,
    #[serde(default)]
    pub patch: Option<Operation>,
    #[serde(default)]
    pub delete: Option<Operation>,
    #[serde(default)]
    pub head: Option<Operation>,
    #[serde(default)]
    pub options: Option<Operation>,
    #[serde(default)]
    pub parameters: Option<Vec<Param>>,
    #[serde(rename = "schema", default)]
    pub schema: Option<HashMap<String, Schema>>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct Operation {
    #[serde(default)]
    pub operation_id: Option<String>,
    #[serde(default)]
    pub summary: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub deprecated: Option<bool>,
    #[serde(default)]
    pub tags: Option<Vec<String>>,
    #[serde(default)]
    pub parameters: Option<Vec<Param>>,
    #[serde(default)]
    pub request_body: Option<RequestBodyRaw>,
    #[serde(default)]
    pub responses: Option<HashMap<String, ResponseRaw>>,
    #[serde(default)]
    pub security: Option<Vec<Vec<SecurityReq>>>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct Param {
    pub name: String,
    #[serde(rename = "in")]
    pub location: ParameterLocation,
    #[serde(default)]
    pub required: Option<bool>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub deprecated: Option<bool>,
    #[serde(default)]
    pub schema: Option<Schema>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct RequestBodyRaw {
    #[serde(default)]
    pub required: Option<bool>,
    #[serde(default)]
    pub content: Option<HashMap<String, MediaType>>,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct ResponseRaw {
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub headers: Option<HashMap<String, Header>>,
    #[serde(default)]
    pub content: Option<HashMap<String, MediaType>>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct SecurityReq {
    #[serde(flatten)]
    pub schemes: HashMap<String, Vec<String>>,
}

#[derive(Debug, Clone, serde::Deserialize)]
struct Components {
    #[serde(rename = "schemas", default)]
    pub schemas: Option<HashMap<String, Schema>>,
    #[serde(rename = "securitySchemes", default)]
    pub security_schemes: Option<HashMap<String, serde_json::Value>>,
}
