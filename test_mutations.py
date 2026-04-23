import json
from smartdatagen.schema import parse_schema, extract_field_info
from smartdatagen.prompt import generate_json_prompt
from smartdatagen.llm import call_llm
from smartdatagen.utils import validate_json
from smartdatagen.generator import apply_mutations, generate_mutated_data

def test_mutations():
    """
    测试变异算子功能
    """
    # 加载测试schema
    schema_path = 'smartdatagen/examples/user.json'
    schema = parse_schema(schema_path)
    field_info = extract_field_info(schema)
    
    # 生成原始数据
    prompt = generate_json_prompt(schema)
    response = call_llm(prompt)
    is_valid, original_data = validate_json(response)
    
    if not is_valid:
        print(f"生成原始数据失败: {original_data}")
        return
    
    print("原始数据:")
    print(json.dumps(original_data, ensure_ascii=False, indent=2))
    print("=" * 60)
    
    # 应用变异算子
    print("\n应用变异算子...")
    mutated_data = generate_mutated_data(original_data, field_info, max_mutations=15)
    
    print(f"\n生成了 {len(mutated_data)} 条变异数据:")
    print("=" * 60)
    
    # 打印变异结果
    for i, data in enumerate(mutated_data):
        print(f"\n变异数据 #{i+1}:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("-" * 40)

if __name__ == "__main__":
    test_mutations()
