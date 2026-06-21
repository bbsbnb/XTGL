#!/usr/bin/env python3
"""
工程项目证据链管理系统 — Web 前端服务器
========================================
启动: python evidence_web.py
访问: http://localhost:5000
"""

import os
import sys
import json
import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_file, render_template

# ============================================================
# 配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == '模板与规则':
    BASE_DIR = os.path.dirname(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, '证据链数据库.db')
TEMPLATE_DIR = os.path.join(BASE_DIR, '模板与规则', 'templates')
os.makedirs(TEMPLATE_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=BASE_DIR)
app.config['JSON_AS_ASCII'] = False

# ============================================================
# 数据库工具
# ============================================================

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

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    return conn


def init_db_if_needed():
    """如果数据库不存在则初始化"""
    if not os.path.exists(DB_PATH):
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
        """)
        conn.commit()
        conn.close()
        return True
    return False


def row_to_dict(row):
    """将 sqlite3.Row 转为 dict"""
    return dict(row) if row else None


# ============================================================
# API 路由
# ============================================================

# ------- 首页 -------

@app.route('/')
def index():
    return render_template('index.html')


# ------- 初始化 -------

@app.route('/api/init', methods=['POST'])
def api_init():
    created = init_db_if_needed()
    return jsonify({'ok': True, 'created': created})


# ------- 项目列表 -------

@app.route('/api/projects')
def api_projects():
    conn = get_db()
    rows = conn.execute("""
        SELECT project_name,
               COUNT(*) as total,
               SUM(CASE WHEN status = '已签认' THEN 1 ELSE 0 END) as signed,
               SUM(CASE WHEN status = '待确认' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = '已否决' THEN 1 ELSE 0 END) as rejected
        FROM evidence
        GROUP BY project_name
        ORDER BY project_name
    """).fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


# ------- 证据列表（支持筛选） -------

@app.route('/api/evidence')
def api_evidence():
    project = request.args.get('project', '')
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    conn = get_db()
    query = "SELECT * FROM evidence WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM evidence WHERE 1=1"
    params = []
    
    if project:
        query += " AND project_name LIKE ?"
        count_query += " AND project_name LIKE ?"
        params.append(f"%{project}%")
    if status:
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category_code = ?"
        count_query += " AND category_code = ?"
        params.append(category)
    if search:
        like = f"%{search}%"
        query += " AND (project_name LIKE ? OR description LIKE ? OR category_name LIKE ? OR notes LIKE ? OR status LIKE ? OR filename LIKE ?)"
        count_query += " AND (project_name LIKE ? OR description LIKE ? OR category_name LIKE ? OR notes LIKE ? OR status LIKE ? OR filename LIKE ?)"
        params.extend([like] * 6)
    
    total = conn.execute(count_query, params).fetchone()[0]
    
    offset = (page - 1) * page_size
    query += " ORDER BY file_date DESC, id DESC LIMIT ? OFFSET ?"
    rows = conn.execute(query, params + [page_size, offset]).fetchall()
    conn.close()
    
    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'data': [row_to_dict(r) for r in rows],
    })


# ------- 单条详情 -------

@app.route('/api/evidence/<int:eid>')
def api_evidence_detail(eid):
    conn = get_db()
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    conn.close()
    if not row:
        return jsonify({'ok': False, 'error': '记录不存在'}), 404
    return jsonify(row_to_dict(row))


# ------- 新增 -------

@app.route('/api/evidence', methods=['POST'])
def api_evidence_add():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': '无效请求'}), 400
    
    required = ['project_name', 'file_date', 'category_code', 'description']
    for field in required:
        if not data.get(field):
            return jsonify({'ok': False, 'error': f'缺少必填字段: {field}'}), 400
    
    code = data['category_code'].upper()
    if code not in CATEGORY_CODES:
        return jsonify({'ok': False, 'error': f'无效类别代码: {code}'}), 400
    
    status = data.get('status', '待确认')
    if status not in VALID_STATUSES:
        status = '待确认'
    
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO evidence (project_name, file_date, category_code, category_name,
                              description, version, status, file_path, filename, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['project_name'].strip(),
        data['file_date'].strip(),
        code,
        CATEGORY_CODES[code],
        data['description'].strip(),
        data.get('version', 'v1.0').strip(),
        status,
        data.get('file_path', '').strip(),
        data.get('filename', '').strip(),
        data.get('notes', '').strip(),
    ))
    conn.commit()
    eid = cur.lastrowid
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    conn.close()
    
    return jsonify({'ok': True, 'data': row_to_dict(row)}), 201


# ------- 编辑 -------

@app.route('/api/evidence/<int:eid>', methods=['PUT'])
def api_evidence_edit(eid):
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': '无效请求'}), 400
    
    conn = get_db()
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    if not row:
        conn.close()
        return jsonify({'ok': False, 'error': '记录不存在'}), 404
    
    # 只更新提供的字段
    updates = {}
    for field in ['project_name', 'file_date', 'description', 'version', 'file_path', 'filename', 'notes']:
        if field in data:
            updates[field] = data[field].strip()
    
    if 'category_code' in data:
        code = data['category_code'].upper()
        if code in CATEGORY_CODES:
            updates['category_code'] = code
            updates['category_name'] = CATEGORY_CODES[code]
    
    if 'status' in data:
        st = data['status']
        if st in VALID_STATUSES:
            updates['status'] = st
    
    if not updates:
        conn.close()
        return jsonify({'ok': False, 'error': '没有有效更新字段'}), 400
    
    updates['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [eid]
    conn.execute(f"UPDATE evidence SET {set_clause} WHERE id = ?", values)
    conn.commit()
    
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    conn.close()
    
    return jsonify({'ok': True, 'data': row_to_dict(row)})


# ------- 删除 -------

@app.route('/api/evidence/<int:eid>', methods=['DELETE'])
def api_evidence_delete(eid):
    conn = get_db()
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", [eid]).fetchone()
    if not row:
        conn.close()
        return jsonify({'ok': False, 'error': '记录不存在'}), 404
    
    conn.execute("DELETE FROM evidence WHERE id = ?", [eid])
    conn.commit()
    conn.close()
    
    return jsonify({'ok': True, 'deleted': eid})


# ------- 统计 -------

@app.route('/api/stats')
def api_stats():
    project = request.args.get('project', '')
    conn = get_db()
    
    where = ""
    params = []
    if project:
        where = " WHERE project_name LIKE ?"
        params.append(f"%{project}%")
    
    total = conn.execute(f"SELECT COUNT(*) FROM evidence{where}", params).fetchone()[0]
    
    by_status = conn.execute(f"""
        SELECT status, COUNT(*) as cnt FROM evidence{where} GROUP BY status ORDER BY cnt DESC
    """, params).fetchall()
    
    by_category = conn.execute(f"""
        SELECT category_code, category_name, COUNT(*) as cnt 
        FROM evidence{where} GROUP BY category_code ORDER BY cnt DESC
    """, params).fetchall()
    
    by_month = conn.execute(f"""
        SELECT substr(file_date, 1, 7) as month, COUNT(*) as cnt
        FROM evidence{where}
        GROUP BY month ORDER BY month DESC LIMIT 12
    """, params).fetchall()
    
    recent = conn.execute(f"""
        SELECT * FROM evidence{where} ORDER BY created_at DESC LIMIT 5
    """, params).fetchall()
    
    conn.close()
    
    return jsonify({
        'total': total,
        'by_status': [row_to_dict(r) for r in by_status],
        'by_category': [row_to_dict(r) for r in by_category],
        'by_month': [row_to_dict(r) for r in by_month],
        'recent': [row_to_dict(r) for r in recent],
    })


# ------- 类别列表 -------

@app.route('/api/categories')
def api_categories():
    return jsonify([{'code': k, 'name': v} for k, v in sorted(CATEGORY_CODES.items())])


# ------- 导出 CSV -------

@app.route('/api/export')
def api_export():
    project = request.args.get('project', '')
    conn = get_db()
    
    if project:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE project_name LIKE ? ORDER BY file_date, id",
            [f"%{project}%"]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM evidence ORDER BY project_name, file_date, id"
        ).fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['序号', '项目名称', '文件日期', '类别缩写', '类别名称',
                     '文件简述', '版本号', '签认状态', '存放路径', '文件名', '备注'])
    
    for i, r in enumerate(rows, 1):
        writer.writerow([
            i, r['project_name'], r['file_date'], r['category_code'],
            r['category_name'], r['description'], r['version'],
            r['status'], r['file_path'], r['filename'], r['notes']
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'证据清单_{project or "全部"}_{timestamp}.csv'
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv; charset=utf-8-sig',
        as_attachment=True,
        download_name=filename,
    )


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    init_db_if_needed()
    print(f"✅ 数据库: {DB_PATH}")
    print(f"✅ 启动服务器: http://localhost:5000")
    print(f"   按 Ctrl+C 停止")
    app.run(host='0.0.0.0', port=5000, debug=True)
