import requests
import json
import os

BASE_URL = "http://localhost:5000"

def test_home_page():
    print("\n=== 测试1: 访问主页 ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"✓ 主页访问成功")
        return True
    except Exception as e:
        print(f"✗ 主页访问失败: {e}")
        return False

def test_generator_page():
    print("\n=== 测试2: 访问数据生成页面 ===")
    try:
        response = requests.get(f"{BASE_URL}/generator")
        print(f"状态码: {response.status_code}")
        print(f"✓ 数据生成页面访问成功")
        return True
    except Exception as e:
        print(f"✗ 数据生成页面访问失败: {e}")
        return False

def test_inline_schema_generation():
    print("\n=== 测试3: 直接输入Schema生成数据 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 120},
            "email": {"type": "string"}
        },
        "required": ["name", "email"]
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 2,
        "format": "json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 直接输入Schema生成数据成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_file_schema_generation():
    print("\n=== 测试4: 上传Schema文件生成数据 ===")
    schema_file = "smartdatagen/examples/user.json"
    
    if not os.path.exists(schema_file):
        print(f"✗ Schema文件不存在: {schema_file}")
        return False
    
    try:
        with open(schema_file, 'rb') as f:
            files = {'schema-file': f}
            data = {
                "source": "file",
                "count": 2,
                "format": "json"
            }
            response = requests.post(f"{BASE_URL}/generator", data=data, files=files)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 上传Schema文件生成数据成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_openapi_generation():
    print("\n=== 测试5: 上传OpenAPI文档生成数据 ===")
    openapi_file = "petstore.json"
    
    if not os.path.exists(openapi_file):
        print(f"✗ OpenAPI文件不存在: {openapi_file}")
        return False
    
    try:
        with open(openapi_file, 'rb') as f:
            files = {'openapi-file': f}
            data = {
                "source": "openapi",
                "count": 1,
                "format": "json"
            }
            response = requests.post(f"{BASE_URL}/generator", data=data, files=files)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 上传OpenAPI文档生成数据成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_smart_generation():
    print("\n=== 测试6: 智能覆盖模式生成数据 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1, "maximum": 100},
            "status": {"type": "string", "enum": ["active", "inactive"]},
            "name": {"type": "string"}
        },
        "required": ["id", "status"]
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 2,
        "smart": "on",
        "format": "json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 智能覆盖模式生成数据成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_mutation_generation():
    print("\n=== 测试7: 变异数据生成 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 120}
        },
        "required": ["name"]
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 1,
        "mutate": "on",
        "format": "json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 变异数据生成成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_coverage_report():
    print("\n=== 测试8: 覆盖率报告生成 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1, "maximum": 100},
            "status": {"type": "string", "enum": ["active", "inactive"]},
            "name": {"type": "string"}
        },
        "required": ["id", "status"]
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 3,
        "report": "on",
        "format": "json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 覆盖率报告生成成功")
            return True
        else:
            print(f"✗ 生成失败")
            return False
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False

def test_csv_output():
    print("\n=== 测试9: CSV格式输出 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"}
        }
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 2,
        "format": "csv"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ CSV格式输出成功")
            return True
        else:
            print(f"✗ 输出失败")
            return False
    except Exception as e:
        print(f"✗ 输出失败: {e}")
        return False

def test_sql_output():
    print("\n=== 测试10: SQL格式输出 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"}
        }
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 2,
        "format": "sql",
        "table": "users"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ SQL格式输出成功")
            return True
        else:
            print(f"✗ 输出失败")
            return False
    except Exception as e:
        print(f"✗ 输出失败: {e}")
        return False

def test_api_test_page():
    print("\n=== 测试11: 访问接口测试页面 ===")
    try:
        response = requests.get(f"{BASE_URL}/api-test")
        print(f"状态码: {response.status_code}")
        print(f"✓ 接口测试页面访问成功")
        return True
    except Exception as e:
        print(f"✗ 接口测试页面访问失败: {e}")
        return False

def test_download_functionality():
    print("\n=== 测试12: 文件下载功能 ===")
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        }
    }
    
    data = {
        "source": "inline",
        "schema": json.dumps(schema, ensure_ascii=False),
        "count": 1,
        "format": "json",
        "download": "on"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generator", data=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200 and "download" in response.text:
            print(f"✓ 文件下载功能正常")
            return True
        else:
            print(f"✗ 下载功能异常")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("SmartDataGen 功能测试")
    print("=" * 60)
    
    tests = [
        test_home_page,
        test_generator_page,
        test_inline_schema_generation,
        test_file_schema_generation,
        test_openapi_generation,
        test_smart_generation,
        test_mutation_generation,
        test_coverage_report,
        test_csv_output,
        test_sql_output,
        test_api_test_page,
        test_download_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
