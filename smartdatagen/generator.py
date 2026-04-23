import random
import string
import json
from .coverage import CoverageTracker
from .prompt import generate_json_prompt
from .llm import call_llm
from .utils import validate_json

def mutate_type(value, field_type):
    """
    类型变异算子
    
    Args:
        value: 原始值
        field_type: 字段类型
        
    Returns:
        list: 变异后的值列表
    """
    mutations = []
    
    if field_type == 'string':
        # 字符串变为数字
        try:
            # 尝试转换为整数
            num_value = int(value)
            mutations.append(num_value)
        except (ValueError, TypeError):
            pass
        # 字符串变为布尔值
        mutations.append(True)
        mutations.append(False)
    
    elif field_type == 'integer' or field_type == 'number':
        # 数字变为字符串
        mutations.append(str(value))
        # 数字变为布尔值
        mutations.append(bool(value))
    
    elif field_type == 'boolean':
        # 布尔值翻转
        mutations.append(not value)
        # 布尔值变为数字
        mutations.append(1 if value else 0)
        # 布尔值变为字符串
        mutations.append(str(value))
    
    return mutations

def mutate_boundary(value, field_type, constraints):
    """
    边界变异算子
    
    Args:
        value: 原始值
        field_type: 字段类型
        constraints: 字段约束
        
    Returns:
        list: 变异后的值列表
    """
    mutations = []
    
    if field_type in ['integer', 'number'] and isinstance(value, (int, float)):
        # 检查是否有最小值约束
        if 'minimum' in constraints:
            min_val = constraints['minimum']
            mutations.extend([min_val - 1, min_val, min_val + 1])
        
        # 检查是否有最大值约束
        if 'maximum' in constraints:
            max_val = constraints['maximum']
            mutations.extend([max_val - 1, max_val, max_val + 1])
    
    elif field_type == 'string' and isinstance(value, str):
        # 字符串长度边界
        if 'minLength' in constraints:
            min_len = constraints['minLength']
            if min_len > 0:
                mutations.append('a' * (min_len - 1))
            mutations.append('a' * min_len)
            mutations.append('a' * (min_len + 1))
        
        if 'maxLength' in constraints:
            max_len = constraints['maxLength']
            if max_len > 0:
                mutations.append('a' * (max_len - 1))
            mutations.append('a' * max_len)
            mutations.append('a' * (max_len + 1))
    
    return mutations

def mutate_null(value, field_type):
    """
    空值变异算子
    
    Args:
        value: 原始值
        field_type: 字段类型
        
    Returns:
        list: 变异后的值列表
    """
    mutations = [None]
    
    if field_type == 'string':
        mutations.append('')
    
    return mutations

def mutate_enum(value, field_type, constraints):
    """
    枚举变异算子
    
    Args:
        value: 原始值
        field_type: 字段类型
        constraints: 字段约束
        
    Returns:
        list: 变异后的值列表
    """
    mutations = []
    
    if 'enum' in constraints:
        enum_values = constraints['enum']
        # 从枚举中选择不同的值
        for enum_val in enum_values:
            if enum_val != value:
                mutations.append(enum_val)
        
        # 尝试不在枚举中的值
        if field_type == 'string':
            mutations.append('non_enum_value')
        elif field_type == 'integer':
            mutations.append(999999)
        elif field_type == 'boolean':
            mutations.append('not_a_boolean')
    
    return mutations

def mutate_string(value, field_type, constraints):
    """
    字符串变异算子
    
    Args:
        value: 原始值
        field_type: 字段类型
        constraints: 字段约束
        
    Returns:
        list: 变异后的值列表
    """
    mutations = []
    
    if field_type == 'string' and isinstance(value, str):
        # 超长字符串
        mutations.append('a' * 500)
        
        # 特殊字符
        special_chars = '@#$%^&*()_+[]{}|;:,.<>?"'
        mutations.append(special_chars)
        
        # Unicode 表情符号
        mutations.append('Hello 😊 World 🌍')
        
        # 随机字符串
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        mutations.append(random_str)
    
    return mutations

def mutate_logic(original_data, field_map):
    """
    逻辑变异算子，违反字段间依赖关系
    
    Args:
        original_data: 原始数据
        field_map: 字段信息映射
        
    Returns:
        list: 变异后的数据列表
    """
    mutations = []
    
    # 检查是否有开始时间和结束时间字段
    if 'start_time' in original_data and 'end_time' in original_data:
        # 生成结束时间早于开始时间的变异
        mutated = original_data.copy()
        mutated['start_time'] = '2023-12-31T23:59:59Z'
        mutated['end_time'] = '2023-01-01T00:00:00Z'
        mutations.append(mutated)
    
    # 检查是否有年龄和职位字段
    if 'age' in original_data and 'position' in original_data:
        # 生成年龄<18但职位为CEO的变异
        mutated = original_data.copy()
        mutated['age'] = 17
        mutated['position'] = 'CEO'
        mutations.append(mutated)
    
    # 检查是否有价格和库存字段
    if 'price' in original_data and 'stock' in original_data:
        # 生成价格为负但库存为正的变异
        mutated = original_data.copy()
        mutated['price'] = -100
        mutated['stock'] = 10
        mutations.append(mutated)
    
    return mutations

def mutate_combination(original_data, field_map):
    """
    组合变异算子，同时变异多个字段
    
    Args:
        original_data: 原始数据
        field_map: 字段信息映射
        
    Returns:
        list: 变异后的数据列表
    """
    mutations = []
    
    # 价格=0且库存=0的组合
    if 'price' in original_data and 'stock' in original_data:
        mutated = original_data.copy()
        mutated['price'] = 0
        mutated['stock'] = 0
        mutations.append(mutated)
    
    # 年龄=0且职位=Senior的组合
    if 'age' in original_data and 'position' in original_data:
        mutated = original_data.copy()
        mutated['age'] = 0
        mutated['position'] = 'Senior'
        mutations.append(mutated)
    
    # 评分=0且状态=active的组合
    if 'score' in original_data and 'status' in original_data:
        mutated = original_data.copy()
        mutated['score'] = 0
        mutated['status'] = 'active'
        mutations.append(mutated)
    
    return mutations

def mutate_business(original_data, field_map):
    """
    业务语义变异算子，针对特定字段生成不可能的组合
    
    Args:
        original_data: 原始数据
        field_map: 字段信息映射
        
    Returns:
        list: 变异后的数据列表
    """
    mutations = []
    
    # 订单状态变异：已发货但未支付
    if 'order_status' in original_data and 'payment_status' in original_data:
        mutated = original_data.copy()
        mutated['order_status'] = 'shipped'
        mutated['payment_status'] = 'unpaid'
        mutations.append(mutated)
    
    # 订单状态变异：已取消但已支付
    if 'order_status' in original_data and 'payment_status' in original_data:
        mutated = original_data.copy()
        mutated['order_status'] = 'cancelled'
        mutated['payment_status'] = 'paid'
        mutations.append(mutated)
    
    # 用户状态变异：已禁用但已验证
    if 'user_status' in original_data and 'verified' in original_data:
        mutated = original_data.copy()
        mutated['user_status'] = 'disabled'
        mutated['verified'] = True
        mutations.append(mutated)
    
    return mutations

def apply_mutations(original_data, field_info):
    """
    应用变异算子到原始数据
    
    Args:
        original_data (dict): 原始生成的数据
        field_info (list): 字段信息列表
        
    Returns:
        list: 包含变异后数据的列表
    """
    mutated_data_list = []
    
    # 创建字段名到字段信息的映射
    field_map = {field['name']: field for field in field_info}
    
    # 应用逻辑变异
    logic_mutations = mutate_logic(original_data, field_map)
    mutated_data_list.extend(logic_mutations)
    
    # 应用组合变异
    combination_mutations = mutate_combination(original_data, field_map)
    mutated_data_list.extend(combination_mutations)
    
    # 应用业务语义变异
    business_mutations = mutate_business(original_data, field_map)
    mutated_data_list.extend(business_mutations)
    
    # 对每个字段应用变异
    for field_name, field_info_item in field_map.items():
        if field_name not in original_data:
            continue
        
        original_value = original_data[field_name]
        field_type = field_info_item.get('type')
        constraints = field_info_item.get('constraints', {})
        
        # 收集所有变异
        all_mutations = []
        
        # 应用类型变异
        type_mutations = mutate_type(original_value, field_type)
        all_mutations.extend(type_mutations)
        
        # 应用边界变异
        boundary_mutations = mutate_boundary(original_value, field_type, constraints)
        all_mutations.extend(boundary_mutations)
        
        # 应用空值变异
        null_mutations = mutate_null(original_value, field_type)
        all_mutations.extend(null_mutations)
        
        # 应用枚举变异
        enum_mutations = mutate_enum(original_value, field_type, constraints)
        all_mutations.extend(enum_mutations)
        
        # 应用字符串变异
        string_mutations = mutate_string(original_value, field_type, constraints)
        all_mutations.extend(string_mutations)
        
        # 为每个变异创建新的数据副本
        for mutation in all_mutations:
            # 创建数据副本
            mutated_data = original_data.copy()
            # 应用变异
            mutated_data[field_name] = mutation
            # 添加到结果列表
            mutated_data_list.append(mutated_data)
    
    return mutated_data_list

def generate_mutated_data(original_data, field_info, max_mutations=20):
    """
    生成变异数据，限制最大变异数量
    
    Args:
        original_data (dict): 原始生成的数据
        field_info (list): 字段信息列表
        max_mutations (int): 最大变异数量
        
    Returns:
        list: 包含变异后数据的列表
    """
    all_mutations = apply_mutations(original_data, field_info)
    
    # 去重
    unique_mutations = []
    seen = set()
    
    for mutation in all_mutations:
        # 将字典转换为字符串以进行去重
        mutation_str = json.dumps(mutation, sort_keys=True)
        if mutation_str not in seen:
            seen.add(mutation_str)
            unique_mutations.append(mutation)
    
    # 限制数量
    return unique_mutations[:max_mutations]

def inject_boundary_values(data, schema, missing_boundaries):
    """
    向数据中注入边界值，确保边界覆盖

    Args:
        data: 原始数据
        schema: JSON schema
        missing_boundaries: 未覆盖的边界列表

    Returns:
        修改后的数据（如果注入成功）
    """
    if not missing_boundaries or not data:
        return data

    # 复制数据避免修改原始值
    modified_data = data.copy()

    # 随机选择一个未覆盖的边界进行注入
    import random
    boundary_to_inject = random.choice(missing_boundaries)
    field = boundary_to_inject['field']
    boundary_type = boundary_to_inject['boundary_type']
    value = boundary_to_inject['value']

    if field in modified_data:
        # 注入边界值
        modified_data[field] = value
        print(f"  [注入边界值] {field}.{boundary_type} = {value}")
        return modified_data

    return data


def inject_enum_values(data, schema, missing_enums):
    """
    向数据中注入枚举值，确保枚举覆盖

    Args:
        data: 原始数据
        schema: JSON schema
        missing_enums: 未覆盖的枚举列表

    Returns:
        修改后的数据（如果注入成功）
    """
    if not missing_enums or not data:
        return data

    # 复制数据避免修改原始值
    modified_data = data.copy()

    # 随机选择一个未覆盖的枚举字段进行注入
    import random
    enum_to_inject = random.choice(missing_enums)
    field = enum_to_inject['field']
    values = enum_to_inject['values']

    if field in modified_data and values:
        # 随机选择一个未覆盖的枚举值
        value_to_inject = random.choice(values)
        modified_data[field] = value_to_inject
        print(f"  [注入枚举值] {field} = {value_to_inject}")
        return modified_data

    return data


def generate_coverage_optimized_data(schema, target_count):
    """
    生成优化覆盖率的数据，强制包含边界值和枚举值

    Args:
        schema: JSON schema
        target_count: 目标数量

    Returns:
        生成的数据列表
    """
    from .schema import extract_field_info

    print(f"[覆盖率优化生成] 目标数量: {target_count}")

    coverage_tracker = CoverageTracker(schema)
    generated_data = []
    field_info = extract_field_info(schema)

    # 计算需要覆盖的边界和枚举总数
    total_boundaries = sum(
        1 for field in field_info
        for _ in field.get('constraints', {}).items()
        if _[0] in ['minimum', 'maximum']
    )
    total_enums = sum(
        len(field.get('constraints', {}).get('enum', []))
        for field in field_info
    )

    print(f"  需要覆盖的边界: {total_boundaries}, 枚举值: {total_enums}")

    # 第一批：生成基础数据
    base_count = min(target_count // 2, 5)
    for i in range(base_count):
        prompt = generate_json_prompt(schema)
        response = call_llm(prompt)
        is_valid, result = validate_json(response)

        if is_valid:
            generated_data.append(result)
            coverage_tracker.update(result)

    print(f"  基础数据生成: {len(generated_data)} 条")

    # 第二批：针对性补充未覆盖的场景
    attempts = 0
    max_attempts = target_count * 2

    while len(generated_data) < target_count and attempts < max_attempts:
        attempts += 1
        missing = coverage_tracker.get_missing()

        # 生成一条基础数据
        prompt = generate_json_prompt(schema)
        response = call_llm(prompt)
        is_valid, result = validate_json(response)

        if not is_valid:
            continue

        # 检查是否需要注入边界值
        if missing['boundaries'] and len(generated_data) < target_count:
            boundary_data = inject_boundary_values(result, schema, missing['boundaries'])
            if boundary_data != result:
                generated_data.append(boundary_data)
                coverage_tracker.update(boundary_data)
                continue

        # 检查是否需要注入枚举值
        if missing['enums'] and len(generated_data) < target_count:
            enum_data = inject_enum_values(result, schema, missing['enums'])
            if enum_data != result:
                generated_data.append(enum_data)
                coverage_tracker.update(enum_data)
                continue

        # 如果没有注入，添加原始数据
        data_str = json.dumps(result, sort_keys=True)
        if data_str not in [json.dumps(d, sort_keys=True) for d in generated_data]:
            generated_data.append(result)
            coverage_tracker.update(result)

    # 第三批：如果还有未覆盖的场景，强制生成
    missing = coverage_tracker.get_missing()

    # 强制补充边界值
    for boundary_info in missing.get('boundaries', []):
        if len(generated_data) >= target_count:
            break

        # 复制最后一条数据进行修改
        if generated_data:
            base_data = generated_data[-1].copy()
        else:
            # 生成一条基础数据
            prompt = generate_json_prompt(schema)
            response = call_llm(prompt)
            is_valid, base_data = validate_json(response)
            if not is_valid:
                continue

        modified = inject_boundary_values(base_data, schema, [boundary_info])
        if modified != base_data:
            generated_data.append(modified)
            coverage_tracker.update(modified)

    # 强制补充枚举值
    for enum_info in missing.get('enums', []):
        if len(generated_data) >= target_count:
            break

        for enum_value in enum_info.get('values', []):
            if len(generated_data) >= target_count:
                break

            if generated_data:
                base_data = generated_data[-1].copy()
            else:
                prompt = generate_json_prompt(schema)
                response = call_llm(prompt)
                is_valid, base_data = validate_json(response)
                if not is_valid:
                    continue

            if enum_info['field'] in base_data:
                base_data[enum_info['field']] = enum_value
                generated_data.append(base_data)
                coverage_tracker.update(base_data)

    print(f"[覆盖率优化完成] 生成: {len(generated_data)} 条")
    coverage = coverage_tracker.get_coverage()
    print(f"  最终覆盖率: 字段={coverage['field_coverage']:.2%}, 边界={coverage['boundary_coverage']:.2%}, 枚举={coverage['enum_coverage']:.2%}")

    return generated_data, coverage_tracker


def generate_with_coverage(schema, target_count, coverage_tracker=None):
    """
    基于覆盖率反馈的智能生成（改进版）

    Args:
        schema: JSON schema 定义
        target_count: 目标生成数量
        coverage_tracker: 覆盖率跟踪器，如果为 None 则创建新的

    Returns:
        tuple: (生成的数据列表, 覆盖率跟踪器)
    """
    try:
        print(f"开始智能生成，目标数量: {target_count}")

        if coverage_tracker is None:
            coverage_tracker = CoverageTracker(schema)

        generated_data = []
        max_attempts = target_count * 3
        attempts = 0

        while len(generated_data) < target_count and attempts < max_attempts:
            attempts += 1

            # 获取未覆盖的场景
            missing = coverage_tracker.get_missing()

            # 生成基础数据
            base_prompt = generate_json_prompt(schema)

            # 添加覆盖率引导提示
            coverage_hint = ""
            if missing['boundaries']:
                coverage_hint += "\n请特别注意生成包含以下边界值的数据：\n"
                for b in missing['boundaries'][:3]:  # 最多提示3个
                    coverage_hint += f"- {b['field']}={b['value']} ({b['boundary_type']})\n"

            if missing['enums']:
                coverage_hint += "\n请生成包含以下枚举值的数据：\n"
                for e in missing['enums'][:2]:  # 最多提示2个字段
                    coverage_hint += f"- {e['field']}: {', '.join(e['values'][:3])}\n"

            prompt = base_prompt + coverage_hint

            # 调用 LLM
            response = call_llm(prompt)
            is_valid, result = validate_json(response)

            if not is_valid:
                continue

            # 如果还有未覆盖的边界，尝试注入
            if missing['boundaries']:
                result = inject_boundary_values(result, schema, missing['boundaries'])

            # 如果还有未覆盖的枚举，尝试注入
            if missing['enums']:
                result = inject_enum_values(result, schema, missing['enums'])

            # 添加到结果集
            data_str = json.dumps(result, sort_keys=True)
            if data_str not in [json.dumps(d, sort_keys=True) for d in generated_data]:
                generated_data.append(result)
                coverage_tracker.update(result)

                # 打印进度
                if len(generated_data) % 5 == 0:
                    coverage = coverage_tracker.get_coverage()
                    print(f"进度: {len(generated_data)}/{target_count}, "
                          f"字段={coverage['field_coverage']:.0%}, "
                          f"边界={coverage['boundary_coverage']:.0%}, "
                          f"枚举={coverage['enum_coverage']:.0%}")

        # 最后强制补充未覆盖的场景
        missing = coverage_tracker.get_missing()

        # 强制注入边界值
        for boundary in missing.get('boundaries', []):
            if len(generated_data) >= target_count * 1.5:  # 允许稍微超出生成数量
                break

            if generated_data:
                modified = generated_data[0].copy()
            else:
                prompt = generate_json_prompt(schema)
                response = call_llm(prompt)
                is_valid, modified = validate_json(response)
                if not is_valid:
                    continue

            field = boundary['field']
            if field in modified:
                modified[field] = boundary['value']
                generated_data.append(modified)
                coverage_tracker.update(modified)

        # 强制注入枚举值
        for enum_info in missing.get('enums', []):
            if len(generated_data) >= target_count * 1.5:
                break

            for value in enum_info.get('values', []):
                if len(generated_data) >= target_count * 1.5:
                    break

                if generated_data:
                    modified = generated_data[0].copy()
                else:
                    prompt = generate_json_prompt(schema)
                    response = call_llm(prompt)
                    is_valid, modified = validate_json(response)
                    if not is_valid:
                        continue

                field = enum_info['field']
                if field in modified:
                    modified[field] = value
                    generated_data.append(modified)
                    coverage_tracker.update(modified)

        print(f"智能生成完成，生成数量: {len(generated_data)}")
        return generated_data, coverage_tracker

    except Exception as e:
        print(f"智能生成函数发生错误: {e}")
        if coverage_tracker is None:
            coverage_tracker = CoverageTracker(schema)
        return [], coverage_tracker
