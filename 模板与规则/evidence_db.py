#!/usr/bin/env python3
"""
工程项目证据链管理系统 — SQLite数据库索引工具
===============================================
用法:
  python evidence_db.py init                          # 初始化数据库
  python evidence_db.py list [项目名]                 # 列出所有记录
  python evidence_db.py add                           # 交互式添加记录
  python evidence_db.py search <关键词>               # 搜索
  python evidence_db.py stats [项目名]                # 统计
  python evidence_db.py import <CSV文件>              # 从CSV导入
  python evidence_db.py export [项目名]               # 导出CSV
  python evidence_db.py info <序号>                   # 查看单条详情
  python evidence_db.py edit <序号>                   # 编辑记录
  python evidence_db.py delete <序号>                 # 删除记录
  python evidence_db.py projects                      # 列出所有项目
"""

import os
import sys
import csv
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ============================================================
# 配置
# ============================================================

DB_DIR = os.path.dirname(os.path.abspath(__file__))
if '模板与规则' in DB_DIR:
    DB_DIR = os.path.dirname(DB_DIR)
DB_PATH = os.path.join(DB_DIR, '证据链数据库.db')

CATEGORY_CODES = {
    'HT': '合同文件', 'ZBTZ': '中标通知书', 'KGBG': '开工报告',
    'VS': '签证单', 'XCQR': '现场确认单', 'FYQR': '费用签认单',
    'BG': '变更通知单', 'BGTZ': '变更图纸', 'BQQS': '变更洽商', 'BGFY': '变更费用报审',
    'RZ': '施工日志', 'CLJZ': '材料进场验收', 'JYP': '检验批记录', 'HYJY': '会议纪要',
    'YBGC': '隐蔽工程验收', 'FFBX': '分部分项验收', 'JGYS': '竣工验收', 'ZGTZ': '整改通知',
    'GCL': '工程量确认单', 'JDK': '进度款申请', 'JSS': '结算书', 'DZD': '对账单',
    'JLF': '甲方来函', 'WFF': '我方发函', 'JLTZ': '监理通知', 'QDD': '会议签到表',
    'PHOTO-SG': '施工过程照片', 'PHOTO-YB': '隐蔽工程照片',
    'PHOTO-YS': '验收照片', 'PHOTO-QJ': '全景照片',
}

VALID_STATUSES = ('已签认', '待确认', '已否决', '自行归档')

# ============================================================
# 数据库操作
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    return conn


def init_db(force=False):
    """初始化数据库表"""
    if os.path.exists(DB_PATH) and not force:
        print(f"✅ 数据库已存在: {DB_PATH}")
        return
    
    if os.path.exists(DB_PATH) and force:
        os.remove(DB_PATH)
        print(f"🔄 已重建数据库")
    
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            file_date TEXT NOT NULL,
            category_code TEXT NOT NULL,
            category_name TEXT NOT NULL,
            description TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT 'v1.0',
            status TEXT NOT NULL DEFAULT '待确认',
            file_path TEXT,
            filename TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_project ON evidence(project_name);
        CREATE INDEX IF NOT EXISTS idx_category ON evidence(category_code);
        CREATE INDEX IF NOT EXISTS idx_status ON evidence(status);
        CREATE INDEX IF NOT EXISTS idx_date ON evidence(file_date);
        
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            full_name TEXT,
            folder_path TEXT,
            contract_amount TEXT,
            start_date TEXT,
            end_date TEXT,
            owner TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


def add_evidence(conn, record):
    """添加一条证据记录"""
    conn.execute("""
        INSERT INTO evidence (project_name, file_date, category_code, category_name,
                              description, version, status, file_path, filename, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record['project_name'],
        record['file_date'],
        record['category_code'],
        CATEGORY_CODES.get(record['category_code'], record['category_code']),
        record['description'],
        record.get('version', 'v1.0'),
        record.get('status', '待确认'),
        record.get('file_path', ''),
        record.get('filename', ''),
        record.get('notes', ''),
    ))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def add_interactive():
    """交互式添加记录"""
    conn = get_db()
    
    print("\n📝 新增证据记录")
    print("─" * 40)
    
    project = input("项目名称: ").strip()
    while not project:
        project = input("项目名称（必填）: ").strip()
    
    date_str = input("文件日期 (YYYY-MM-DD, 留空=今天): ").strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print("\n类别代码:")
    for code, name in sorted(CATEGORY_CODES.items()):
        print(f"  {code:12s} {name}")
    
    code = input("\n类别代码: ").strip().upper()
    while code not in CATEGORY_CODES:
        print(f"⚠️  无效代码，可选: {', '.join(sorted(CATEGORY_CODES.keys()))}")
        code = input("类别代码: ").strip().upper()
    
    desc = input("文件简述: ").strip()
    while not desc:
        desc = input("文件简述（必填）: ").strip()
    
    version = input("版本号 (默认 v1.0): ").strip() or 'v1.0'
    
    print(f"\n状态选项: {', '.join(VALID_STATUSES)}")
    status = input("签认状态 (默认 待确认): ").strip() or '待确认'
    while status not in VALID_STATUSES:
        print(f"⚠️  无效状态，可选: {', '.join(VALID_STATUSES)}")
        status = input("签认状态: ").strip()
    
    file_path = input("文件存放路径（相对于项目文件夹, 可选）: ").strip()
    filename = input("文件名（可选）: ").strip()
    notes = input("备注（可选）: ").strip()
    
    record = {
        'project_name': project,
        'file_date': date_str,
        'category_code': code,
        'description': desc,
        'version': version,
        'status': status,
        'file_path': file_path,
        'filename': filename,
        'notes': notes,
    }
    
    eid = add_evidence(conn, record)
    conn.close()
    
    print(f"\n✅ 已添加记录 (编号: {eid})")


def list_records(conn, project_filter=None, status_filter=None, code_filter=None):
    """列出记录，支持筛选"""
    query = "SELECT * FROM evidence WHERE 1=1"
    params = []
    
    if project_filter:
        query += " AND project_name LIKE ?"
        params.append(f"%{project_filter}%")
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if code_filter:
        query += " AND category_code = ?"
        params.append(code_filter)
    
    query += " ORDER BY file_date DESC, id DESC"
    
    rows = conn.execute(query, params).fetchall()
    return rows


def print_records(rows, show_all=False):
    """打印记录列表"""
    if not rows:
        print("\n📭 没有找到记录。")
        return
    
    print(f"\n📋 共 {len(rows)} 条记录:")
    print("─" * 100 if show_all else "─" * 80)
    
    if show_all:
        header = f"{'ID':>4} {'日期':12s} {'项目':20s} {'类别':10s} {'简述':30s} {'版本':8s} {'状态':8s}"
        print(header)
        print("─" * 100)
        for r in rows:
            print(f"{r['id']:>4d} {r['file_date']:12s} {r['project_name']:20s} {r['category_code']:10s} {r['description']:30s} {r['version']:8s} {r['status']:8s}")
    else:
        header = f"{'ID':>4} {'日期':12s} {'类别':10s} {'简述':50s} {'状态':8s}"
        print(header)
        print("─" * 80)
        for r in rows:
            desc = r['description'][:50] if len(r['description']) > 50 else r['description']
            print(f"{r['id']:>4d} {r['file_date']:12s} {r['category_code']:10s} {desc:50s} {r['status']:8s}")
    
    print("─" * 80)


def search_records(conn, keyword):
    """搜索记录"""
    query = """
        SELECT * FROM evidence 
        WHERE project_name LIKE ? 
           OR description LIKE ? 
           OR category_name LIKE ?
           OR status LIKE ?
           OR notes LIKE ?
           OR filename LIKE ?
        ORDER BY file_date DESC
    """
    like = f"%{keyword}%"
    rows = conn.execute(query, [like, like, like, like, like, like]).fetchall()
    return rows


def print_stats(conn, project_filter=None):
    """打印统计信息"""
    if project_filter:
        where = " WHERE project_name LIKE ?"
        params = [f"%{project_filter}%"]
    else:
        where = ""
        params = []
    
    # 总记录数
    total = conn.execute(f"SELECT COUNT(*) FROM evidence{where}", params).fetchone()[0]
    
    # 按项目统计
    rows = conn.execute(f"""
        SELECT project_name, COUNT(*) as cnt 
        FROM evidence{where} 
        GROUP BY project_name 
        ORDER BY cnt DESC
    """, params).fetchall()
    
    # 按类别统计
    cat_rows = conn.execute(f"""
        SELECT category_code, category_name, COUNT(*) as cnt 
        FROM evidence{where} 
        GROUP BY category_code 
        ORDER BY cnt DESC
    """, params).fetchall()
    
    # 按状态统计
    status_rows = conn.execute(f"""
        SELECT status, COUNT(*) as cnt 
        FROM evidence{where} 
        GROUP BY status 
        ORDER BY cnt DESC
    """, params).fetchall()
    
    # 按月份统计（最近12个月）
    month_rows = conn.execute(f"""
        SELECT substr(file_date, 1, 7) as month, COUNT(*) as cnt
        FROM evidence{where}
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """, params).fetchall()
    
    print(f"\n📊 统计报告")
    print("═" * 50)
    print(f"  总证据数: {total}")
    
    if project_filter:
        print(f"  项目筛选: {project_filter}")
    
    print(f"\n📁 按项目:")
    for r in rows:
        print(f"  {r['project_name']:30s} {r['cnt']:3d} 份")
    
    print(f"\n📂 按类别:")
    for r in cat_rows:
        print(f"  {r['category_code']:12s} {r['category_name']:12s} {r['cnt']:3d} 份")
    
    print(f"\n📌 按签认状态:")
    icons = {'已签认': '✅', '待确认': '⏳', '已否决': '❌', '自行归档': '📄'}
    for r in status_rows:
        icon = icons.get(r['status'], '❓')
        print(f"  {icon} {r['status']:8s} {r['cnt']:3d} 份")
    
    if month_rows:
        print(f"\n📅 按月趋势（最近12个月）:")
        for r in month_rows:
            print(f"  {r['month']:10s} {'█' * (r['cnt'])} {r['cnt']}")
    
    print("═" * 50)


def info_record(conn, eid):
    """查看单条记录详情"""
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    if not row:
        print(f"⚠️  记录 #{eid} 不存在。")
        return
    
    print(f"\n📄 证据详情 (编号: {row['id']})")
    print("═" * 50)
    print(f"  项目名称:    {row['project_name']}")
    print(f"  文件日期:    {row['file_date']}")
    print(f"  类别:        {row['category_code']} ({row['category_name']})")
    print(f"  简述:        {row['description']}")
    print(f"  版本号:      {row['version']}")
    print(f"  签认状态:    {row['status']}")
    print(f"  存放路径:    {row['file_path'] or '(未填写)'}")
    print(f"  文件名:      {row['filename'] or '(未填写)'}")
    print(f"  备注:        {row['notes'] or '(无)'}")
    print(f"  创建时间:    {row['created_at']}")
    print(f"  更新时间:    {row['updated_at']}")
    print("═" * 50)


def edit_record(conn, eid):
    """编辑单条记录"""
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    if not row:
        print(f"⚠️  记录 #{eid} 不存在。")
        return
    
    print(f"\n✏️  编辑记录 #{eid}（直接回车保持原值）")
    print("─" * 50)
    
    fields = [
        ('project_name', '项目名称'),
        ('file_date', '文件日期 (YYYY-MM-DD)'),
        ('category_code', f'类别代码 ({", ".join(sorted(CATEGORY_CODES.keys()))})'),
        ('description', '文件简述'),
        ('version', '版本号'),
        ('status', f'签认状态 ({", ".join(VALID_STATUSES)})'),
        ('file_path', '文件存放路径'),
        ('filename', '文件名'),
        ('notes', '备注'),
    ]
    
    updates = {}
    for field, prompt in fields:
        current = row[field] or ''
        val = input(f"{prompt} [{current}]: ").strip()
        if val:
            updates[field] = val
    
    if not updates:
        print("没有修改。")
        return
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    updates['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    set_clause += ", updated_at = ?"
    
    values = list(updates.values()) + [eid]
    conn.execute(f"UPDATE evidence SET {set_clause} WHERE id = ?", values)
    conn.commit()
    
    print(f"✅ 记录 #{eid} 已更新。")


def delete_record(conn, eid):
    """删除记录"""
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    if not row:
        print(f"⚠️  记录 #{eid} 不存在。")
        return
    
    print(f"\n🗑️  确认删除:")
    print(f"  ID: {row['id']}")
    print(f"  项目: {row['project_name']}")
    print(f"  简述: {row['description']}")
    confirm = input("\n确认删除? (y/N): ").strip().lower()
    
    if confirm == 'y':
        conn.execute("DELETE FROM evidence WHERE id = ?", [eid])
        conn.commit()
        print(f"✅ 记录 #{eid} 已删除。")
    else:
        print("已取消。")


def import_csv(conn, csv_path):
    """从CSV导入记录"""
    if not os.path.exists(csv_path):
        print(f"⚠️  文件不存在: {csv_path}")
        return
    
    encodings = ['utf-8-sig', 'gbk', 'gb18030', 'utf-8']
    for enc in encodings:
        try:
            with open(csv_path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                count = 0
                errors = []
                
                for i, row in enumerate(reader, 2):
                    try:
                        project = row.get('项目名称', row.get('project_name', '')).strip()
                        date = row.get('文件日期', row.get('file_date', row.get('日期', ''))).strip()
                        code = row.get('类别缩写', row.get('category_code', row.get('类别', ''))).strip().upper()
                        desc = row.get('文件简述', row.get('description', row.get('简述', ''))).strip()
                        ver = row.get('版本号', row.get('version', 'v1.0')).strip()
                        st = row.get('签认状态', row.get('status', '待确认')).strip()
                        fp = row.get('存放路径', row.get('file_path', '')).strip()
                        fn = row.get('文件名', row.get('filename', '')).strip()
                        notes = row.get('备注', row.get('notes', '')).strip()
                        
                        if not project or not date or not code or not desc:
                            errors.append(f"  第{i}行: 缺少必填字段")
                            continue
                        
                        if code not in CATEGORY_CODES:
                            errors.append(f"  第{i}行: 无效类别代码 '{code}'")
                            continue
                        
                        if st not in VALID_STATUSES:
                            st = '待确认'
                        
                        record = {
                            'project_name': project,
                            'file_date': date,
                            'category_code': code,
                            'description': desc,
                            'version': ver,
                            'status': st,
                            'file_path': fp,
                            'filename': fn,
                            'notes': notes,
                        }
                        add_evidence(conn, record)
                        count += 1
                    
                    except Exception as e:
                        errors.append(f"  第{i}行: {e}")
                
                if count > 0:
                    print(f"✅ 成功导入 {count} 条记录")
                if errors:
                    print(f"⚠️  {len(errors)} 个错误:")
                    for e in errors:
                        print(f"  {e}")
                return
        
        except UnicodeDecodeError:
            continue
    
    print(f"⚠️  无法读取文件编码: {csv_path}")


def export_csv(conn, project_filter=None, output_path=None):
    """导出记录到CSV"""
    if project_filter:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE project_name LIKE ? ORDER BY file_date, id",
            [f"%{project_filter}%"]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM evidence ORDER BY project_name, file_date, id"
        ).fetchall()
    
    if not rows:
        print("📭 没有记录可导出。")
        return
    
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(DB_DIR, f'证据清单_导出_{timestamp}.csv')
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '项目名称', '文件日期', '类别缩写', '类别名称',
                        '文件简述', '版本号', '签认状态', '存放路径', '文件名', '备注'])
        
        for i, r in enumerate(rows, 1):
            writer.writerow([
                i, r['project_name'], r['file_date'], r['category_code'],
                r['category_name'], r['description'], r['version'],
                r['status'], r['file_path'], r['filename'], r['notes']
            ])
    
    print(f"✅ 已导出 {len(rows)} 条记录到: {output_path}")


def list_projects(conn):
    """列出所有项目及其统计"""
    rows = conn.execute("""
        SELECT project_name, COUNT(*) as cnt,
               SUM(CASE WHEN status = '已签认' THEN 1 ELSE 0 END) as signed,
               SUM(CASE WHEN status = '待确认' THEN 1 ELSE 0 END) as pending
        FROM evidence
        GROUP BY project_name
        ORDER BY project_name
    """).fetchall()
    
    if not rows:
        print("\n📭 还没有项目记录。")
        return
    
    print(f"\n📁 项目列表 ({len(rows)} 个)")
    print("═" * 60)
    total_all = sum(r['cnt'] for r in rows)
    signed_all = sum(r['signed'] for r in rows)
    pending_all = sum(r['pending'] for r in rows)
    
    for r in rows:
        pct = r['signed'] / r['cnt'] * 100 if r['cnt'] > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        print(f"  {r['project_name']:30s} {r['cnt']:3d} 份  ✅{r['signed']} ⏳{r['pending']}  {bar} {pct:.0f}%")
    
    print("═" * 60)
    print(f"  {'合计':30s} {total_all:3d} 份  ✅{signed_all} ⏳{pending_all}")


# ============================================================
# 主入口
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'init':
        force = '--force' in sys.argv or '-f' in sys.argv
        init_db(force)
        return
    
    # 以下命令需要数据库
    if not os.path.exists(DB_PATH):
        print(f"⚠️  数据库不存在，请先运行: python evidence_db.py init")
        return
    
    conn = get_db()
    
    try:
        if cmd == 'list':
            project = sys.argv[2] if len(sys.argv) > 2 else None
            status = sys.argv[3] if len(sys.argv) > 3 else None
            code = sys.argv[4] if len(sys.argv) > 4 else None
            rows = list_records(conn, project, status, code)
            show_all = len(sys.argv) > 3
            print_records(rows, show_all)
        
        elif cmd == 'add':
            add_interactive()
        
        elif cmd == 'search':
            if len(sys.argv) < 3:
                print("用法: python evidence_db.py search <关键词>")
                return
            keyword = sys.argv[2]
            rows = search_records(conn, keyword)
            print_records(rows, show_all=True)
        
        elif cmd == 'stats':
            project = sys.argv[2] if len(sys.argv) > 2 else None
            print_stats(conn, project)
        
        elif cmd == 'import':
            if len(sys.argv) < 3:
                print("用法: python evidence_db.py import <CSV文件路径>")
                return
            import_csv(conn, sys.argv[2])
        
        elif cmd == 'export':
            project = sys.argv[2] if len(sys.argv) > 2 else None
            output = sys.argv[3] if len(sys.argv) > 3 else None
            export_csv(conn, project, output)
        
        elif cmd == 'info':
            if len(sys.argv) < 3:
                print("用法: python evidence_db.py info <序号>")
                return
            info_record(conn, int(sys.argv[2]))
        
        elif cmd == 'edit':
            if len(sys.argv) < 3:
                print("用法: python evidence_db.py edit <序号>")
                return
            edit_record(conn, int(sys.argv[2]))
        
        elif cmd == 'delete':
            if len(sys.argv) < 3:
                print("用法: python evidence_db.py delete <序号>")
                return
            delete_record(conn, int(sys.argv[2]))
        
        elif cmd == 'projects':
            list_projects(conn)
        
        else:
            print(f"未知命令: {cmd}")
            print(__doc__)
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()
