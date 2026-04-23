import json
import os
import sys
import tempfile
import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smartdatagen.schema import parse_schema, extract_field_info


def test_parse_schema_valid():
    """测试解析有效的 schema 文件"""
    # 创建临时 schema 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }, f)
        temp_file = f.name
    
    try:
        # 测试解析
        schema = parse_schema(temp_file)
        assert isinstance(schema, dict)
        assert schema['type'] == 'object'
        assert 'properties' in schema
    finally:
        # 清理临时文件
        os.unlink(temp_file)


def test_parse_schema_nonexistent():
    """测试解析不存在的文件"""
    with pytest.raises(FileNotFoundError):
        parse_schema('non_existent_file.json')


def test_parse_schema_invalid_json():
    """测试解析无效的 JSON 文件"""
    # 创建包含无效 JSON 的临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json')
        temp_file = f.name
    
    try:
        with pytest.raises(json.JSONDecodeError):
            parse_schema(temp_file)
    finally:
        os.unlink(temp_file)


def test_extract_field_info_normal():
    """测试提取正常 schema 的字段信息"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 2, "maxLength": 50},
            "age": {"type": "integer", "minimum": 0, "maximum": 120},
            "email": {"type": "string", "format": "email"}
        },
        "required": ["name", "email"]
    }
    
    field_info = extract_field_info(schema)
    
    assert len(field_info) == 3
    
    # 检查 name 字段
    name_field = next(f for f in field_info if f['name'] == 'name')
    assert name_field['type'] == 'string'
    assert name_field['required'] == True
    assert name_field['constraints']['minLength'] == 2
    assert name_field['constraints']['maxLength'] == 50
    
    # 检查 age 字段
    age_field = next(f for f in field_info if f['name'] == 'age')
    assert age_field['type'] == 'integer'
    assert age_field['required'] == False
    assert age_field['constraints']['minimum'] == 0
    assert age_field['constraints']['maximum'] == 120
    
    # 检查 email 字段
    email_field = next(f for f in field_info if f['name'] == 'email')
    assert email_field['type'] == 'string'
    assert email_field['format'] == 'email'
    assert email_field['required'] == True


def test_extract_field_info_with_enum():
    """测试提取带枚举的 schema 字段信息"""
    schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "inactive", "pending"]
            },
            "role": {
                "type": "string",
                "enum": ["admin", "user", "guest"]
            }
        }
    }
    
    field_info = extract_field_info(schema)
    
    assert len(field_info) == 2
    
    # 检查 status 字段
    status_field = next(f for f in field_info if f['name'] == 'status')
    assert status_field['type'] == 'string'
    assert status_field['constraints']['enum'] == ["active", "inactive", "pending"]
    
    # 检查 role 字段
    role_field = next(f for f in field_info if f['name'] == 'role')
    assert role_field['type'] == 'string'
    assert role_field['constraints']['enum'] == ["admin", "user", "guest"]


def test_extract_field_info_empty():
    """测试提取空 schema 的字段信息"""
    # 空 schema
    empty_schema = {}
    field_info = extract_field_info(empty_schema)
    assert len(field_info) == 0
    
    # 没有 properties 的 schema
    no_properties_schema = {"type": "object"}
    field_info = extract_field_info(no_properties_schema)
    assert len(field_info) == 0


def test_extract_field_info_invalid_schema():
    """测试提取无效 schema 的字段信息"""
    # 非字典类型的 schema
    with pytest.raises(TypeError):
        extract_field_info("not a dict")
    
    with pytest.raises(TypeError):
        extract_field_info(123)
    
    with pytest.raises(TypeError):
        extract_field_info(None)
