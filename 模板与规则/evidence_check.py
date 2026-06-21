#!/usr/bin/env python3
"""
工程项目证据链管理系统 — 自动化检查工具
=========================================
用法:
  python evidence_check.py                     # 检查当前目录下的项目
  python evidence_check.py <项目文件夹路径>     # 检查指定项目
  python evidence_check.py --scan-all          # 扫描所有项目
  python evidence_check.py --init <项目名>      # 新建一个空项目
  python evidence_check.py --export <项目路径>  # 导出证据清单CSV

功能:
  - 扫描项目文件夹，按类别统计文件数
  - 验证文件名是否符合命名规则
  - 标记异常文件（命名不规范、位置放错等）
  - 输出检查报告
  - 检查结算清单缺项
  - 一键导出证据清单
"""

import os
import sys
import re
import csv
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ============================================================
# 配置 — 与命名规则文档保持一致
# ============================================================

# 类别缩写对照表
CATEGORY_CODES = {
    'HT': '合同文件',
    'ZBTZ': '中标通知书',
    'KGBG': '开工报告',
    'VS': '签证单',
    'XCQR': '现场确认单',
    'FYQR': '费用签认单',
    'BG': '变更通知单',
    'BGTZ': '变更图纸',
    'BQQS': '变更洽商',
    'BGFY': '变更费用报审',
    'RZ': '施工日志',
    'CLJZ': '材料进场验收',
    'JYP': '检验批记录',
    'HYJY': '会议纪要',
    'YBGC': '隐蔽工程验收',
    'FFBX': '分部分项验收',
    'JGYS': '竣工验收',
    'ZGTZ': '整改通知',
    'GCL': '工程量确认单',
    'JDK': '进度款申请',
    'JSS': '结算书',
    'DZD': '对账单',
    'JLF': '甲方来函',
    'WFF': '我方发函',
    'JLTZ': '监理通知',
    'QDD': '会议签到表',
    'PHOTO-SG': '施工过程照片',
    'PHOTO-YB': '隐蔽工程照片',
    'PHOTO-YS': '验收照片',
    'PHOTO-QJ': '全景照片',
}

# 类别 → 应存放的文件夹路径（相对项目根目录）
CATEGORY_FOLDER = {
    'HT': '00-项目概览/合同文件',
    'ZBTZ': '00-项目概览/中标通知',
    'KGBG': '00-项目概览/开工报告',
    'VS': '01-过程签证/签证单',
    'XCQR': '01-过程签证/现场确认单',
    'FYQR': '01-过程签证/费用签认单',
    'BG': '02-设计变更/变更通知单',
    'BGTZ': '02-设计变更/变更图纸',
    'BQQS': '02-设计变更/变更洽商',
    'BGFY': '02-设计变更/变更费用报审',
    'RZ': '03-施工过程/施工日志',
    'CLJZ': '03-施工过程/材料进场验收',
    'JYP': '03-施工过程/检验批记录',
    'HYJY': '03-施工过程/会议纪要',
    'YBGC': '04-验收记录/隐蔽工程验收',
    'FFBX': '04-验收记录/分部分项验收',
    'JGYS': '04-验收记录/竣工验收',
    'ZGTZ': '04-验收记录/整改通知',
    'GCL': '05-工程量与计价/工程量确认单',
    'JDK': '05-工程量与计价/进度款申请',
    'JSS': '05-工程量与计价/结算书',
    'DZD': '05-工程量与计价/对账单',
    'JLF': '06-往来函件/甲方来函',
    'WFF': '06-往来函件/我方发函',
    'JLTZ': '06-往来函件/监理通知',
    'QDD': '06-往来函件/会议签到表',
    'PHOTO-SG': '07-影像资料/施工过程照片',
    'PHOTO-YB': '07-影像资料/隐蔽工程照片',
    'PHOTO-YS': '07-影像资料/验收照片',
    'PHOTO-QJ': '07-影像资料/全景照片',
}

# 标准目录结构（检查缺层）
STANDARD_DIRS = [
    '00-项目概览', '00-项目概览/合同文件', '00-项目概览/中标通知', '00-项目概览/开工报告',
    '01-过程签证', '01-过程签证/签证单', '01-过程签证/现场确认单', '01-过程签证/费用签认单',
    '02-设计变更', '02-设计变更/变更通知单', '02-设计变更/变更图纸', '02-设计变更/变更洽商', '02-设计变更/变更费用报审',
    '03-施工过程', '03-施工过程/施工日志', '03-施工过程/材料进场验收', '03-施工过程/检验批记录', '03-施工过程/会议纪要',
    '04-验收记录', '04-验收记录/隐蔽工程验收', '04-验收记录/分部分项验收', '04-验收记录/竣工验收', '04-验收记录/整改通知',
    '05-工程量与计价', '05-工程量与计价/工程量确认单', '05-工程量与计价/进度款申请', '05-工程量与计价/结算书', '05-工程量与计价/对账单',
    '06-往来函件', '06-往来函件/甲方来函', '06-往来函件/我方发函', '06-往来函件/监理通知', '06-往来函件/会议签到表',
    '07-影像资料', '07-影像资料/施工过程照片', '07-影像资料/隐蔽工程照片', '07-影像资料/验收照片', '07-影像资料/全景照片',
]

# 文件名正则：YYYYMMDD-CODE-简述-vX.Y-状态.ext
FILENAME_PATTERN = re.compile(
    r'^(\d{8})'                # 1: 日期 YYYYMMDD
    r'-([A-Z]+(?:-[A-Z]+)?)'   # 2: 类别缩写（含 PHOTO-SG 这种带连字符的）
    r'-(.+)'                    # 3: 简述
    r'-v(\d+\.\d+)'             # 4: 版本号
    r'-(已签认|待确认|已否决|自行归档)'  # 5: 状态
    r'\.\w+$'                   # 扩展名
)

VALID_STATUSES = {'已签认', '待确认', '已否决', '自行归档'}

# 结算清单必检项
CHECKLIST_REQUIRED = {
    'HT': {'min': 1, 'label': '施工合同'},
    'ZBTZ': {'min': 1, 'label': '中标通知书'},
    'KGBG': {'min': 1, 'label': '开工报告'},
    'VS': {'min': 1, 'label': '过程签证单'},
    'BG': {'min': 1, 'label': '设计变更通知（如果有）'},
    'YBGC': {'min': 1, 'label': '隐蔽工程验收记录'},
    'FFBX': {'min': 1, 'label': '分部分项验收'},
    'JGYS': {'min': 1, 'label': '竣工验收记录'},
    'GCL': {'min': 1, 'label': '工程量确认单'},
    'JSS': {'min': 1, 'label': '结算书'},
    'DZD': {'min': 1, 'label': '对账单'},
}


# ============================================================
# 核心功能
# ============================================================

def find_project_root(path):
    """判断一个目录是否为项目文件夹（含标准子目录即为项目）"""
    if not os.path.isdir(path):
        return None
    contents = set(os.listdir(path))
    # 如果里面含 00-... 或 01-... 等标准目录，即认为是项目
    has_standard = any(d.startswith(('00-', '01-', '02-', '03-', '04-', '05-', '06-', '07-')) for d in contents)
    return path if has_standard else None


def scan_all_projects(base_path):
    """扫描根目录下所有项目"""
    projects = []
    if not os.path.isdir(base_path):
        return projects
    for item in sorted(os.listdir(base_path)):
        item_path = os.path.join(base_path, item)
        if find_project_root(item_path):
            projects.append(item_path)
    return projects


def parse_filename(filename):
    """解析文件名，返回各部分信息，不符合返回None"""
    match = FILENAME_PATTERN.match(filename)
    if not match:
        return None
    date_str, code, desc, version, status = match.groups()
    
    # 验证日期合法性
    try:
        datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return None
    
    # 验证类别代码
    if code not in CATEGORY_CODES:
        return None
    
    return {
        'filename': filename,
        'date': date_str,
        'code': code,
        'category': CATEGORY_CODES[code],
        'description': desc,
        'version': version,
        'status': status,
        'expected_folder': CATEGORY_FOLDER.get(code, ''),
    }


def get_relative_path(file_path, project_root):
    """获取文件相对于项目根目录的路径"""
    try:
        return os.path.relpath(file_path, project_root).replace('\\', '/')
    except ValueError:
        return file_path


def scan_project(project_path):
    """扫描一个项目文件夹，返回完整的分析结果"""
    result = {
        'project_name': os.path.basename(project_path),
        'project_path': project_path,
        'total_files': 0,
        'valid_files': 0,
        'invalid_files': 0,
        'by_category': defaultdict(lambda: {'count': 0, 'valid': 0, 'invalid': 0}),
        'by_status': defaultdict(int),
        'issues': [],
        'valid_entries': [],
        'invalid_entries': [],
        'missing_dirs': [],
        'checklist': {},
    }
    
    # 检查缺失的标准目录
    for std_dir in STANDARD_DIRS:
        dir_path = os.path.join(project_path, std_dir)
        if not os.path.isdir(dir_path):
            result['missing_dirs'].append(std_dir)
    
    # 遍历所有文件
    for root, dirs, files in os.walk(project_path):
        # 跳过模板与规则目录
        if '模板与规则' in root:
            continue
        
        rel_dir = get_relative_path(root, project_path)
        
        for f in files:
            # 跳过隐藏文件和临时文件
            if f.startswith('.') or f.startswith('~$'):
                continue
            
            # 跳过项目基本信息.md、README等元文件
            if f in ('项目基本信息.md', 'README.md', 'index.csv', 'index.xlsx'):
                continue
            
            result['total_files'] += 1
            file_path = os.path.join(root, f)
            
            parsed = parse_filename(f)
            if parsed:
                result['valid_files'] += 1
                code = parsed['code']
                result['by_category'][code]['count'] += 1
                result['by_category'][code]['valid'] += 1
                result['by_status'][parsed['status']] += 1
                
                entry = {
                    'filename': f,
                    'path': get_relative_path(file_path, project_path),
                    'date': parsed['date'],
                    'code': code,
                    'category': parsed['category'],
                    'description': parsed['description'],
                    'version': parsed['version'],
                    'status': parsed['status'],
                    'expected_folder': parsed['expected_folder'],
                }
                
                # 检查文件是否放在正确的文件夹
                if parsed['expected_folder']:
                    # 检查相对路径是否包含期望的文件夹
                    if parsed['expected_folder'] not in rel_dir:
                        entry['location_warning'] = f"文件应放在 {parsed['expected_folder']}/ 下，实际在 {rel_dir}/"
                        result['issues'].append(f"[位置错误] {f} → 应放在 {parsed['expected_folder']}/，实际在 {rel_dir}/")
                
                result['valid_entries'].append(entry)
            else:
                result['invalid_files'] += 1
                result['invalid_entries'].append({
                    'filename': f,
                    'path': get_relative_path(file_path, project_path),
                })
                result['issues'].append(f"[命名不规范] {f} (路径: {rel_dir}/)")
    
    # 结算清单检查
    result['checklist'] = check_completeness(result['valid_entries'])
    
    return result


def check_completeness(valid_entries):
    """对照结算清单，检查是否满足最低要求"""
    checklist = {}
    by_code = defaultdict(list)
    for e in valid_entries:
        by_code[e['code']].append(e)
    
    for code, req in CHECKLIST_REQUIRED.items():
        label = req['label']
        count = len(by_code.get(code, []))
        
        # 检查是否至少有要求的最低数量
        has_required = count >= req['min']
        
        # 检查是否有未签认的
        pending = [e for e in by_code.get(code, []) if e['status'] != '已签认']
        
        checklist[code] = {
            'label': label,
            'required_min': req['min'],
            'actual_count': count,
            'passed': has_required,
            'pending_count': len(pending),
            'pending_files': [e['filename'] for e in pending],
        }
    
    return checklist


def print_report(result):
    """打印格式化的检查报告"""
    p = result['project_path']
    name = result['project_name']
    
    print(f"\n{'='*60}")
    print(f"  📋 证据链检查报告")
    print(f"  📁 项目: {name}")
    print(f"  📂 路径: {p}")
    print(f"{'='*60}\n")
    
    print(f"  📊 总体统计")
    print(f"  ───────────")
    print(f"  总文件数:      {result['total_files']}")
    print(f"  ✅ 命名合规:    {result['valid_files']}")
    print(f"  ❌ 命名不合规:  {result['invalid_files']}")
    
    if result['missing_dirs']:
        print(f"\n  ⚠️  缺失的标准目录（建议创建）：")
        for d in result['missing_dirs']:
            print(f"    mkdir -p \"{d}\"")
    
    # 按类别统计
    if result['by_category']:
        print(f"\n  📂 按类别统计")
        print(f"  ─────────────")
        # 按代码排序
        for code in sorted(result['by_category'].keys()):
            info = result['by_category'][code]
            cat_name = CATEGORY_CODES.get(code, code)
            marker = '✅' if info['valid'] > 0 else '🔴'
            print(f"  {marker} {code:12s} {cat_name:12s} {info['valid']:3d} 份文件")
    
    # 按状态统计
    if result['by_status']:
        print(f"\n  📌 按签认状态统计")
        print(f"  ────────────────")
        for status in ['已签认', '待确认', '已否决', '自行归档']:
            if status in result['by_status']:
                icon = {'已签认': '✅', '待确认': '⏳', '已否决': '❌', '自行归档': '📄'}
                print(f"  {icon.get(status, '❓')} {status}: {result['by_status'][status]} 份")
    
    # 结算清单检查
    print(f"\n  ✅ 结算清单检查")
    print(f"  ───────────────")
    all_pass = True
    for code, item in sorted(result['checklist'].items()):
        if item['passed']:
            print(f"  ✅ {item['label']:20s} {item['actual_count']} 份 (合格)")
        else:
            all_pass = False
            print(f"  ❌ {item['label']:20s} {item['actual_count']} 份 (要求 ≥{item['required_min']})")
        if item['pending_count'] > 0:
            print(f"     ⏳ 未签认: {', '.join(item['pending_files'])}")
    
    if all_pass:
        print(f"  🎉 全部通过！可正常进入结算流程。")
    else:
        print(f"  ⚠️  有缺项，结算前需要补全！")
    
    # 问题汇总
    if result['issues']:
        print(f"\n  ❌ 问题汇总（共 {len(result['issues'])} 个）")
        print(f"  ───────────────")
        for issue in result['issues']:
            print(f"  • {issue}")
    
    print(f"\n{'='*60}\n")


def export_csv(project_path, result, output_path=None):
    """导出证据清单CSV"""
    if not output_path:
        output_path = os.path.join(project_path, '证据清单_导出.csv')
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '文件日期', '类别', '类别缩写', '文件简述', '版本号', '签认状态', '存放路径', '文件名'])
        
        for i, entry in enumerate(result['valid_entries'], 1):
            writer.writerow([
                i,
                entry['date'],
                entry['category'],
                entry['code'],
                entry['description'],
                entry['version'],
                entry['status'],
                entry['path'],
                entry['filename'],
            ])
    
    return output_path


def init_project(project_path, project_name):
    """初始化一个新项目文件夹结构"""
    base = os.path.join(project_path, project_name)
    if os.path.exists(base):
        print(f"⚠️  项目 '{project_name}' 已存在，跳过创建。")
        return base
    
    created = []
    for std_dir in STANDARD_DIRS:
        dir_path = os.path.join(base, std_dir)
        os.makedirs(dir_path, exist_ok=True)
        created.append(dir_path)
    
    # 创建项目基本信息
    info_path = os.path.join(base, '00-项目概览', '项目基本信息.md')
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(f"# {project_name} 项目基本信息\n\n")
        f.write(f"项目名称：{project_name}\n")
        f.write(f"项目编号：\n")
        f.write(f"合同金额：\n")
        f.write(f"开工日期：\n")
        f.write(f"竣工日期：\n")
        f.write(f"建设单位：\n")
        f.write(f"施工单位：\n")
        f.write(f"监理单位：\n")
    
    print(f"✅ 项目 '{project_name}' 创建成功！")
    print(f"📂 路径: {base}")
    print(f"📁 共创建 {len(created)} 个标准文件夹")
    
    return base


# ============================================================
# 入口
# ============================================================

def main():
    if len(sys.argv) < 2:
        # 默认检查当前目录
        path = os.getcwd()
        print(f"🔍 检查当前目录: {path}")
        project_root = find_project_root(path)
        if project_root:
            result = scan_project(project_root)
            print_report(result)
        else:
            # 扫描当前目录下所有项目
            projects = scan_all_projects(path)
            if projects:
                print(f"🔍 发现 {len(projects)} 个项目:")
                for p in projects:
                    result = scan_project(p)
                    print_report(result)
            else:
                print("⚠️  当前目录下未找到项目文件夹。")
                print("   用法: python evidence_check.py <项目路径>")
                print("         python evidence_check.py --init <项目名>")
                return
        return
    
    cmd = sys.argv[1]
    
    if cmd == '--init':
        if len(sys.argv) < 3:
            print("用法: python evidence_check.py --init <项目名>")
            return
        init_project(os.getcwd(), sys.argv[2])
        return
    
    if cmd == '--scan-all':
        base = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        projects = scan_all_projects(base)
        if not projects:
            print(f"⚠️  在 '{base}' 下未找到项目。")
            return
        print(f"🔍 共发现 {len(projects)} 个项目:\n")
        for p in projects:
            result = scan_project(p)
            print_report(result)
        return
    
    if cmd == '--export':
        if len(sys.argv) < 3:
            print("用法: python evidence_check.py --export <项目路径>")
            return
        project_root = find_project_root(sys.argv[2])
        if not project_root:
            print(f"⚠️  '{sys.argv[2]}' 不是有效的项目文件夹。")
            return
        result = scan_project(project_root)
        out = export_csv(project_root, result)
        print(f"✅ 证据清单已导出: {out}")
        return
    
    # 检查指定路径
    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"⚠️  路径不存在: {target}")
        return
    
    project_root = find_project_root(target)
    if project_root:
        result = scan_project(project_root)
        print_report(result)
    else:
        # 可能是根目录，扫描子项目
        projects = scan_all_projects(target)
        if projects:
            print(f"🔍 发现 {len(projects)} 个项目:")
            for p in projects:
                result = scan_project(p)
                print_report(result)
        else:
            print(f"⚠️  '{target}' 下未找到项目文件夹。")


if __name__ == '__main__':
    main()
