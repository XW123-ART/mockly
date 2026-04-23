class CoverageTracker:
    """覆盖率跟踪器，维护当前已生成数据的覆盖情况"""
    
    def __init__(self, schema):
        """初始化覆盖率跟踪器
        
        Args:
            schema: JSON schema 定义
        """
        self.schema = schema
        self.properties = schema.get('properties', {})
        self.field_names = list(self.properties.keys())
        
        # 初始化字段覆盖
        self.field_coverage = {}
        for field in self.field_names:
            self.field_coverage[field] = False
        
        # 初始化边界覆盖
        self.boundary_coverage = {}
        for field, props in self.properties.items():
            boundaries = []
            if 'minimum' in props:
                boundaries.append(('min', props['minimum']))
            if 'maximum' in props:
                boundaries.append(('max', props['maximum']))
            if boundaries:
                self.boundary_coverage[field] = {}
                for boundary_type, value in boundaries:
                    # 存储边界值和覆盖状态
                    self.boundary_coverage[field][boundary_type] = {
                        'value': value,
                        'covered': False
                    }
        
        # 初始化枚举覆盖
        self.enum_coverage = {}
        for field, props in self.properties.items():
            if 'enum' in props:
                enum_values = props['enum']
                self.enum_coverage[field] = {
                    'covered': set(),
                    'total': enum_values
                }
    
    def update(self, data):
        """更新覆盖率跟踪器
        
        Args:
            data: 生成的数据
        """
        # 更新字段覆盖
        for field in self.field_names:
            if field in data and data[field] is not None:
                self.field_coverage[field] = True
        
        # 更新边界覆盖
        for field, boundaries in self.boundary_coverage.items():
            if field in data and isinstance(data[field], (int, float)):
                for boundary_type, boundary_info in boundaries.items():
                    if data[field] == boundary_info['value']:
                        self.boundary_coverage[field][boundary_type]['covered'] = True
        
        # 更新枚举覆盖
        for field, enum_info in self.enum_coverage.items():
            if field in data and data[field] in enum_info['total']:
                enum_info['covered'].add(data[field])
    
    def get_missing(self):
        """获取未覆盖的场景
        
        Returns:
            包含未覆盖场景的字典
        """
        missing = {
            'fields': [],
            'boundaries': [],
            'enums': []
        }
        
        # 未覆盖的字段
        for field, covered in self.field_coverage.items():
            if not covered:
                missing['fields'].append(field)
        
        # 未覆盖的边界
        for field, boundaries in self.boundary_coverage.items():
            for boundary_type, boundary_info in boundaries.items():
                if not boundary_info['covered']:
                    missing['boundaries'].append({
                        'field': field,
                        'boundary_type': boundary_type,
                        'value': boundary_info['value']
                    })
        
        # 未覆盖的枚举值
        for field, enum_info in self.enum_coverage.items():
            covered_values = enum_info['covered']
            total_values = enum_info['total']
            missing_values = [v for v in total_values if v not in covered_values]
            if missing_values:
                missing['enums'].append({
                    'field': field,
                    'values': missing_values
                })
        
        return missing
    
    def get_coverage(self):
        """获取当前覆盖率
        
        Returns:
            包含各项覆盖率指标的字典
        """
        coverage = {
            'field_coverage': 0,
            'boundary_coverage': 0,
            'enum_coverage': 0,
            'summary': {}
        }
        
        if not self.field_names:
            return coverage
        
        # 字段覆盖
        covered_fields = sum(1 for covered in self.field_coverage.values() if covered)
        coverage['field_coverage'] = covered_fields / len(self.field_names) if self.field_names else 0
        coverage['summary']['field_coverage'] = {
            'covered': covered_fields,
            'total': len(self.field_names),
            'details': self.field_coverage
        }
        
        # 边界覆盖
        total_boundaries = sum(len(boundaries) for boundaries in self.boundary_coverage.values())
        covered_boundaries = sum(
            sum(1 for boundary_info in boundaries.values() if boundary_info['covered'])
            for boundaries in self.boundary_coverage.values()
        )
        coverage['boundary_coverage'] = covered_boundaries / total_boundaries if total_boundaries else 0
        coverage['summary']['boundary_coverage'] = {
            'covered': covered_boundaries,
            'total': total_boundaries,
            'details': self.boundary_coverage
        }
        
        # 枚举覆盖
        total_enum_values = sum(len(info['total']) for info in self.enum_coverage.values())
        covered_enum_values = sum(len(info['covered']) for info in self.enum_coverage.values())
        coverage['enum_coverage'] = covered_enum_values / total_enum_values if total_enum_values else 0
        coverage['summary']['enum_coverage'] = {
            'covered': covered_enum_values,
            'total': total_enum_values,
            'details': self.enum_coverage
        }
        
        return coverage

def calculate_coverage(data_list, schema):
    """计算生成数据的覆盖率
    
    Args:
        data_list: 生成的数据列表
        schema: JSON schema 定义
    
    Returns:
        包含各项覆盖率指标的字典
    """
    tracker = CoverageTracker(schema)
    for data in data_list:
        tracker.update(data)
    return tracker.get_coverage()

def generate_coverage_report(coverage, schema_name="unknown"):
    """生成覆盖率报告
    
    Args:
        coverage: 覆盖率统计结果
        schema_name: schema 名称
    
    Returns:
        格式化的覆盖率报告字符串
    """
    report = f"\n=== 覆盖率报告: {schema_name} ===\n"
    report += f"字段覆盖: {coverage['field_coverage']:.2%} ({coverage['summary']['field_coverage']['covered']}/{coverage['summary']['field_coverage']['total']})\n"
    report += f"边界覆盖: {coverage['boundary_coverage']:.2%} ({coverage['summary']['boundary_coverage']['covered']}/{coverage['summary']['boundary_coverage']['total']})\n"
    report += f"枚举覆盖: {coverage['enum_coverage']:.2%} ({coverage['summary']['enum_coverage']['covered']}/{coverage['summary']['enum_coverage']['total']})\n"
    
    # 详细信息
    report += "\n详细信息:\n"
    
    # 字段覆盖详情
    report += "\n字段覆盖:\n"
    for field, covered in coverage['summary']['field_coverage']['details'].items():
        status = "[OK]" if covered else "[MISS]"
        report += f"  {field}: {status}\n"
    
    # 边界覆盖详情
    if coverage['summary']['boundary_coverage']['total'] > 0:
        report += "\n边界覆盖:\n"
        for field, boundaries in coverage['summary']['boundary_coverage']['details'].items():
            for boundary_type, boundary_info in boundaries.items():
                status = "[OK]" if boundary_info['covered'] else "[MISS]"
                report += f"  {field} ({boundary_type}): {status} (值: {boundary_info['value']})\n"
    
    # 枚举覆盖详情
    if coverage['summary']['enum_coverage']['total'] > 0:
        report += "\n枚举覆盖:\n"
        for field, enum_info in coverage['summary']['enum_coverage']['details'].items():
            covered_values = list(enum_info['covered'])
            total_values = enum_info['total']
            report += f"  {field}: {len(covered_values)}/{len(total_values)} 覆盖值: {covered_values}\n"
    
    report += "============================\n"
    return report