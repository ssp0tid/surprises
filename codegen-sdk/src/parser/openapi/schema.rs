use crate::parser::types::*;
use std::collections::HashMap;

pub struct SchemaResolver {
    ref_cache: HashMap<String, Schema>,
}

impl SchemaResolver {
    pub fn new() -> Self {
        Self {
            ref_cache: HashMap::new(),
        }
    }

    pub fn resolve_ref(&mut self, ref_path: &str, schemas: &[Schema]) -> Option<Schema> {
        if let Some(cached) = self.ref_cache.get(ref_path) {
            return Some(cached.clone());
        }

        let name = ref_path.split('/').last().map(|s| s.to_string())?;

        for schema in schemas {
            if schema.name.as_ref() == Some(&name) {
                self.ref_cache.insert(ref_path.to_string(), schema.clone());
                return Some(schema.clone());
            }
        }

        None
    }

    pub fn resolve_schema(&mut self, schema: &Schema, schemas: &[Schema]) -> Schema {
        if let Some(ref_path) = &schema.ref_path {
            if let Some(resolved) = self.resolve_ref(ref_path, schemas) {
                return resolved;
            }
        }

        let mut resolved = schema.clone();

        if let Some(items) = &schema.items {
            resolved.items = Some(Box::new(self.resolve_schema(items, schemas)));
        }

        if let Some(one_of) = &schema.one_of {
            resolved.one_of = Some(
                one_of
                    .iter()
                    .map(|s| self.resolve_schema(s, schemas))
                    .collect(),
            );
        }

        if let Some(props) = &schema.properties {
            let mut new_props = HashMap::new();
            for (k, v) in props {
                new_props.insert(k.clone(), self.resolve_schema(v, schemas));
            }
            resolved.properties = Some(new_props);
        }

        resolved
    }
}

impl Default for SchemaResolver {
    fn default() -> Self {
        Self::new()
    }
}

pub fn infer_type(schema: &Schema) -> &str {
    schema.schema_type.as_deref().unwrap_or("unknown")
}

pub fn is_nullable(schema: &Schema) -> bool {
    schema
        .extensions
        .get("x-nullable")
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
}
