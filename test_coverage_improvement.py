#!/usr/bin/env python
"""
测试覆盖率改进效果
对比普通生成 vs 覆盖率优化生成
"""
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartdatagen.coverage import CoverageTracker, calculate_coverage, generate_coverage_report
from smartdatagen.generator import (
    generate_coverage_optimized_data,
    inject_boundary_values,
    inject_enum_values
)


def test_inject_functions():
    """测试注入函数"""
    print("=" * 60)
    print("测试1: 边界值注入函数")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "age": {"type": "integer", "minimum": 0, "maximum": 120},
            "id": {"type": "integer", "minimum": 1}
        }
    }

    data = {"age": 25, "id": 100}
    missing_boundaries = [
        {"field": "age", "boundary_type": "min", "value": 0},
        {"field": "age", "boundary_type": "max", "value": 120}
    ]

    print(f"原始数据: {data}")
    print(f"未覆盖边界: {missing_boundaries}")

    result = inject_boundary_values(data, schema, missing_boundaries)
    print(f"注入后数据: {result}")

    # 验证是否注入了边界值
    if result["age"] in [0, 120]:
        print("[OK] 边界值注入成功!")
    else:
        print("[FAIL] 边界值注入失败")

    print()


def test_enum_inject():
    """测试枚举值注入"""
    print("=" * 60)
    print("测试2: 枚举值注入函数")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["active", "inactive", "pending"]}
        }
    }

    data = {"status": "active"}
    missing_enums = [
        {"field": "status", "values": ["inactive", "pending"]}
    ]

    print(f"原始数据: {data}")
    print(f"未覆盖枚举: {missing_enums}")

    result = inject_enum_values(data, schema, missing_enums)
    print(f"注入后数据: {result}")

    if result["status"] in ["inactive", "pending"]:
        print("[OK] 枚举值注入成功!")
    else:
        print("[FAIL] 枚举值注入失败")

    print()


def test_coverage_tracker():
    """测试覆盖率跟踪器"""
    print("=" * 60)
    print("测试3: 覆盖率跟踪器")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1, "maximum": 100},
            "status": {"type": "string", "enum": ["active", "inactive"]}
        }
    }

    tracker = CoverageTracker(schema)

    # 模拟生成数据
    test_data = [
        {"id": 50, "status": "active"},      # 普通值
        {"id": 1, "status": "active"},       # 边界值：id最小值
        {"id": 100, "status": "inactive"},   # 边界值：id最大值 + 枚举值
    ]

    print("生成数据:")
    for i, data in enumerate(test_data):
        print(f"  {i+1}. {data}")
        tracker.update(data)

    coverage = tracker.get_coverage()
    print(f"\n覆盖率统计:")
    print(f"  字段覆盖: {coverage['field_coverage']:.1%}")
    print(f"  边界覆盖: {coverage['boundary_coverage']:.1%}")
    print(f"  枚举覆盖: {coverage['enum_coverage']:.1%}")

    # 检查未覆盖的场景
    missing = tracker.get_missing()
    print(f"\n未覆盖场景: {missing}")

    print()


def test_manual_coverage_improvement():
    """手动模拟覆盖率优化过程"""
    print("=" * 60)
    print("测试4: 手动模拟覆盖率优化")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "age": {"type": "integer", "minimum": 0, "maximum": 120},
            "status": {"type": "string", "enum": ["active", "inactive", "pending"]}
        }
    }

    tracker = CoverageTracker(schema)

    # 阶段1：普通生成（模拟LLM生成）
    print("阶段1: 普通生成")
    normal_data = [
        {"age": 25, "status": "active"},
        {"age": 30, "status": "active"},
        {"age": 35, "status": "active"}
    ]

    for data in normal_data:
        tracker.update(data)

    coverage = tracker.get_coverage()
    print(f"  生成 {len(normal_data)} 条数据")
    print(f"  字段覆盖: {coverage['field_coverage']:.1%}")
    print(f"  边界覆盖: {coverage['boundary_coverage']:.1%}")
    print(f"  枚举覆盖: {coverage['enum_coverage']:.1%}")

    # 阶段2：注入边界值
    print("\n阶段2: 注入边界值")
    missing = tracker.get_missing()

    for boundary_info in missing['boundaries']:
        modified_data = normal_data[0].copy()
        modified_data[boundary_info['field']] = boundary_info['value']
        tracker.update(modified_data)
        print(f"  注入: {boundary_info['field']} = {boundary_info['value']}")

    coverage = tracker.get_coverage()
    print(f"  边界覆盖: {coverage['boundary_coverage']:.1%}")

    # 阶段3：注入枚举值
    print("\n阶段3: 注入枚举值")

    for enum_info in missing['enums']:
        for value in enum_info['values']:
            modified_data = normal_data[0].copy()
            modified_data[enum_info['field']] = value
            tracker.update(modified_data)
            print(f"  注入: {enum_info['field']} = {value}")

    coverage = tracker.get_coverage()
    print(f"  枚举覆盖: {coverage['enum_coverage']:.1%}")

    # 最终结果
    print("\n最终结果:")
    print(f"  总数据量: {len(normal_data) + len(missing['boundaries']) + sum(len(e['values']) for e in missing['enums'])}")
    print(f"  字段覆盖: {coverage['field_coverage']:.1%}")
    print(f"  边界覆盖: {coverage['boundary_coverage']:.1%}")
    print(f"  枚举覆盖: {coverage['enum_coverage']:.1%}")

    if coverage['boundary_coverage'] == 1.0 and coverage['enum_coverage'] == 1.0:
        print("\n[OK] 覆盖率优化成功! 所有边界和枚举都已覆盖")
    else:
        print("\n[FAIL] 还有未覆盖的场景")

    print()


def generate_report_demo():
    """生成覆盖率报告示例"""
    print("=" * 60)
    print("测试5: 覆盖率报告示例")
    print("=" * 60)

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1, "maximum": 1000},
            "age": {"type": "integer", "minimum": 0, "maximum": 120},
            "status": {"type": "string", "enum": ["active", "inactive", "pending"]}
        }
    }

    # 模拟覆盖率优化前后的数据
    # 优化前：只有普通值
    data_before = [
        {"id": 50, "age": 25, "status": "active"},
        {"id": 60, "age": 30, "status": "active"}
    ]

    # 优化后：包含边界值和所有枚举值
    data_after = [
        {"id": 50, "age": 25, "status": "active"},
        {"id": 60, "age": 30, "status": "active"},
        {"id": 1, "age": 0, "status": "inactive"},      # 边界+枚举
        {"id": 1000, "age": 120, "status": "pending"}    # 边界+枚举
    ]

    print("\n【优化前】")
    coverage_before = calculate_coverage(data_before, schema)
    report_before = generate_coverage_report(coverage_before, "优化前")
    print(report_before)

    print("\n【优化后】")
    coverage_after = calculate_coverage(data_after, schema)
    report_after = generate_coverage_report(coverage_after, "优化后")
    print(report_after)

    print("\n对比:")
    print(f"  边界覆盖: {coverage_before['boundary_coverage']:.0%} → {coverage_after['boundary_coverage']:.0%}")
    print(f"  枚举覆盖: {coverage_before['enum_coverage']:.0%} → {coverage_after['enum_coverage']:.0%}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("覆盖率改进功能测试")
    print("=" * 60 + "\n")

    test_inject_functions()
    test_enum_inject()
    test_coverage_tracker()
    test_manual_coverage_improvement()
    generate_report_demo()

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
