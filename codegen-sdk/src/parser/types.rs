use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiSpec {
    pub info: ApiInfo,
    pub servers: Vec<Server>,
    pub endpoints: Vec<Endpoint>,
    pub schemas: Vec<Schema>,
    pub security: Vec<SecurityScheme>,
    #[serde(default)]
    pub extensions: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiInfo {
    pub title: String,
    pub version: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub contact: Option<Contact>,
    #[serde(default)]
    pub license: Option<License>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contact {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub email: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct License {
    pub name: String,
    #[serde(default)]
    pub url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Server {
    pub url: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub variables: HashMap<String, ServerVariable>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerVariable {
    #[serde(default)]
    pub default: Option<String>,
    #[serde(default)]
    pub enum_values: Option<Vec<String>>,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Endpoint {
    #[serde(rename = "path")]
    pub path: String,
    pub method: HttpMethod,
    #[serde(default)]
    pub operation_id: Option<String>,
    #[serde(default)]
    pub summary: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub deprecated: bool,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub parameters: Vec<Parameter>,
    #[serde(default)]
    pub request_body: Option<RequestBody>,
    #[serde(default)]
    pub responses: Vec<Response>,
    #[serde(default)]
    pub security: Vec<Vec<String>>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum HttpMethod {
    Get,
    Post,
    Put,
    Patch,
    Delete,
    Head,
    Options,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Parameter {
    pub name: String,
    pub location: ParameterLocation,
    #[serde(default)]
    pub required: bool,
    #[serde(default)]
    pub schema: Option<Schema>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub deprecated: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ParameterLocation {
    #[serde(rename = "path")]
    Path,
    #[serde(rename = "query")]
    Query,
    #[serde(rename = "header")]
    Header,
    #[serde(rename = "cookie")]
    Cookie,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequestBody {
    #[serde(default)]
    pub required: bool,
    #[serde(default)]
    pub content: HashMap<String, MediaType>,
    #[serde(default)]
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Response {
    #[serde(rename = "statusCode")]
    pub status_code: u16,
    pub description: String,
    #[serde(default)]
    pub headers: HashMap<String, Header>,
    #[serde(default)]
    pub content: HashMap<String, MediaType>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Header {
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub required: bool,
    #[serde(default)]
    pub schema: Option<Schema>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaType {
    #[serde(default)]
    pub schema: Option<Schema>,
    #[serde(default)]
    pub example: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Schema {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(rename = "type", default)]
    pub schema_type: Option<String>,
    #[serde(default)]
    pub format: Option<String>,
    #[serde(default)]
    pub required: Vec<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub deprecated: bool,
    #[serde(default)]
    pub default: Option<serde_json::Value>,
    #[serde(default)]
    pub example: Option<serde_json::Value>,
    #[serde(default)]
    pub properties: Option<HashMap<String, Schema>>,
    #[serde(default)]
    pub items: Option<Box<Schema>>,
    #[serde(default)]
    pub one_of: Option<Vec<Schema>>,
    #[serde(default)]
    pub any_of: Option<Vec<Schema>>,
    #[serde(default)]
    pub all_of: Option<Vec<Schema>>,
    #[serde(default)]
    pub enum_values: Option<Vec<serde_json::Value>>,
    #[serde(default, rename = "$ref")]
    pub ref_path: Option<String>,
    #[serde(default)]
    pub additional_properties: Option<Box<Schema>>,
    #[serde(default)]
    pub extensions: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityScheme {
    pub name: String,
    #[serde(rename = "type")]
    pub scheme_type: SecuritySchemeType,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub location: Option<ParameterLocation>,
    #[serde(default)]
    pub flows: Option<Vec<OAuth2Flow>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "kebab-case")]
pub enum SecuritySchemeType {
    ApiKey {
        name: String,
        #[serde(rename = "in")]
        location: ParameterLocation,
    },
    Http {
        scheme: String,
        #[serde(default)]
        bearer_format: Option<String>,
    },
    OAuth2 {
        flows: Vec<OAuth2Flow>,
    },
    OpenIdConnect {
        #[serde(rename = "openIdConnectUrl")]
        url: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OAuth2Flow {
    #[serde(rename = "flowType", default)]
    pub flow_type: Option<OAuth2FlowType>,
    #[serde(default)]
    pub authorization_url: Option<String>,
    #[serde(default)]
    pub token_url: Option<String>,
    #[serde(default)]
    pub scopes: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OAuth2FlowType {
    AuthorizationCode,
    Implicit,
    ClientCredentials,
    Password,
}
