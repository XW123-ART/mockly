from flask import Flask, render_template_string, render_template, request, jsonify, send_file, session, redirect, url_for, flash
import json
import os
import sys
import tempfile
import uuid
from functools import wraps

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from smartdatagen.schema import parse_schema, extract_field_info
from smartdatagen.generator import generate_mutated_data, generate_with_coverage
from smartdatagen.prompt import generate_json_prompt
from smartdatagen.llm import call_llm
from smartdatagen.utils import validate_json, to_csv, to_sql
from smartdatagen.coverage import calculate_coverage, generate_coverage_report
from smartdatagen.openapi_parser import extract_schemas_with_resolved_refs

# 获取项目根目录（确保是绝对路径）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(PROJECT_ROOT, 'templates')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')

print(f"[DEBUG] 项目根目录: {PROJECT_ROOT}")
print(f"[DEBUG] 模板目录: {TEMPLATE_FOLDER}")
print(f"[DEBUG] 模板目录是否存在: {os.path.exists(TEMPLATE_FOLDER)}")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
app.secret_key = 'mockly-secret-key-2024'

# 上传文件保存目录
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 用户数据（简单存储，实际项目应使用数据库）
USERS = {
    'admin': '123456',
    'test': 'test123'
}


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """首页 - MiMo 风格展示页面"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('generator'))
        else:
            return render_template('login.html', error='用户名或密码错误')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """退出登录"""
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/generator', methods=['GET', 'POST'])
@login_required
def generator():
    if request.method == 'POST':
        try:
            # 获取表单数据
            source = request.form.get('source', 'inline')
            count = int(request.form.get('count', 1))
            smart = 'smart' in request.form
            mutate = 'mutate' in request.form
            report = 'report' in request.form
            format = request.form.get('format', 'json')
            table = request.form.get('table', 'test_table')
            download = 'download' in request.form

            results = []
            schema_name = 'custom_schema'

            # 处理不同的数据来源
            if source == 'inline':
                # 直接输入 Schema
                schema_str = request.form.get('schema', '{}')
                schema = json.loads(schema_str)
                field_info = extract_field_info(schema)

                # 生成数据
                if smart:
                    # 智能生成
                    smart_data, coverage_tracker = generate_with_coverage(schema, count)
                    results.extend(smart_data)
                else:
                    # 传统生成 - 按顺序生成，确保枚举覆盖
                    # 提取枚举字段信息
                    enum_fields = []
                    for field in field_info:
                        constraints = field.get('constraints', {})
                        if 'enum' in constraints:
                            enum_fields.append({
                                'name': field['name'],
                                'values': constraints['enum']
                            })

                    for i in range(count):
                        # 计算枚举提示，确保按顺序覆盖
                        enum_hints = []
                        for enum_field in enum_fields:
                            field_name = enum_field['name']
                            values = enum_field['values']
                            if values:
                                # 按顺序选择枚举值
                                enum_index = i % len(values)
                                enum_value = values[enum_index]
                                enum_hints.append(f"{field_name} 字段必须是: '{enum_value}' (枚举值 {enum_index + 1}/{len(values)})")

                        # 传入序号（从1开始）和枚举提示
                        prompt = generate_json_prompt(schema, sequence=i+1, enum_hints=enum_hints)
                        response = call_llm(prompt)
                        is_valid, result = validate_json(response)
                        if is_valid:
                            results.append(result)
                        else:
                            return render_template('generator.html',
                                                       error=f"生成失败: {result}",
                                                       source=source,
                                                       schema=schema_str,
                                                       count=count,
                                                       smart=smart,
                                                       mutate=mutate,
                                                       report=report,
                                                       format=format,
                                                       table=table,
                                                       download=download)

                # 生成变异数据
                if mutate and field_info:
                    mutated_results = []
                    for data in results:
                        mutated_data = generate_mutated_data(data, field_info, max_mutations=10)
                        mutated_results.extend(mutated_data)
                    results.extend(mutated_results)

            elif source == 'file':
                # 上传 Schema 文件
                if 'schema-file' not in request.files:
                    return render_template('generator.html',
                                               error="请选择 Schema 文件",
                                               source_value=request.form.get('source', 'file'),
                                               count=request.form.get('count', 1),
                                               smart='smart' in request.form,
                                               mutate='mutate' in request.form,
                                               report='report' in request.form,
                                               format=request.form.get('format', 'json'),
                                               table=request.form.get('table', 'test_table'),
                                               download='download' in request.form)

                file = request.files['schema-file']
                if file.filename == '':
                    return render_template('generator.html',
                                               error="请选择 Schema 文件",
                                               source_value=request.form.get('source', 'file'),
                                               count=request.form.get('count', 1),
                                               smart='smart' in request.form,
                                               mutate='mutate' in request.form,
                                               report='report' in request.form,
                                               format=request.form.get('format', 'json'),
                                               table=request.form.get('table', 'test_table'),
                                               download='download' in request.form)

                # 保存文件
                filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filename)

                # 解析 Schema
                schema = parse_schema(filename)
                field_info = extract_field_info(schema)
                schema_name = os.path.splitext(file.filename)[0]

                # 生成数据
                if smart:
                    smart_data, coverage_tracker = generate_with_coverage(schema, count)
                    results.extend(smart_data)
                else:
                    # 提取枚举字段信息
                    enum_fields = []
                    for field in field_info:
                        constraints = field.get('constraints', {})
                        if 'enum' in constraints:
                            enum_fields.append({
                                'name': field['name'],
                                'values': constraints['enum']
                            })

                    for i in range(count):
                        # 计算枚举提示
                        enum_hints = []
                        for enum_field in enum_fields:
                            field_name = enum_field['name']
                            values = enum_field['values']
                            if values:
                                enum_index = i % len(values)
                                enum_value = values[enum_index]
                                enum_hints.append(f"{field_name} 字段必须是: '{enum_value}' (枚举值 {enum_index + 1}/{len(values)})")

                        prompt = generate_json_prompt(schema, sequence=i+1, enum_hints=enum_hints)
                        response = call_llm(prompt)
                        is_valid, result = validate_json(response)
                        if is_valid:
                            results.append(result)
                        else:
                            return render_template('generator.html',
                                                       error=f"生成失败: {result}",
                                                       source=source,
                                                       count=count,
                                                       smart=smart,
                                                       mutate=mutate,
                                                       report=report,
                                                       format=format,
                                                       table=table,
                                                       download=download)

                # 生成变异数据
                if mutate and field_info:
                    mutated_results = []
                    for data in results:
                        mutated_data = generate_mutated_data(data, field_info, max_mutations=10)
                        mutated_results.extend(mutated_data)
                    results.extend(mutated_results)

            elif source == 'openapi':
                # 上传 OpenAPI 文档
                if 'openapi-file' not in request.files:
                    return render_template('generator.html',
                                               error="请选择 OpenAPI 文档",
                                               source_value=request.form.get('source', 'openapi'),
                                               count=request.form.get('count', 1),
                                               smart='smart' in request.form,
                                               mutate='mutate' in request.form,
                                               report='report' in request.form,
                                               format=request.form.get('format', 'json'),
                                               table=request.form.get('table', 'test_table'),
                                               download='download' in request.form)

                file = request.files['openapi-file']
                if file.filename == '':
                    return render_template('generator.html',
                                               error="请选择 OpenAPI 文档",
                                               source_value=request.form.get('source', 'openapi'),
                                               count=request.form.get('count', 1),
                                               smart='smart' in request.form,
                                               mutate='mutate' in request.form,
                                               report='report' in request.form,
                                               format=request.form.get('format', 'json'),
                                               table=request.form.get('table', 'test_table'),
                                               download='download' in request.form)

                # 保存文件
                filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filename)

                # 提取 schemas
                schemas = extract_schemas_with_resolved_refs(filename)

                # 为每个 schema 生成数据
                for schema_name, schema_data in schemas.items():
                    field_info = extract_field_info(schema_data)

                    if smart:
                        smart_data, coverage_tracker = generate_with_coverage(schema_data, count)
                        results.extend(smart_data)
                    else:
                        # 提取枚举字段信息
                        enum_fields = []
                        for field in field_info:
                            constraints = field.get('constraints', {})
                            if 'enum' in constraints:
                                enum_fields.append({
                                    'name': field['name'],
                                    'values': constraints['enum']
                                })

                        for i in range(count):
                            # 计算枚举提示
                            enum_hints = []
                            for enum_field in enum_fields:
                                field_name = enum_field['name']
                                values = enum_field['values']
                                if values:
                                    enum_index = i % len(values)
                                    enum_value = values[enum_index]
                                    enum_hints.append(f"{field_name} 字段必须是: '{enum_value}' (枚举值 {enum_index + 1}/{len(values)})")

                            prompt = generate_json_prompt(schema_data, sequence=i+1, enum_hints=enum_hints)
                            response = call_llm(prompt)
                            is_valid, result = validate_json(response)
                            if is_valid:
                                results.append(result)

                # 生成变异数据
                if mutate:
                    for schema_name, schema_data in schemas.items():
                        field_info = extract_field_info(schema_data)
                        if field_info:
                            mutated_results = []
                            for data in results:
                                mutated_data = generate_mutated_data(data, field_info, max_mutations=10)
                                mutated_results.extend(mutated_data)
                            results.extend(mutated_results)

            # 生成覆盖率报告
            coverage_report = None
            if report and results and (source == 'inline' or source == 'file'):
                if source == 'inline':
                    schema = json.loads(request.form['schema'])
                else:
                    schema = parse_schema(filename)
                coverage = calculate_coverage(results, schema)
                coverage_report = generate_coverage_report(coverage, schema_name)

            # 格式化结果
            if format == 'json':
                formatted_results = json.dumps(results, ensure_ascii=False, indent=2)
                file_extension = 'json'
                mimetype = 'application/json'
            elif format == 'csv':
                formatted_results = to_csv(results)
                file_extension = 'csv'
                mimetype = 'text/csv'
            elif format == 'sql':
                formatted_results = to_sql(results, table)
                file_extension = 'sql'
                mimetype = 'text/plain'

            # 处理下载
            download_link = None
            if download:
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'.{file_extension}', delete=False)
                temp_file.write(formatted_results)
                temp_file.close()

                # 生成下载链接
                download_link = f'/download/{os.path.basename(temp_file.name)}'

            return render_template('generator.html',
                                       results=formatted_results,
                                       coverage_report=coverage_report,
                                       download_link=download_link,
                                       source_value=source,
                                       schema=request.form.get('schema', ''),
                                       count=count,
                                       smart=smart,
                                       mutate=mutate,
                                       report=report,
                                       format=format,
                                       table=table,
                                       download=download)

        except json.JSONDecodeError as e:
            return render_template('generator.html',
                                       error=f"JSON 格式错误: {str(e)}",
                                       source_value=request.form.get('source', 'inline'),
                                       schema=request.form.get('schema', ''),
                                       count=request.form.get('count', 1),
                                       smart='smart' in request.form,
                                       mutate='mutate' in request.form,
                                       report='report' in request.form,
                                       format=request.form.get('format', 'json'),
                                       table=request.form.get('table', 'test_table'),
                                       download='download' in request.form)
        except Exception as e:
            return render_template('generator.html',
                                       error=f"发生错误: {str(e)}",
                                       source_value=request.form.get('source', 'inline'),
                                       schema=request.form.get('schema', ''),
                                       count=request.form.get('count', 1),
                                       smart='smart' in request.form,
                                       mutate='mutate' in request.form,
                                       report='report' in request.form,
                                       format=request.form.get('format', 'json'),
                                       table=request.form.get('table', 'test_table'),
                                       download='download' in request.form)

    # GET 请求
    return render_template('generator.html')

@app.route('/download/<filename>')
def download_file(filename):
    """下载生成的文件"""
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, mimetype='text/plain; charset=utf-8')
    else:
        return "文件不存在", 404

if __name__ == '__main__':
    app.run(debug=True)
