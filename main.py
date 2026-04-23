import sys
import os
import click
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartdatagen.schema import parse_schema
from smartdatagen.prompt import generate_json_prompt
from smartdatagen.llm import call_llm
from smartdatagen.utils import validate_json, to_csv, to_sql
from smartdatagen.generator import generate_mutated_data, generate_with_coverage, generate_coverage_optimized_data
from smartdatagen.openapi_parser import extract_schemas_with_resolved_refs
from smartdatagen.coverage import calculate_coverage, generate_coverage_report, CoverageTracker

@click.command()
@click.option('--schema', help='Schema文件路径')
@click.option('--openapi', type=click.Path(exists=True), help='OpenAPI文档路径，将批量生成所有接口的数据')
@click.option('--count', default=1, type=int, help='生成条数，默认为1')
@click.option('--output', help='输出文件路径')
@click.option('--format', default='json', type=click.Choice(['json', 'csv', 'sql']), help='输出格式，默认为json')
@click.option('--table', default='test_table', help='SQL表名，默认为test_table')
@click.option('--mutate/--no-mutate', default=False, help='是否生成变异数据')
@click.option('--report', type=click.Path(), help='生成覆盖率报告，可指定报告文件路径')
@click.option('--smart/--no-smart', default=False, help='启用智能覆盖模式，根据覆盖率反馈生成数据')
@click.option('--coverage-opt', 'coverage_opt', is_flag=True, help='启用覆盖率优化模式，强制生成边界值和枚举值')
def generate_data(schema, openapi, count, output, format, table, mutate, report, smart, coverage_opt):
    """
    根据Schema生成JSON数据
    
    示例:
        python main.py --schema smartdatagen/examples/user.json
        python main.py --schema smartdatagen/examples/user.json --count 3 --output out.json
    """
    try:
        # 验证参数
        if count < 1:
            raise ValueError("生成条数必须大于等于1")
        
        if not schema and not openapi:
            raise ValueError("必须指定 --schema 或 --openapi 参数")
        
        # 处理输出目录
        if output:
            # 检查输出目录是否存在
            if os.path.isdir(output):
                # 输出为目录
                if not os.path.exists(output):
                    os.makedirs(output, exist_ok=True)
            else:
                # 输出为文件
                output_dir = os.path.dirname(output)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
        
        # 处理 OpenAPI 文档
        if openapi:
            click.echo(f"正在处理 OpenAPI 文档: {openapi}")
            schemas = extract_schemas_with_resolved_refs(openapi)
            click.echo(f"✓ 成功提取到 {len(schemas)} 个 schema")
            
            # 为每个 schema 生成数据
            all_results = {}
            total_success = 0
            total_mutations = 0
            
            for schema_name, schema_data in schemas.items():
                click.echo(f"\n=== 处理 schema: {schema_name} ===")
                
                # 提取字段信息（用于变异）
                field_info = []
                if mutate:
                    from smartdatagen.schema import extract_field_info
                    field_info = extract_field_info(schema_data)
                    click.echo(f"✓ 提取到 {len(field_info)} 个字段信息")
                
                # 生成数据
                results = []
                success_count = 0
                mutation_count = 0
                
                if coverage_opt:
                    click.echo("\n启用覆盖率优化模式...")
                    # 使用覆盖率优化生成
                    opt_data, coverage_tracker = generate_coverage_optimized_data(schema_data, count)
                    results.extend(opt_data)
                    success_count = len(opt_data)

                    # 应用变异
                    if mutate and field_info:
                        click.echo("\n正在生成变异数据...")
                        total_mutations = 0
                        for data in opt_data:
                            mutated_data = generate_mutated_data(data, field_info, max_mutations=20)
                            if mutated_data:
                                # 去重
                                for mutation in mutated_data:
                                    # 检查是否已存在
                                    exists = False
                                    for existing in results:
                                        if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                            exists = True
                                            break
                                    if not exists:
                                        results.append(mutation)
                                        total_mutations += 1
                        mutation_count = total_mutations
                        click.echo(f"✓ 生成了 {total_mutations} 条变异数据")
                elif smart:
                    click.echo("\n启用智能覆盖模式...")
                    # 使用智能生成
                    smart_data, coverage_tracker = generate_with_coverage(schema_data, count)
                    results.extend(smart_data)
                    success_count = len(smart_data)

                    # 应用变异
                    if mutate and field_info:
                        click.echo("\n正在生成变异数据...")
                        total_mutations = 0
                        for data in smart_data:
                            mutated_data = generate_mutated_data(data, field_info, max_mutations=20)
                            if mutated_data:
                                # 去重
                                for mutation in mutated_data:
                                    # 检查是否已存在
                                    exists = False
                                    for existing in results:
                                        if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                            exists = True
                                            break
                                    if not exists:
                                        results.append(mutation)
                                        total_mutations += 1
                        mutation_count = total_mutations
                        click.echo(f"✓ 生成了 {total_mutations} 条变异数据")
                else:
                    # 传统生成方式
                    for i in range(count):
                        click.echo(f"\n生成第 {i+1} 条数据...")
                        
                        try:
                            # 生成Prompt
                            prompt = generate_json_prompt(schema_data)
                            
                            # 调用LLM
                            response = call_llm(prompt)
                            
                            # 验证JSON
                            is_valid, result = validate_json(response)
                            if is_valid:
                                click.echo(f"✓ 生成成功")
                                results.append(result)
                                success_count += 1
                                
                                # 应用变异
                                if mutate and field_info:
                                    click.echo(f"  正在生成变异数据...")
                                    mutated_data = generate_mutated_data(result, field_info, max_mutations=20)
                                    if mutated_data:
                                        # 去重
                                        for mutation in mutated_data:
                                            # 检查是否已存在
                                            exists = False
                                            for existing in results:
                                                if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                                    exists = True
                                                    break
                                            if not exists:
                                                results.append(mutation)
                                                mutation_count += 1
                                        click.echo(f"  ✓ 生成了 {len(mutated_data)} 条变异数据")
                            else:
                                click.echo(f"✗ 生成失败: {result}")
                                
                        except Exception as e:
                            click.echo(f"✗ 生成过程中发生错误: {e}")
                
                all_results[schema_name] = results
                total_success += success_count
                total_mutations += mutation_count
                
                if mutate:
                    click.echo(f"\n✓ 共生成 {success_count} 条原始数据，{mutation_count} 条变异数据，总计 {len(results)} 条数据")
                else:
                    click.echo(f"\n✓ 共生成 {success_count} 条有效数据")
                
                # 生成覆盖率报告
                if report:
                    click.echo(f"\n正在生成覆盖率报告...")
                    coverage = calculate_coverage(results, schema_data)
                    coverage_report = generate_coverage_report(coverage, schema_name)
                    click.echo(coverage_report)
                    
                    # 如果指定了报告文件路径，保存报告
                    if report != 'True' and report:
                        try:
                            report_dir = os.path.dirname(report)
                            if report_dir and not os.path.exists(report_dir):
                                os.makedirs(report_dir, exist_ok=True)
                            
                            # 为每个 schema 生成单独的报告文件
                            if os.path.isdir(report):
                                safe_name = schema_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(':', '')
                                report_file = os.path.join(report, f"{safe_name}_coverage.txt")
                            else:
                                report_file = report
                            
                            with open(report_file, 'a', encoding='utf-8') as f:
                                f.write(coverage_report)
                            click.echo(f"✓ 覆盖率报告已保存到: {report_file}")
                        except Exception as e:
                            click.echo(f"✗ 保存覆盖率报告失败: {e}")
            
            # 输出结果
            if output:
                if os.path.isdir(output):
                    # 输出到目录
                    for schema_name, results in all_results.items():
                        # 生成文件名
                        safe_name = schema_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(':', '')
                        if format == 'json':
                            file_name = f"{safe_name}.json"
                        elif format == 'csv':
                            file_name = f"{safe_name}.csv"
                        elif format == 'sql':
                            file_name = f"{safe_name}.sql"
                        file_path = os.path.join(output, file_name)
                        
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                if format == 'json':
                                    json.dump(results, f, ensure_ascii=False, indent=2)
                                elif format == 'csv':
                                    csv_content = to_csv(results)
                                    f.write(csv_content)
                                elif format == 'sql':
                                    # 使用schema名称作为表名
                                    table_name = safe_name.replace('_', '')
                                    sql_content = to_sql(results, table_name)
                                    f.write(sql_content)
                            click.echo(f"✓ 数据已保存到: {file_path}")
                        except Exception as e:
                            click.echo(f"✗ 保存文件失败: {e}")
                else:
                    # 输出到单个文件
                    try:
                        with open(output, 'w', encoding='utf-8') as f:
                            if format == 'json':
                                json.dump(all_results, f, ensure_ascii=False, indent=2)
                            elif format == 'csv':
                                # 合并所有数据
                                all_data = []
                                for results in all_results.values():
                                    all_data.extend(results)
                                csv_content = to_csv(all_data)
                                f.write(csv_content)
                            elif format == 'sql':
                                # 为每个schema生成SQL
                                sql_statements = []
                                for schema_name, results in all_results.items():
                                    table_name = schema_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(':', '').replace('_', '')
                                    sql_content = to_sql(results, table_name)
                                    sql_statements.append(sql_content)
                                f.write('\n\n'.join(sql_statements))
                        click.echo(f"\n✓ 所有数据已保存到: {output}")
                    except Exception as e:
                        click.echo(f"✗ 保存文件失败: {e}")
            else:
                # 输出到控制台
                for schema_name, results in all_results.items():
                    click.echo(f"\n=== {schema_name} ===")
                    if format == 'json':
                        for i, result in enumerate(results):
                            click.echo(f"\n第 {i+1} 条:")
                            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
                    elif format == 'csv':
                        csv_content = to_csv(results)
                        click.echo(csv_content)
                    elif format == 'sql':
                        table_name = schema_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(':', '').replace('_', '')
                        sql_content = to_sql(results, table_name)
                        click.echo(sql_content)
            
            click.echo(f"\n=== 总计 ===")
            if mutate:
                click.echo(f"✓ 共处理 {len(schemas)} 个 schema，生成 {total_success} 条原始数据，{total_mutations} 条变异数据")
            else:
                click.echo(f"✓ 共处理 {len(schemas)} 个 schema，生成 {total_success} 条有效数据")
        
        # 处理单个 Schema 文件
        elif schema:
            click.echo(f"正在处理 schema: {schema}")
            schema_data = parse_schema(schema)
            click.echo(f"✓ 成功解析 schema")
            
            # 提取字段信息（用于变异）
            field_info = []
            if mutate:
                from smartdatagen.schema import extract_field_info
                field_info = extract_field_info(schema_data)
                click.echo(f"✓ 提取到 {len(field_info)} 个字段信息")
            
            # 生成数据
            results = []
            success_count = 0
            mutation_count = 0

            if coverage_opt:
                click.echo("\n启用覆盖率优化模式...")
                # 使用覆盖率优化生成
                opt_data, coverage_tracker = generate_coverage_optimized_data(schema_data, count)
                results.extend(opt_data)
                success_count = len(opt_data)

                # 应用变异
                if mutate and field_info:
                    click.echo("\n正在生成变异数据...")
                    total_mutations = 0
                    for data in opt_data:
                        mutated_data = generate_mutated_data(data, field_info, max_mutations=20)
                        if mutated_data:
                            # 去重
                            for mutation in mutated_data:
                                # 检查是否已存在
                                exists = False
                                for existing in results:
                                    if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                        exists = True
                                        break
                                if not exists:
                                    results.append(mutation)
                                    total_mutations += 1
                    mutation_count = total_mutations
                    click.echo(f"✓ 生成了 {total_mutations} 条变异数据")
            elif smart:
                click.echo("\n启用智能覆盖模式...")
                # 使用智能生成
                smart_data, coverage_tracker = generate_with_coverage(schema_data, count)
                results.extend(smart_data)
                success_count = len(smart_data)

                # 应用变异
                if mutate and field_info:
                    click.echo("\n正在生成变异数据...")
                    total_mutations = 0
                    for data in smart_data:
                        mutated_data = generate_mutated_data(data, field_info, max_mutations=20)
                        if mutated_data:
                            # 去重
                            for mutation in mutated_data:
                                # 检查是否已存在
                                exists = False
                                for existing in results:
                                    if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                        exists = True
                                        break
                                if not exists:
                                    results.append(mutation)
                                    total_mutations += 1
                    mutation_count = total_mutations
                    click.echo(f"✓ 生成了 {total_mutations} 条变异数据")
            else:
                # 传统生成方式
                for i in range(count):
                    click.echo(f"\n生成第 {i+1} 条数据...")
                    
                    try:
                        # 生成Prompt
                        prompt = generate_json_prompt(schema_data)
                        
                        # 调用LLM
                        response = call_llm(prompt)
                        
                        # 验证JSON
                        is_valid, result = validate_json(response)
                        if is_valid:
                            click.echo(f"✓ 生成成功")
                            results.append(result)
                            success_count += 1
                            
                            # 应用变异
                            if mutate and field_info:
                                click.echo(f"  正在生成变异数据...")
                                mutated_data = generate_mutated_data(result, field_info, max_mutations=20)
                                if mutated_data:
                                    # 去重
                                    for mutation in mutated_data:
                                        # 检查是否已存在
                                        exists = False
                                        for existing in results:
                                            if json.dumps(existing, sort_keys=True) == json.dumps(mutation, sort_keys=True):
                                                exists = True
                                                break
                                        if not exists:
                                            results.append(mutation)
                                            mutation_count += 1
                                    click.echo(f"  ✓ 生成了 {len(mutated_data)} 条变异数据")
                        else:
                            click.echo(f"✗ 生成失败: {result}")
                            
                    except Exception as e:
                        click.echo(f"✗ 生成过程中发生错误: {e}")
            
            # 输出结果
            if results:
                if output:
                    try:
                        with open(output, 'w', encoding='utf-8') as f:
                            if format == 'json':
                                json.dump(results, f, ensure_ascii=False, indent=2)
                            elif format == 'csv':
                                csv_content = to_csv(results)
                                f.write(csv_content)
                            elif format == 'sql':
                                sql_content = to_sql(results, table)
                                f.write(sql_content)
                        click.echo(f"\n✓ 数据已保存到: {output}")
                    except Exception as e:
                        click.echo(f"✗ 保存文件失败: {e}")
                else:
                    click.echo("\n生成的数据:")
                    if format == 'json':
                        for i, result in enumerate(results):
                            click.echo(f"\n第 {i+1} 条:")
                            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
                    elif format == 'csv':
                        csv_content = to_csv(results)
                        click.echo(csv_content)
                    elif format == 'sql':
                        sql_content = to_sql(results, table)
                        click.echo(sql_content)
                
                if mutate:
                    click.echo(f"\n✓ 共生成 {success_count} 条原始数据，{mutation_count} 条变异数据，总计 {len(results)} 条数据")
                else:
                    click.echo(f"\n✓ 共生成 {success_count} 条有效数据")
                
                # 生成覆盖率报告
                if report:
                    click.echo(f"\n正在生成覆盖率报告...")
                    coverage = calculate_coverage(results, schema_data)
                    coverage_report = generate_coverage_report(coverage, os.path.basename(schema))
                    click.echo(coverage_report)
                    
                    # 如果指定了报告文件路径，保存报告
                    if report != 'True' and report:
                        try:
                            report_dir = os.path.dirname(report)
                            if report_dir and not os.path.exists(report_dir):
                                os.makedirs(report_dir, exist_ok=True)
                            
                            with open(report, 'w', encoding='utf-8') as f:
                                f.write(coverage_report)
                            click.echo(f"✓ 覆盖率报告已保存到: {report}")
                        except Exception as e:
                            click.echo(f"✗ 保存覆盖率报告失败: {e}")
            else:
                click.echo("\n✗ 没有生成有效数据")
        
    except Exception as e:
        click.echo(f"✗ 处理失败: {e}")

if __name__ == '__main__':
    generate_data()