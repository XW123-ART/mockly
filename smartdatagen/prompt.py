import os
import random
import time
from .schema import extract_field_info

def generate_example(schema):
    """根据 schema 生成示例数据"""
    properties = schema.get('properties', {})
    example = {}

    for field_name, field_schema in properties.items():
        field_type = field_schema.get('type')

        if field_type == 'string':
            field_format = field_schema.get('format')
            if field_format == 'email':
                example[field_name] = "user.name@example.com"
            elif field_format == 'date':
                example[field_name] = "2023-01-01"
            elif field_format == 'date-time':
                example[field_name] = "2023-01-01T12:00:00Z"
            elif 'pattern' in field_schema:
                pattern = field_schema['pattern']
                if 'ORD-' in pattern:
                    example[field_name] = "ORD-123456"
                elif 'PAY-' in pattern:
                    example[field_name] = "PAY-12345678"
                elif 'DEV-' in pattern:
                    example[field_name] = "DEV-123456"
                elif 'VIN' in field_name.upper():
                    example[field_name] = "1HGCM82633A004352"
                else:
                    example[field_name] = "example"
            elif 'enum' in field_schema:
                example[field_name] = field_schema['enum'][0]
            else:
                example[field_name] = "example"
        elif field_type == 'integer':
            example[field_name] = 1
        elif field_type == 'number':
            example[field_name] = 1.0
        elif field_type == 'boolean':
            example[field_name] = True

    return example

def generate_json_prompt(schema, seed=None, sequence=1, enum_hints=None):
    """
    生成 JSON 数据的 Prompt

    Args:
        schema: JSON schema 定义
        seed: 随机种子，用于生成不同的数据。如果为 None，则使用当前时间
        sequence: 生成序号，用于按顺序生成（从1开始）
        enum_hints: 枚举字段提示，用于确保枚举覆盖

    Returns:
        str: 生成的 prompt 文本
    """
    # 检查 schema 类型
    if not isinstance(schema, dict):
        raise TypeError("Schema 必须是字典类型")

    # 处理数组类型的 schema
    if schema.get('type') == 'array' and 'items' in schema:
        # 使用 items 中的 schema
        return generate_json_prompt(schema['items'], seed)

    # 检查 schema 是否包含 properties
    if 'properties' not in schema:
        raise ValueError("Schema 必须包含 properties 字段")

    try:
        # 提取字段信息
        field_info = extract_field_info(schema)

        # 检查是否有字段信息
        if not field_info:
            raise ValueError("Schema 中没有字段信息")

        # 构建字段描述
        field_descriptions = []
        for field in field_info:
            desc = f"- {field['name']}: {field['type']}"
            if field['format']:
                desc += f" (格式: {field['format']})"
            if field['required']:
                desc += " (必填)"
            if field['constraints']:
                constraints = []
                if 'minimum' in field['constraints']:
                    constraints.append(f"最小值: {field['constraints']['minimum']}")
                if 'maximum' in field['constraints']:
                    constraints.append(f"最大值: {field['constraints']['maximum']}")
                if 'minLength' in field['constraints']:
                    constraints.append(f"最小长度: {field['constraints']['minLength']}")
                if 'maxLength' in field['constraints']:
                    constraints.append(f"最大长度: {field['constraints']['maxLength']}")
                if 'enum' in field['constraints']:
                    constraints.append(f"枚举值: {field['constraints']['enum']}")
                if 'pattern' in field['constraints']:
                    constraints.append(f"正则模式: {field['constraints']['pattern']}")
                if constraints:
                    desc += "，约束: " + "、".join(constraints)
            field_descriptions.append(desc)

        # 生成示例数据
        example = generate_example(schema)
        import json
        example_json = json.dumps(example, ensure_ascii=False, indent=2)

        # 读取优化后的 Prompt 模板
        template_path = os.path.join(os.path.dirname(__file__), '..', 'prompt_templates', 'v2.txt')
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 替换模板中的占位符
        prompt = template.replace('{field_descriptions}', '\n'.join(field_descriptions))
        prompt = prompt.replace('{example}', example_json)
        prompt = prompt.replace('{sequence}', str(sequence))

        # 添加枚举覆盖提示
        if enum_hints:
            prompt += "\n\n【枚举覆盖要求】\n"
            for hint in enum_hints:
                prompt += f"- {hint}\n"

        # 添加顺序生成要求
        prompt += f"""\n\n【顺序生成要求】
- 本次是第 {sequence} 条数据
- ID 字段必须是: {sequence}
- 所有数值字段按顺序递增

只返回 JSON 数据，不要添加任何其他文本。\n"""

        return prompt

    except Exception as e:
        # 处理异常
        raise Exception(f"生成 Prompt 时发生错误: {str(e)}")
