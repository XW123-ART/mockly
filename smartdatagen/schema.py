import json
import os

def parse_schema(file_path):
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Schema 文件不存在: {file_path}")
    
    # 检查是否为文件
    if not os.path.isfile(file_path):
        raise ValueError(f"提供的路径不是文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"JSON 格式错误: {str(e)}", e.doc, e.pos)

def extract_field_info(schema):
    
    # 检查 schema 类型
    if not isinstance(schema, dict):
        raise TypeError("Schema 必须是字典类型")
    
    field_info_list = []
    
    # 检查 schema 是否包含 properties
    if 'properties' in schema:
        properties = schema['properties']
        
        # 遍历每个字段
        for field_name, field_def in properties.items():
            field_info = {
                'name': field_name,
                'type': field_def.get('type'),
                'format': field_def.get('format'),
                'constraints': {}
            }
            
            # 提取约束信息
            if 'minimum' in field_def:
                field_info['constraints']['minimum'] = field_def['minimum']
            if 'maximum' in field_def:
                field_info['constraints']['maximum'] = field_def['maximum']
            if 'enum' in field_def:
                field_info['constraints']['enum'] = field_def['enum']
            if 'minLength' in field_def:
                field_info['constraints']['minLength'] = field_def['minLength']
            if 'maxLength' in field_def:
                field_info['constraints']['maxLength'] = field_def['maxLength']
            if 'pattern' in field_def:
                field_info['constraints']['pattern'] = field_def['pattern']
            
            # 检查是否为必填字段
            if 'required' in schema and field_name in schema['required']:
                field_info['required'] = True
            else:
                field_info['required'] = False
            
            field_info_list.append(field_info)
    
    return field_info_list