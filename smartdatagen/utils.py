import json
import csv
import io

def validate_json(response):

    # 检查 response 类型
    if not isinstance(response, str):
        raise TypeError("响应必须是字符串类型")

    # 尝试去除可能存在的代码块标记
    if response.strip().startswith('```json'):
        response = response.strip().replace('```json', '').replace('```', '').strip()
    elif response.strip().startswith('```'):
        response = response.strip().replace('```', '').strip()

    try:
        parsed_json = json.loads(response)
        return True, parsed_json
    except json.JSONDecodeError as e:
        return False, str(e)

def to_csv(data_list, fieldnames=None):
    """
    将数据列表转换为 CSV 字符串

    Args:
        data_list (list): 数据字典列表
        fieldnames (list): 字段名列表，如果为 None 则自动从数据中提取

    Returns:
        str: CSV 格式的字符串
    """
    if not data_list:
        return ""

    # 自动提取字段名
    if not fieldnames:
        fieldnames = set()
        for item in data_list:
            if isinstance(item, dict):
                fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)

    # 创建 CSV 写入器
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    # 写入表头
    writer.writeheader()

    # 写入数据
    for item in data_list:
        # 处理嵌套数据，转换为 JSON 字符串
        row = {}
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value, ensure_ascii=False)
            else:
                row[key] = value
        writer.writerow(row)

    return output.getvalue()

def to_sql(data_list, table_name='test_table'):
    """
    将数据列表转换为 SQL INSERT 语句

    Args:
        data_list (list): 数据字典列表
        table_name (str): 表名

    Returns:
        str: SQL INSERT 语句字符串
    """
    if not data_list:
        return ""

    # 提取字段名
    fieldnames = set()
    for item in data_list:
        if isinstance(item, dict):
            fieldnames.update(item.keys())
    fieldnames = sorted(fieldnames)

    if not fieldnames:
        return ""

    # 构建 SQL 语句
    sql_statements = []
    for item in data_list:
        # 构建值列表
        values = []
        for field in fieldnames:
            value = item.get(field)
            if value is None:
                values.append('NULL')
            elif isinstance(value, (dict, list)):
                # 嵌套数据转换为 JSON 字符串
                json_str = json.dumps(value, ensure_ascii=False)
                values.append("'" + json_str.replace("'", "''") + "'")
            elif isinstance(value, str):
                # 字符串转义
                values.append("'" + value.replace("'", "''") + "'")
            else:
                # 数字、布尔值等直接使用
                values.append(str(value))

        # 构建 INSERT 语句
        fields_str = ', '.join(fieldnames)
        values_str = ', '.join(values)
        sql = f"INSERT INTO {table_name} ({fields_str}) VALUES ({values_str});"
        sql_statements.append(sql)

    return '\n'.join(sql_statements)
