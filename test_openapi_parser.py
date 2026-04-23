import os
import json
import urllib.request
from smartdatagen.openapi_parser import extract_schemas_from_openapi, extract_schemas_with_resolved_refs

def download_petstore_example():
    """
    下载 Petstore 示例 OpenAPI 文件
    """
    url = "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.json"
    file_path = "petstore.json"
    
    if not os.path.exists(file_path):
        print("正在下载 Petstore 示例 OpenAPI 文件...")
        try:
            urllib.request.urlretrieve(url, file_path)
            print("✓ 下载成功")
        except Exception as e:
            print(f"✗ 下载失败: {e}")
            return None
    else:
        print("✓ Petstore 示例文件已存在")
    
    return file_path

def test_openapi_parser():
    """
    测试 OpenAPI 解析功能
    """
    # 下载示例文件
    openapi_path = download_petstore_example()
    if not openapi_path:
        return
    
    print("\n=== 测试提取 schema ===")
    # 提取 schema
    schemas = extract_schemas_from_openapi(openapi_path)
    
    print(f"\n提取到 {len(schemas)} 个 schema:")
    for i, (key, schema) in enumerate(schemas.items()):
        print(f"\n{i+1}. {key}")
        print(f"   类型: {schema.get('type', 'N/A')}")
        if 'properties' in schema:
            print(f"   属性数量: {len(schema['properties'])}")
    
    print("\n=== 测试解析 $ref 引用 ===")
    # 提取并解析引用
    resolved_schemas = extract_schemas_with_resolved_refs(openapi_path)
    
    print(f"\n解析后的数据:")
    for key, schema in list(resolved_schemas.items())[:3]:  # 只显示前3个
        print(f"\n{key}")
        print(json.dumps(schema, ensure_ascii=False, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    test_openapi_parser()
