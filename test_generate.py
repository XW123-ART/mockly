#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试按顺序生成数据"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartdatagen.schema import extract_field_info
from smartdatagen.prompt import generate_json_prompt
from smartdatagen.llm import call_llm
from smartdatagen.utils import validate_json

# 测试用的 schema，包含枚举字段
test_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "name": {"type": "string"},
        "category": {"type": "string", "enum": ["electronics", "clothing", "food"]},
        "status": {"type": "string", "enum": ["active", "inactive"]}
    },
    "required": ["name"]
}

def test_sequential_generation():
    """测试按顺序生成 6 条数据"""
    print("=" * 60)
    print("测试: 按顺序生成 6 条数据（测试枚举覆盖）")
    print("=" * 60)

    field_info = extract_field_info(test_schema)

    # 提取枚举字段
    enum_fields = []
    for field in field_info:
        constraints = field.get('constraints', {})
        if 'enum' in constraints:
            enum_fields.append({
                'name': field['name'],
                'values': constraints['enum']
            })

    print(f"枚举字段: {[f['name'] for f in enum_fields]}")
    for ef in enum_fields:
        print(f"  - {ef['name']}: {ef['values']}")
    print()

    results = []
    for i in range(6):
        # 计算枚举提示
        enum_hints = []
        for enum_field in enum_fields:
            field_name = enum_field['name']
            values = enum_field['values']
            if values:
                enum_index = i % len(values)
                enum_value = values[enum_index]
                enum_hints.append(f"{field_name} 字段必须是: '{enum_value}' (枚举值 {enum_index + 1}/{len(values)})")

        prompt = generate_json_prompt(test_schema, sequence=i+1, enum_hints=enum_hints)

        try:
            response = call_llm(prompt)
            is_valid, result = validate_json(response)

            if is_valid:
                results.append(result)
                cat = result.get('category', 'N/A')
                status = result.get('status', 'N/A')
                id_val = result.get('id', 'N/A')
                name = result.get('name', 'N/A')
                print(f"数据 {i+1}: id={id_val}, name={name}, category={cat}, status={status}")
            else:
                print(f"[ERROR] 第 {i+1} 条数据生成失败: {result}")
                return False
        except Exception as e:
            print(f"[ERROR] 第 {i+1} 条生成异常: {e}")
            return False

    # 检查枚举覆盖
    print("\n" + "-" * 60)
    print("枚举覆盖检查:")

    for enum_field in enum_fields:
        field_name = enum_field['name']
        expected_values = set(enum_field['values'])
        actual_values = set(r.get(field_name) for r in results if field_name in r)

        print(f"\n{field_name}:")
        print(f"  期望值: {expected_values}")
        print(f"  实际值: {actual_values}")

        if expected_values.issubset(actual_values):
            print(f"  [OK] 已完全覆盖")
        else:
            missing = expected_values - actual_values
            print(f"  [WARN] 未覆盖: {missing}")

    # 检查 ID 顺序
    print("\n" + "-" * 60)
    print("ID 顺序检查:")
    ids = [r.get('id') for r in results]
    print(f"  ID 列表: {ids}")
    if ids == list(range(1, 7)):
        print("  [OK] ID 按顺序从 1 到 6")
    else:
        print(f"  [WARN] ID 不完全按顺序")

    print("\n[PASS] 测试完成")
    return True

if __name__ == '__main__':
    success = test_sequential_generation()
    sys.exit(0 if success else 1)
