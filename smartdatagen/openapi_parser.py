import json
import yaml
from openapi_spec_validator import validate_spec

def load_openapi_file(file_path):
    """
    加载 OpenAPI 文件（YAML 或 JSON）
    
    Args:
        file_path (str): OpenAPI 文件路径
        
    Returns:
        dict: 解析后的 OpenAPI 规范
    """
    # 手动读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        # 尝试解析为 JSON
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试解析为 YAML
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as yaml_error:
            raise Exception(f"无法解析 OpenAPI 文件: {yaml_error}")

def extract_schemas_from_openapi(openapi_path):
    """
    从 OpenAPI 文档中提取 schema
    
    Args:
        openapi_path (str): OpenAPI 文件路径
        
    Returns:
        dict: 键为接口路径+方法，值为 schema 对象
    """
    # 加载 OpenAPI 文件
    spec = load_openapi_file(openapi_path)
    
    # 验证规范
    try:
        validate_spec(spec)
        print("[OK] OpenAPI 规范验证通过")
    except Exception as e:
        print(f"[WARN] OpenAPI 规范验证警告: {e}")
    
    schemas = {}
    
    # 遍历 paths
    if 'paths' in spec:
        paths = spec['paths']
        
        for path, path_item in paths.items():
            # 遍历 HTTP 方法
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    operation_id = operation.get('operationId', f"{method.upper()}_{path}")
                    key = f"{method.upper()} {path}"
                    
                    # 提取 requestBody 中的 schema
                    if 'requestBody' in operation:
                        request_body = operation['requestBody']
                        if 'content' in request_body:
                            content = request_body['content']
                            if 'application/json' in content:
                                json_content = content['application/json']
                                if 'schema' in json_content:
                                    schemas[f"{key} (request)"] = json_content['schema']
                    
                    # 提取 responses 中的 schema
                    if 'responses' in operation:
                        responses = operation['responses']
                        for status_code, response in responses.items():
                            if 'content' in response:
                                content = response['content']
                                if 'application/json' in content:
                                    json_content = content['application/json']
                                    if 'schema' in json_content:
                                        schemas[f"{key} (response {status_code})"] = json_content['schema']
    
    # 提取 components/schemas 中的 schema
    if 'components' in spec and 'schemas' in spec['components']:
        components_schemas = spec['components']['schemas']
        for schema_name, schema in components_schemas.items():
            schemas[f"Component: {schema_name}"] = schema
    
    return schemas

def resolve_refs(schema, spec):
    """
    解析 schema 中的 $ref 引用
    
    Args:
        schema (dict): 包含 $ref 的 schema
        spec (dict): 完整的 OpenAPI 规范
        
    Returns:
        dict: 解析后的 schema
    """
    if isinstance(schema, dict):
        if '$ref' in schema:
            ref = schema['$ref']
            # 处理本地引用
            if ref.startswith('#/'):
                parts = ref[2:].split('/')
                resolved = spec
                for part in parts:
                    resolved = resolved.get(part)
                    if resolved is None:
                        return schema
                return resolved
        else:
            # 递归解析
            for key, value in schema.items():
                schema[key] = resolve_refs(value, spec)
    elif isinstance(schema, list):
        # 递归解析列表
        for i, item in enumerate(schema):
            schema[i] = resolve_refs(item, spec)
    return schema

def extract_schemas_with_resolved_refs(openapi_path):
    """
    提取 schema 并解析 $ref 引用
    
    Args:
        openapi_path (str): OpenAPI 文件路径
        
    Returns:
        dict: 解析后的 schema 字典
    """
    spec = load_openapi_file(openapi_path)
    schemas = extract_schemas_from_openapi(openapi_path)
    
    # 解析引用
    resolved_schemas = {}
    for key, schema in schemas.items():
        resolved_schemas[key] = resolve_refs(schema, spec)
    
    return resolved_schemas
