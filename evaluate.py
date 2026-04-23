import os
import json
import re
from datetime import datetime

# 添加当前目录到Python路径
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartdatagen.schema import parse_schema
from smartdatagen.prompt import generate_json_prompt
from smartdatagen.llm import call_llm
from smartdatagen.utils import validate_json

def load_eval_data():
    """加载评估测试集数据"""
    eval_dir = os.path.join(os.path.dirname(__file__), 'eval')
    test_cases = []
    
    # 遍历 eval 目录中的文件
    for file in os.listdir(eval_dir):
        if file.endswith('_schema.json'):
            # 提取测试名称
            name = file.replace('_schema.json', '')
            schema_path = os.path.join(eval_dir, file)
            expected_path = os.path.join(eval_dir, f'{name}_expected.json')
            
            if os.path.exists(expected_path):
                # 加载 schema
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                # 加载期望数据
                with open(expected_path, 'r', encoding='utf-8') as f:
                    expected_data = json.load(f)
                
                test_cases.append({
                    'name': name,
                    'schema': schema,
                    'expected_data': expected_data,
                    'count': len(expected_data)
                })
    
    return test_cases

def generate_test_data(schema, count):
    """生成测试数据"""
    generated_data = []
    
    for i in range(count):
        try:
            # 生成 Prompt
            prompt = generate_json_prompt(schema)
            
            # 调用 LLM
            response = call_llm(prompt)
            
            # 验证 JSON
            is_valid, result = validate_json(response)
            if is_valid:
                generated_data.append(result)
            else:
                print(f"  生成失败: {result}")
        except Exception as e:
            print(f"  生成过程中发生错误: {e}")
    
    return generated_data

def validate_field(field_name, field_value, field_schema):
    """验证单个字段"""
    # 检查字段是否存在
    if field_value is None:
        return False, "字段值为 None"
    
    # 检查类型
    expected_type = field_schema.get('type')
    if expected_type == 'string' and not isinstance(field_value, str):
        return False, f"类型错误: 期望字符串，实际为 {type(field_value).__name__}"
    elif expected_type == 'integer' and not isinstance(field_value, int):
        return False, f"类型错误: 期望整数，实际为 {type(field_value).__name__}"
    elif expected_type == 'number' and not isinstance(field_value, (int, float)):
        return False, f"类型错误: 期望数字，实际为 {type(field_value).__name__}"
    elif expected_type == 'boolean' and not isinstance(field_value, bool):
        return False, f"类型错误: 期望布尔值，实际为 {type(field_value).__name__}"
    
    # 检查格式
    field_format = field_schema.get('format')
    if field_format == 'email' and isinstance(field_value, str):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, field_value):
            return False, f"邮箱格式错误: {field_value}"
    elif field_format == 'date' and isinstance(field_value, str):
        try:
            datetime.strptime(field_value, '%Y-%m-%d')
        except ValueError:
            return False, f"日期格式错误: {field_value}"
    elif field_format == 'date-time' and isinstance(field_value, str):
        try:
            datetime.fromisoformat(field_value.replace('Z', '+00:00'))
        except ValueError:
            return False, f"日期时间格式错误: {field_value}"
    
    # 检查约束
    constraints = field_schema
    if 'minimum' in constraints and isinstance(field_value, (int, float)):
        if field_value < constraints['minimum']:
            return False, f"值小于最小值: {field_value} < {constraints['minimum']}"
    if 'maximum' in constraints and isinstance(field_value, (int, float)):
        if field_value > constraints['maximum']:
            return False, f"值大于最大值: {field_value} > {constraints['maximum']}"
    if 'minLength' in constraints and isinstance(field_value, str):
        if len(field_value) < constraints['minLength']:
            return False, f"长度小于最小长度: {len(field_value)} < {constraints['minLength']}"
    if 'maxLength' in constraints and isinstance(field_value, str):
        if len(field_value) > constraints['maxLength']:
            return False, f"长度大于最大长度: {len(field_value)} > {constraints['maxLength']}"
    if 'pattern' in constraints and isinstance(field_value, str):
        pattern = constraints['pattern']
        if not re.match(pattern, field_value):
            return False, f"模式匹配失败: {field_value} 不符合 {pattern}"
    if 'enum' in constraints:
        if field_value not in constraints['enum']:
            return False, f"值不在枚举列表中: {field_value} 不在 {constraints['enum']}"
    
    return True, ""

def evaluate_data(generated_data, expected_data, schema):
    """评估生成的数据"""
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    total_fields = 0
    correct_fields = 0
    fully_correct_records = 0
    
    for i, (generated, expected) in enumerate(zip(generated_data, expected_data)):
        record_correct = True
        
        # 检查所有期望的字段
        for field_name, field_schema in properties.items():
            total_fields += 1
            
            # 检查字段是否存在
            if field_name not in generated:
                if field_name in required_fields:
                    print(f"  记录 {i+1}: 缺少必填字段 {field_name}")
                    record_correct = False
                else:
                    # 非必填字段，跳过
                    correct_fields += 1
                continue
            
            # 验证字段值
            field_value = generated[field_name]
            is_valid, error_msg = validate_field(field_name, field_value, field_schema)
            if is_valid:
                correct_fields += 1
            else:
                print(f"  记录 {i+1}: 字段 {field_name} 验证失败: {error_msg}")
                record_correct = False
        
        if record_correct:
            fully_correct_records += 1
    
    # 计算准确率
    if total_fields > 0:
        overall_accuracy = correct_fields / total_fields
    else:
        overall_accuracy = 0.0
    
    if len(expected_data) > 0:
        fully_correct_rate = fully_correct_records / len(expected_data)
    else:
        fully_correct_rate = 0.0
    
    return {
        'total_fields': total_fields,
        'correct_fields': correct_fields,
        'overall_accuracy': overall_accuracy,
        'fully_correct_records': fully_correct_records,
        'total_records': len(expected_data),
        'fully_correct_rate': fully_correct_rate
    }

def main():
    """主函数"""
    print("开始评估...")
    
    # 加载评估数据
    test_cases = load_eval_data()
    print(f"加载了 {len(test_cases)} 个测试用例")
    
    overall_results = {
        'total_fields': 0,
        'correct_fields': 0,
        'total_records': 0,
        'fully_correct_records': 0
    }
    
    # 遍历测试用例
    for test_case in test_cases:
        name = test_case['name']
        schema = test_case['schema']
        expected_data = test_case['expected_data']
        count = test_case['count']
        
        print(f"\n=== 测试 {name} ===")
        print(f"期望生成 {count} 条数据")
        
        # 生成测试数据
        generated_data = generate_test_data(schema, count)
        print(f"实际生成 {len(generated_data)} 条数据")
        
        if len(generated_data) < count:
            print(f"警告: 生成的数据数量不足，期望 {count} 条，实际 {len(generated_data)} 条")
            # 只评估生成的数据
            expected_data = expected_data[:len(generated_data)]
        
        # 评估数据
        if generated_data and expected_data:
            results = evaluate_data(generated_data, expected_data, schema)
            
            print(f"\n评估结果:")
            print(f"  总字段数: {results['total_fields']}")
            print(f"  正确字段数: {results['correct_fields']}")
            print(f"  总体准确率: {results['overall_accuracy']:.2%}")
            print(f"  完全正确的记录数: {results['fully_correct_records']}/{results['total_records']}")
            print(f"  完全正确的比例: {results['fully_correct_rate']:.2%}")
            
            # 累计总体结果
            overall_results['total_fields'] += results['total_fields']
            overall_results['correct_fields'] += results['correct_fields']
            overall_results['total_records'] += results['total_records']
            overall_results['fully_correct_records'] += results['fully_correct_records']
        else:
            print("  无法评估: 生成的数据或期望数据为空")
    
    # 输出总体结果
    print("\n=== 总体评估结果 ===")
    if overall_results['total_fields'] > 0:
        overall_accuracy = overall_results['correct_fields'] / overall_results['total_fields']
    else:
        overall_accuracy = 0.0
    
    if overall_results['total_records'] > 0:
        fully_correct_rate = overall_results['fully_correct_records'] / overall_results['total_records']
    else:
        fully_correct_rate = 0.0
    
    print(f"总字段数: {overall_results['total_fields']}")
    print(f"正确字段数: {overall_results['correct_fields']}")
    print(f"总体准确率: {overall_accuracy:.2%}")
    print(f"完全正确的记录数: {overall_results['fully_correct_records']}/{overall_results['total_records']}")
    print(f"完全正确的比例: {fully_correct_rate:.2%}")

if __name__ == '__main__':
    main()