#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工程项目证据链管理系统 - Web 后端服务器 (v2.0)
"""
import os,sys,json,csv,io,re,hashlib,uuid
from datetime import datetime, date
from functools import wraps
from flask import Flask,request,jsonify,send_file,send_from_directory,session,g

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT=os.path.dirname(BASE_DIR)
UPLOAD_DIR=os.path.join(BASE_DIR,"uploads")
DB_PATH=os.path.join(PROJECT_ROOT,"证据链数据库.db")
TEMPLATE_DIR=os.path.join(BASE_DIR,"templates")
os.makedirs(UPLOAD_DIR,exist_ok=True);os.makedirs(TEMPLATE_DIR,exist_ok=True)
app=Flask(__name__,template_folder=TEMPLATE_DIR,static_folder=BASE_DIR)
app.config["JSON_AS_ASCII"]=False
app.config["SECRET_KEY"]="evidence-chain-secret-key-2024"
app.config["MAX_CONTENT_LENGTH"]=50*1024*1024

import sqlite3
def get_db():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
def row_to_dict(r): return dict(r) if r else None
def rows_to_list(rs): return [dict(r) for r in rs]
def init_database():
    conn=get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '施工员',
            phone TEXT DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            full_name TEXT DEFAULT '',
            code TEXT DEFAULT '',
            contract_amount REAL DEFAULT 0,
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            owner TEXT DEFAULT '',
            status TEXT DEFAULT '进行中',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER DEFAULT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_no TEXT UNIQUE NOT NULL,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            tags TEXT DEFAULT '[]',
            event_time TEXT,
            description TEXT DEFAULT '',
            solution TEXT DEFAULT '',
            quantity REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            contract_no TEXT DEFAULT '',
            related_parties TEXT DEFAULT '[]',
            location TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT '待提交',
            is_deleted INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            file_path TEXT NOT NULL,
            uploaded_by INTEGER,
            uploaded_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS approval_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER NOT NULL,
            approval_level TEXT NOT NULL,
            approver_id INTEGER,
            result TEXT NOT NULL DEFAULT '待审核',
            comment TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
            FOREIGN KEY (approver_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            required_items TEXT NOT NULL DEFAULT '[]',
            description TEXT DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER,
            rule_id INTEGER,
            alert_type TEXT NOT NULL DEFAULT 'missing',
            severity TEXT NOT NULL DEFAULT '中',
            title TEXT NOT NULL,
            message TEXT DEFAULT '',
            is_dismissed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        );
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT DEFAULT '',
            target_id INTEGER,
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence(project_id);
        CREATE INDEX IF NOT EXISTS idx_evidence_category ON evidence(category_id);
        CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);
        CREATE INDEX IF NOT EXISTS idx_evidence_date ON evidence(event_time);
        CREATE INDEX IF NOT EXISTS idx_evidence_no ON evidence(evidence_no);
        CREATE INDEX IF NOT EXISTS idx_approval_eid ON approval_records(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_attachments_eid ON attachments(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_eid ON alerts(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_logs_user ON activity_logs(user_id);
CREATE TABLE IF NOT EXISTS settlement_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    project_id INTEGER NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS settlement_package_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (package_id) REFERENCES settlement_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);

    ''')
    if conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0] == 0:
        cats=[
            ('HT','合同文件',None,1,1),('ZBTZ','中标通知书',None,1,2),
            ('KGBG','开工报告',None,1,3),('BG','变更类',None,1,4),
            ('VS','签证单',4,2,1),('XCQR','现场确认单',4,2,2),
            ('FYQR','费用签认单',4,2,3),('BGTZ','变更图纸',4,2,4),
            ('BQQS','变更洽商',4,2,5),('BGFY','变更费用报审',4,2,6),
            ('SG','施工过程',None,1,5),('RZ','施工日志',11,2,1),
            ('CLJZ','材料进场验收',11,2,2),('JYP','检验批记录',11,2,3),
            ('HYJY','会议纪要',11,2,4),('YS','验收记录',None,1,6),
            ('YBGC','隐蔽工程验收',16,2,1),('FFBX','分部分项验收',16,2,2),
            ('JGYS','竣工验收',16,2,3),('ZGTZ','整改通知',16,2,4),
            ('GCL','工程量确认单',11,2,5),('JJ','计价结算',None,1,7),
            ('JDK','进度款申请',22,2,1),('JSS','结算书',22,2,2),
            ('DZD','对账单',22,2,3),('WL','往来函件',None,1,8),
            ('JLF','甲方来函',26,2,1),('WFF','我方发函',26,2,2),
            ('JLTZ','监理通知',26,2,3),('QDD','会议签到表',26,2,4),
            ('PHOTO','影像资料',None,1,9),('PHOTO-SG','施工过程照片',31,2,1),
            ('PHOTO-YB','隐蔽工程照片',31,2,2),('PHOTO-YS','验收照片',31,2,3),
            ('PHOTO-QJ','全景照片',31,2,4),
        ]
        conn.executemany('INSERT INTO categories (code,name,parent_id,level,sort_order) VALUES (?,?,?,?,?)',cats)
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0:
        us=[
            ('admin',hashlib.sha256('admin123'.encode()).hexdigest(),'系统管理员','项目经理',''),
            ('ziliao',hashlib.sha256('123456'.encode()).hexdigest(),'李资料','资料员',''),
            ('yusuan',hashlib.sha256('123456'.encode()).hexdigest(),'赵预算','预算员',''),
            ('shigong',hashlib.sha256('123456'.encode()).hexdigest(),'王施工','施工员',''),
        ]
        conn.executemany('INSERT INTO users (username,password_hash,display_name,role,phone) VALUES (?,?,?,?,?)',us)
    if conn.execute('SELECT COUNT(*) FROM alert_rules').fetchone()[0]==0:
        m={r['code']:r['id'] for r in conn.execute('SELECT id,code FROM categories').fetchall()}
        conn.execute('INSERT INTO alert_rules (category_id,name,required_items,description) VALUES (?,?,?,?)',
            (m.get('VS'),'变更签证完整性检查','["联系单","照片佐证","工程量","单价"]','变更签证必须包含联系单、照片佐证、工程量和单价'))
        conn.execute('INSERT INTO alert_rules (category_id,name,required_items,description) VALUES (?,?,?,?)',
            (m.get('YBGC'),'隐蔽工程验收完整性检查','["签字盖章页","照片"]','隐蔽工程验收必须有签字盖章页和照片'))
    if conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]==0:
        conn.execute('INSERT INTO projects (name,full_name) VALUES (?,?)',('示例项目-2025-001','示例工程项目'))
    conn.commit(); conn.close()
def gen_evidence_no(pid):
    conn=get_db()
    t=date.today().strftime('%Y%m%d')
    pf=f'PJ{pid}-{t}-'
    l=conn.execute('SELECT evidence_no FROM evidence WHERE evidence_no LIKE ? ORDER BY id DESC LIMIT 1',[f'{pf}%']).fetchone()
    conn.close()
    s=int(l['evidence_no'].split('-')[-1])+1 if l else 1
    return f'{pf}{s:03d}'

def log_act(uid,act,tt='',ti=None,det=''):
    try:
        conn=get_db()
        conn.execute('INSERT INTO activity_logs (user_id,action,target_type,target_id,detail) VALUES (?,?,?,?,?)',(uid,act,tt,ti,det))
        conn.commit(); conn.close()
    except: pass

def login_required(f):
    @wraps(f)
    def d(*a,**kw):
        if not session.get('user_id'): return jsonify({'ok':False,'error':'未登录'}),401
        g.user_id=session['user_id'];g.user_role=session.get('user_role','');g.user_name=session.get('user_name','')
        return f(*a,**kw)
    return d

def check_alerts(eid):
    conn=get_db()
    ev=conn.execute('SELECT * FROM evidence WHERE id=?',[eid]).fetchone()
    if not ev: conn.close(); return []
    rs=conn.execute('SELECT * FROM alert_rules WHERE is_active=1 AND category_id=?',[ev['category_id']]).fetchall()
    res=[]
    for r in rs:
        req=json.loads(r['required_items'])
        ats=conn.execute('SELECT * FROM attachments WHERE evidence_id=?',[eid]).fetchall()
        an=[a['original_name'] for a in ats]
        miss=[i for i in req if not any(i in (x or '') for x in an) and i not in (ev['description'] or '') and i not in (ev['solution'] or '')]
        if miss:
            m=f"{ev['title']}: 缺少 {', '.join(miss)}"
            conn.execute('INSERT INTO alerts (evidence_id,rule_id,alert_type,severity,title,message) VALUES (?,?,?,?,?,?)',(eid,r['id'],'missing','中',f'证据缺失: {ev["title"]}',m))
            res.append(m)
    conn.commit(); conn.close()
    return res
@app.route('/')
def index():
    return send_from_directory(TEMPLATE_DIR,'index.html',mimetype='text/html')

@app.route('/api/health')
def api_health():
    return jsonify({'ok':True,'time':datetime.now().isoformat()})

@app.route('/api/login',methods=['POST'])
def api_login():
    d=request.get_json() or {}
    u=d.get('username','').strip();p=d.get('password','').strip()
    if not u or not p: return jsonify({'ok':False,'error':'请输入用户名和密码'}),400
    conn=get_db()
    usr=conn.execute('SELECT * FROM users WHERE username=? AND is_active=1',[u]).fetchone()
    conn.close()
    if not usr: return jsonify({'ok':False,'error':'用户不存在'}),401
    if usr['password_hash']!=hashlib.sha256(p.encode()).hexdigest(): return jsonify({'ok':False,'error':'密码错误'}),401
    session['user_id']=usr['id'];session['user_role']=usr['role'];session['user_name']=usr['display_name']
    log_act(usr['id'],'登录','user',usr['id'])
    return jsonify({'ok':True,'user':{'id':usr['id'],'username':usr['username'],'display_name':usr['display_name'],'role':usr['role']}})

@app.route('/api/logout',methods=['POST'])
def api_logout():
    session.clear(); return jsonify({'ok':True})

@app.route('/api/me')
@login_required
def api_me():
    conn=get_db()
    usr=conn.execute('SELECT * FROM users WHERE id=?',[g.user_id]).fetchone()
    conn.close()
    if not usr: return jsonify({'ok':False,'error':'用户不存在'}),404
    return jsonify({'ok':True,'user':{'id':usr['id'],'username':usr['username'],'display_name':usr['display_name'],'role':usr['role'],'phone':usr['phone']}})

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    conn=get_db()
    t=conn.execute('SELECT COUNT(*) FROM evidence WHERE is_deleted=0').fetchone()[0]
    bs=rows_to_list(conn.execute('SELECT status,COUNT(*) as cnt FROM evidence WHERE is_deleted=0 GROUP BY status').fetchall())
    ac=conn.execute('SELECT COUNT(*) FROM alerts WHERE is_dismissed=0').fetchone()[0]
    pa=conn.execute("SELECT COUNT(*) FROM approval_records WHERE result='待审核'").fetchone()[0]
    rn=rows_to_list(conn.execute('SELECT l.*,u.display_name as user_name FROM activity_logs l LEFT JOIN users u ON l.user_id=u.id ORDER BY l.created_at DESC LIMIT 10').fetchall())
    al=rows_to_list(conn.execute('SELECT a.*,e.title as evidence_title FROM alerts a LEFT JOIN evidence e ON a.evidence_id=e.id WHERE a.is_dismissed=0 ORDER BY a.created_at DESC LIMIT 10').fetchall())
    bp=rows_to_list(conn.execute('SELECT p.name,COUNT(e.id) as cnt FROM evidence e JOIN projects p ON e.project_id=p.id WHERE e.is_deleted=0 GROUP BY p.id ORDER BY cnt DESC').fetchall())
    conn.close()
    return jsonify({'total':t,'by_status':bs,'alert_count':ac,'pending_approval':pa,'recent_activity':rn,'alerts':al,'by_project':bp})
@app.route('/api/evidence',methods=['GET'])
@login_required
def api_evidence_list():
    pid=request.args.get('project_id',type=int);cid=request.args.get('category_id',type=int)
    st=request.args.get('status','');sr=request.args.get('search','')
    p=request.args.get('page',1,type=int);ps=request.args.get('page_size',20,type=int)
    sb=request.args.get('sort_by','created_at');so=request.args.get('sort_order','DESC')
    conn=get_db()
    w='WHERE e.is_deleted=0';pr=[]
    if pid: w+=' AND e.project_id=?';pr.append(pid)
    if cid: w+=' AND e.category_id=?';pr.append(cid)
    if st: w+=' AND e.status=?';pr.append(st)
    if sr:
        l=f'%{sr}%'
        w+=' AND (e.evidence_no LIKE ? OR e.title LIKE ? OR e.description LIKE ? OR e.tags LIKE ? OR e.contract_no LIKE ?)'
        pr.extend([l]*5)
    t=conn.execute(f'SELECT COUNT(*) FROM evidence e {w}',pr).fetchone()[0]
    off=(p-1)*ps
    q=f'SELECT e.*,p.name as project_name,c.name as category_name,c.code as category_code,u.display_name as creator_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id LEFT JOIN users u ON e.created_by=u.id {w} ORDER BY e.{sb} {so} LIMIT ? OFFSET ?'
    rows=conn.execute(q,pr+[ps,off]).fetchall()
    conn.close()
    return jsonify({'total':t,'page':p,'page_size':ps,'data':rows_to_list(rows)})

@app.route('/api/evidence',methods=['POST'])
@login_required
def api_evidence_create():
    d=request.get_json() or {}
    for f in ['project_id','title','category_id','event_time']:
        if not d.get(f): return jsonify({'ok':False,'error':f'缺少必填字段: {f}'}),400
    conn=get_db()
    pid=int(d['project_id']);evno=gen_evidence_no(pid)
    tags=json.dumps(d.get('tags',[]),ensure_ascii=False)
    pa=json.dumps(d.get('related_parties',[]),ensure_ascii=False)
    cur=conn.execute('INSERT INTO evidence (evidence_no,project_id,title,category_id,tags,event_time,description,solution,quantity,unit_price,total_amount,contract_no,related_parties,location,status,created_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (evno,pid,d['title'],int(d['category_id']),tags,d['event_time'],d.get('description',''),d.get('solution',''),float(d.get('quantity',0)),float(d.get('unit_price',0)),float(d.get('total_amount',0)),d.get('contract_no',''),pa,d.get('location',''),d.get('status','待提交'),g.user_id))
    conn.commit();eid=cur.lastrowid
    check_alerts(eid)
    row=conn.execute('SELECT * FROM evidence WHERE id=?',[eid]).fetchone()
    conn.close()
    log_act(g.user_id,'新增证据','evidence',eid,evno)
    return jsonify({'ok':True,'data':row_to_dict(row)}),201

@app.route('/api/evidence/<int:eid>',methods=['GET'])
@login_required
def api_evidence_detail(eid):
    conn=get_db()
    row=conn.execute('SELECT e.*,p.name as project_name,c.name as category_name,c.code as category_code,u.display_name as creator_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id LEFT JOIN users u ON e.created_by=u.id WHERE e.id=?',[eid]).fetchone()
    if not row: conn.close(); return jsonify({'ok':False,'error':'记录不存在'}),404
    atts=rows_to_list(conn.execute('SELECT * FROM attachments WHERE evidence_id=?',[eid]).fetchall())
    apr=rows_to_list(conn.execute('SELECT ar.*,u.display_name as approver_name FROM approval_records ar LEFT JOIN users u ON ar.approver_id=u.id WHERE ar.evidence_id=? ORDER BY ar.created_at',[eid]).fetchall())
    als=rows_to_list(conn.execute('SELECT * FROM alerts WHERE evidence_id=? ORDER BY created_at DESC',[eid]).fetchall())
    conn.close()
    r=row_to_dict(row);r['attachments']=atts;r['approval_records']=apr;r['alerts']=als
    return jsonify(r)

@app.route('/api/evidence/<int:eid>',methods=['PUT'])
@login_required
def api_evidence_update(eid):
    d=request.get_json() or {}
    conn=get_db()
    ex=conn.execute('SELECT * FROM evidence WHERE id=?',[eid]).fetchone()
    if not ex: conn.close(); return jsonify({'ok':False,'error':'记录不存在'}),404
    up={}
    for f in ['title','description','solution','event_time','contract_no','location','status']:
        if f in d: up[f]=d[f]
    for f in ['quantity','unit_price','total_amount']:
        if f in d: up[f]=float(d[f])
    if 'category_id' in d: up['category_id']=int(d['category_id'])
    if 'tags' in d: up['tags']=json.dumps(d['tags'],ensure_ascii=False)
    if 'related_parties' in d: up['related_parties']=json.dumps(d['related_parties'],ensure_ascii=False)
    if not up: conn.close(); return jsonify({'ok':False,'error':'没有需要更新的字段'}),400
    up['updated_at']=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cl=', '.join(f'{k}=?' for k in up)
    conn.execute(f'UPDATE evidence SET {cl} WHERE id=?',list(up.values())+[eid])
    conn.commit()
    check_alerts(eid)
    row=conn.execute('SELECT * FROM evidence WHERE id=?',[eid]).fetchone()
    conn.close()
    log_act(g.user_id,'更新证据','evidence',eid)
    return jsonify({'ok':True,'data':row_to_dict(row)})

@app.route('/api/evidence/<int:eid>',methods=['DELETE'])

@app.route('/api/evidence/batch-upload',methods=['POST'])
@login_required
def api_batch_upload():
    pid=request.form.get('project_id',type=int)
    cid=request.form.get('category_id',type=int)
    if not pid: return jsonify({"ok":False,"error":"请选择项目"}),400
    files=request.files.getlist('files')
    if not files: return jsonify({"ok":False,"error":"没有上传文件"}),400
    conn=get_db()
    results=[]
    for f in files:
        if not f.filename: continue
        import uuid
        ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
        sn=f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        dd=datetime.now().strftime('%Y%m')
        sd=os.path.join(UPLOAD_DIR,dd);os.makedirs(sd,exist_ok=True)
        fp=os.path.join(sd,sn);f.save(fp)
        sz=os.path.getsize(fp)
        title=os.path.splitext(f.filename)[0][:100]
        evno=gen_evidence_no(pid)
        cur=conn.execute("INSERT INTO evidence (evidence_no,project_id,title,category_id,event_time,status,created_by) VALUES (?,?,?,?,?,?,?)",
            (evno,pid,title,cid or 1,datetime.now().strftime('%Y-%m-%d'),"待提交",g.user_id))
        eid=cur.lastrowid
        conn.execute("INSERT INTO attachments (evidence_id,filename,original_name,file_type,file_size,file_path,uploaded_by) VALUES (?,?,?,?,?,?,?)",
            (eid,sn,f.filename,ext,sz,fp,g.user_id))
        results.append({"eid":eid,"evidence_no":evno,"title":title,"filename":f.filename,"file_size":sz})
    conn.commit();conn.close()
    log_act(g.user_id,"批量上传",detail=f"上传{len(results)}个文件")
    return jsonify({"ok":True,"results":results}),201

@login_required
def api_evidence_delete(eid):
    conn=get_db(); conn.execute('UPDATE evidence SET is_deleted=1 WHERE id=?',[eid]); conn.commit(); conn.close()
    log_act(g.user_id,'删除证据','evidence',eid)
    return jsonify({'ok':True,'deleted':eid})
ALLOWED_EXTENSIONS={'pdf','png','jpg','jpeg','gif','bmp','dwg','doc','docx','xls','xlsx','zip','rar'}
@app.route('/api/evidence/<int:eid>/attachments',methods=['POST'])
@login_required
def api_upload_attachment(eid):
    if 'file' not in request.files: return jsonify({'ok':False,'error':'没有上传文件'}),400
    file=request.files['file']
    if not file.filename: return jsonify({'ok':False,'error':'文件名为空'}),400
    ext=file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS: return jsonify({'ok':False,'error':'不支持的文件类型'}),400
    sn=f'{uuid.uuid4().hex}.{ext}' if ext else uuid.uuid4().hex
    dd=datetime.now().strftime('%Y%m')
    sd=os.path.join(UPLOAD_DIR,dd);os.makedirs(sd,exist_ok=True)
    fp=os.path.join(sd,sn);file.save(fp)
    sz=os.path.getsize(fp)
    conn=get_db()
    conn.execute('INSERT INTO attachments (evidence_id,filename,original_name,file_type,file_size,file_path,uploaded_by) VALUES (?,?,?,?,?,?,?)',
        (eid,sn,file.filename,ext,sz,fp,g.user_id))
    conn.commit()
    aid=conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    check_alerts(eid)
    log_act(g.user_id,'上传附件','attachment',aid,file.filename)
    return jsonify({'ok':True,'attachment':{'id':aid,'original_name':file.filename,'file_size':sz}})

@app.route('/api/attachments/<int:aid>/download')
@login_required
def api_download_attachment(aid):
    conn=get_db();att=conn.execute('SELECT * FROM attachments WHERE id=?',[aid]).fetchone();conn.close()
    if not att: return jsonify({'ok':False,'error':'附件不存在'}),404
    return send_file(att['file_path'],as_attachment=True,download_name=att['original_name'])

@app.route('/api/attachments/<int:aid>',methods=['DELETE'])
@login_required
def api_delete_attachment(aid):
    conn=get_db();att=conn.execute('SELECT * FROM attachments WHERE id=?',[aid]).fetchone()
    if not att: conn.close(); return jsonify({'ok':False,'error':'附件不存在'}),404
    if os.path.exists(att['file_path']): os.remove(att['file_path'])
    conn.execute('DELETE FROM attachments WHERE id=?',[aid]); conn.commit(); conn.close()
    log_act(g.user_id,'删除附件','attachment',aid)
    return jsonify({'ok':True,'deleted':aid})

@app.route('/api/approvals/pending')
@login_required
def api_pending_approvals():
    conn=get_db()
    rows=conn.execute("SELECT ar.*,e.evidence_no,e.title as evidence_title,e.status as evidence_status,p.name as project_name,u.display_name as creator_name FROM approval_records ar JOIN evidence e ON ar.evidence_id=e.id LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN users u ON e.created_by=u.id WHERE ar.result='待审核' ORDER BY ar.created_at DESC").fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/evidence/<int:eid>/submit-approval',methods=['POST'])
@login_required
def api_submit_approval(eid):
    conn=get_db()
    ev=conn.execute('SELECT * FROM evidence WHERE id=?',[eid]).fetchone()
    if not ev: conn.close(); return jsonify({'ok':False,'error':'证据不存在'}),404
    conn.execute("UPDATE evidence SET status=?,updated_at=datetime('now','localtime') WHERE id=?",('待审核',eid))
    conn.execute('INSERT INTO approval_records (evidence_id,approval_level,result) VALUES (?,?,?)',(eid,'初审','待审核'))
    conn.commit(); conn.close()
    log_act(g.user_id,'提审','evidence',eid)
    return jsonify({'ok':True})

@app.route('/api/approvals/<int:aid>/review',methods=['POST'])
@login_required
def api_review_approval(aid):
    d=request.get_json() or {};r=d.get('result','');c=d.get('comment','')
    if r not in ('通过','退回'): return jsonify({'ok':False,'error':'审核结果必须是“通过”或“退回”'}),400
    conn=get_db()
    ar=conn.execute('SELECT * FROM approval_records WHERE id=?',[aid]).fetchone()
    if not ar: conn.close(); return jsonify({'ok':False,'error':'审核记录不存在'}),404
    conn.execute('UPDATE approval_records SET result=?,comment=?,approver_id=? WHERE id=?',(r,c,g.user_id,aid))
    eid=ar['evidence_id']
    if r=='通过':
        if ar['approval_level']=='初审':
            conn.execute('INSERT INTO approval_records (evidence_id,approval_level,result) VALUES (?,?,?)',(eid,'终审','待审核'))
            conn.execute("UPDATE evidence SET status=?,updated_at=datetime('now','localtime') WHERE id=?",('待审核',eid))
        else:
            conn.execute("UPDATE evidence SET status=?,updated_at=datetime('now','localtime') WHERE id=?",('已审核',eid))
    else:
        conn.execute("UPDATE evidence SET status=?,updated_at=datetime('now','localtime') WHERE id=?",('退回',eid))
    conn.commit(); conn.close()
    log_act(g.user_id,f'{ar["approval_level"]}{r}','evidence',eid)
    return jsonify({'ok':True})

@app.route('/api/alerts')
@login_required
def api_alerts():
    dis=request.args.get('dismissed','0')
    conn=get_db()
    wh='WHERE a.is_dismissed=?' if dis in ('0','1') else ''
    pr=[int(dis)] if dis in ('0','1') else []
    rows=conn.execute(f'SELECT a.*,e.title as evidence_title,e.evidence_no FROM alerts a LEFT JOIN evidence e ON a.evidence_id=e.id {wh} ORDER BY a.created_at DESC LIMIT 50',pr).fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/alerts/<int:aid>/dismiss',methods=['POST'])
@login_required
def api_dismiss_alert(aid):
    conn=get_db(); conn.execute('UPDATE alerts SET is_dismissed=1 WHERE id=?',[aid]); conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/alerts/check',methods=['POST'])
@login_required
def api_check_alerts():
    conn=get_db();ids=[r['id'] for r in conn.execute('SELECT id FROM evidence WHERE is_deleted=0').fetchall()];conn.close()
    t=sum(len(check_alerts(i)) for i in ids)
    return jsonify({'ok':True,'alerts_generated':t})
@app.route('/api/categories')
@login_required
def api_categories():
    pid=request.args.get('parent_id',type=int)
    conn=get_db()
    if pid is not None: rows=conn.execute('SELECT * FROM categories WHERE parent_id=? ORDER BY sort_order',[pid]).fetchall()
    else: rows=conn.execute('SELECT c.*,(SELECT COUNT(*) FROM categories WHERE parent_id=c.id) as child_count FROM categories c ORDER BY c.sort_order').fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/projects')
@login_required
def api_projects():
    conn=get_db()
    rows=conn.execute("SELECT p.*,COUNT(e.id) as evidence_count,SUM(CASE WHEN e.status='已审核' THEN 1 ELSE 0 END) as approved_count FROM projects p LEFT JOIN evidence e ON p.id=e.project_id AND e.is_deleted=0 GROUP BY p.id ORDER BY p.name").fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/projects',methods=['POST'])
@login_required
def api_project_create():
    d=request.get_json() or {}
    if not d.get('name'): return jsonify({'ok':False,'error':'项目名称不能为空'}),400
    conn=get_db()
    if conn.execute('SELECT id FROM projects WHERE name=?',[d['name']]).fetchone(): conn.close(); return jsonify({'ok':False,'error':'项目名称已存在'}),400
    conn.execute('INSERT INTO projects (name,full_name,code,contract_amount,start_date,end_date,owner,notes) VALUES (?,?,?,?,?,?,?,?)',
        (d['name'],d.get('full_name',''),d.get('code',''),float(d.get('contract_amount',0)),d.get('start_date',''),d.get('end_date',''),d.get('owner',''),d.get('notes','')))
    conn.commit();pid=conn.execute('SELECT last_insert_rowid()').fetchone()[0];conn.close()
    return jsonify({'ok':True,'project':{'id':pid,'name':d['name']}}),201

@app.route('/api/projects/<int:pid>',methods=['PUT'])
@login_required
def api_project_update(pid):
    d=request.get_json() or {};conn=get_db();up={}
    for f in ['name','full_name','code','contract_amount','start_date','end_date','owner','status','notes']:
        if f in d: up[f]=d[f] if f!='contract_amount' else float(d[f])
    if not up: conn.close(); return jsonify({'ok':False,'error':'没有更新字段'}),400
    cl=', '.join(f'{k}=?' for k in up)
    conn.execute(f'UPDATE projects SET {cl} WHERE id=?',list(up.values())+[pid])
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/projects/<int:pid>',methods=['DELETE'])
@login_required
def api_project_delete(pid):
    conn=get_db()
    cnt=conn.execute('SELECT COUNT(*) FROM evidence WHERE project_id=?',[pid]).fetchone()[0]
    if cnt>0: conn.close(); return jsonify({'ok':False,'error':f'该项目下有{cnt}条证据，不能删除'}),400
    conn.execute('DELETE FROM projects WHERE id=?',[pid]); conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/users')
@login_required
def api_users():
    conn=get_db()
    rows=conn.execute('SELECT id,username,display_name,role,phone,is_active,created_at FROM users ORDER BY id').fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/users',methods=['POST'])
@login_required
def api_user_create():
    d=request.get_json() or {}
    if not d.get('username') or not d.get('password'): return jsonify({'ok':False,'error':'用户名和密码不能为空'}),400
    conn=get_db()
    if conn.execute('SELECT id FROM users WHERE username=?',[d['username']]).fetchone(): conn.close(); return jsonify({'ok':False,'error':'用户名已存在'}),400
    pwd=hashlib.sha256(d['password'].encode()).hexdigest()
    conn.execute('INSERT INTO users (username,password_hash,display_name,role,phone) VALUES (?,?,?,?,?)',
        (d['username'],pwd,d.get('display_name',d['username']),d.get('role','施工员'),d.get('phone','')))
    conn.commit();uid=conn.execute('SELECT last_insert_rowid()').fetchone()[0];conn.close()
    return jsonify({'ok':True,'user':{'id':uid,'username':d['username']}}),201

@app.route('/api/users/<int:uid>',methods=['PUT'])
@login_required
def api_user_update(uid):
    d=request.get_json() or {};conn=get_db();up={}
    for f in ['display_name','role','phone','is_active']:
        if f in d: up[f]=d[f]
    if 'password' in d and d['password']: up['password_hash']=hashlib.sha256(d['password'].encode()).hexdigest()
    if not up: conn.close(); return jsonify({'ok':False,'error':'没有更新字段'}),400
    cl=', '.join(f'{k}=?' for k in up)
    conn.execute(f'UPDATE users SET {cl} WHERE id=?',list(up.values())+[uid])
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/users/<int:uid>',methods=['DELETE'])
@login_required
def api_user_delete(uid):
    if uid==g.user_id: return jsonify({'ok':False,'error':'不能删除自己'}),400
    conn=get_db(); conn.execute('UPDATE users SET is_active=0 WHERE id=?',[uid]); conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/alert-rules')
@login_required
def api_alert_rules():
    conn=get_db()
    rows=conn.execute('SELECT ar.*,c.name as category_name FROM alert_rules ar LEFT JOIN categories c ON ar.category_id=c.id ORDER BY ar.id').fetchall()
    conn.close()
    return jsonify({'data':rows_to_list(rows)})

@app.route('/api/alert-rules',methods=['POST'])
@login_required
def api_alert_rule_create():
    d=request.get_json() or {}
    if not d.get('name'): return jsonify({'ok':False,'error':'规则名称不能为空'}),400
    conn=get_db()
    conn.execute('INSERT INTO alert_rules (category_id,name,required_items,description) VALUES (?,?,?,?)',
        (d.get('category_id'),d['name'],json.dumps(d.get('required_items',[]),ensure_ascii=False),d.get('description','')))
    conn.commit();rid=conn.execute('SELECT last_insert_rowid()').fetchone()[0];conn.close()
    return jsonify({'ok':True,'rule':{'id':rid}}),201

@app.route('/api/alert-rules/<int:rid>',methods=['PUT'])
@login_required
def api_alert_rule_update(rid):
    d=request.get_json() or {};conn=get_db();up={}
    for f in ['name','description','is_active']:
        if f in d: up[f]=d[f]
    if 'required_items' in d: up['required_items']=json.dumps(d['required_items'],ensure_ascii=False)
    if 'category_id' in d: up['category_id']=d['category_id']
    if not up: conn.close(); return jsonify({'ok':False,'error':'没有更新字段'}),400
    cl=', '.join(f'{k}=?' for k in up)
    conn.execute(f'UPDATE alert_rules SET {cl} WHERE id=?',list(up.values())+[rid])
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/alert-rules/<int:rid>',methods=['DELETE'])
@login_required
def api_alert_rule_delete(rid):
    conn=get_db(); conn.execute('DELETE FROM alert_rules WHERE id=?',[rid]); conn.commit(); conn.close()
    return jsonify({'ok':True})
@app.route('/api/export/evidence')
@login_required
def api_export_evidence():
    pid=request.args.get('project_id',type=int);st=request.args.get('status','')
    conn=get_db()
    w='WHERE e.is_deleted=0';pr=[]
    if pid: w+=' AND e.project_id=?';pr.append(pid)
    if st: w+=' AND e.status=?';pr.append(st)
    rows=conn.execute(f'SELECT e.*,p.name as project_name,c.name as category_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id {w} ORDER BY e.evidence_no',pr).fetchall()
    conn.close()
    import io; output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['证据编号','项目名称','标题','分类','标签','事件时间','描述','处理方案','工程量','单价','总金额','合同编号','涉及方','状态','创建时间'])
    for r in rows:
        writer.writerow([r['evidence_no'],r['project_name'],r['title'],r['category_name'],r['tags'],r['event_time'],r['description'],r['solution'],r['quantity'],r['unit_price'],r['total_amount'],r['contract_no'],r['related_parties'],r['status'],r['created_at']])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),mimetype='text/csv; charset=utf-8-sig',as_attachment=True,download_name=f'证据清单_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/api/export/settlement')
@login_required
def api_export_settlement():
    pid=request.args.get('project_id',type=int)
    if not pid: return jsonify({'ok':False,'error':'请选择项目'}),400
    conn=get_db()
    rows=conn.execute("SELECT e.*,p.name as project_name,c.name as category_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id WHERE e.project_id=? AND e.is_deleted=0 AND e.status='已审核' ORDER BY e.evidence_no",[pid]).fetchall()
    conn.close()
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['证据编号','项目名称','标题','分类','事件时间','描述','处理方案','工程量','单价','总金额','状态'])
    for r in rows:
        writer.writerow([r['evidence_no'],r['project_name'],r['title'],r['category_name'],r['event_time'],r['description'],r['solution'],r['quantity'],r['unit_price'],r['total_amount'],r['status']])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),mimetype='text/csv; charset=utf-8-sig',as_attachment=True,download_name=f'结算包_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/api/llm/extract',methods=['POST'])
@login_required
def api_llm_extract():
    d=request.get_json() or {};t=d.get('text','')
    if not t: return jsonify({'ok':False,'error':'请输入文本'}),400
    tm=re.search(r'(\d{4}[-/\u5e74]\d{1,2}[-/\u6708]\d{1,2}[\u65e5]?)',t)
    am=re.search(r'(\d+[.,]?\d*)\s*\u4e07?\u5143',t)
    qm=re.search(r'(\d+[.,]?\d*)\s*(m[23]?|\u4e2a|\u5904|\u9879|\u6761|\u4efd)',t)
    ls=[l.strip() for l in t.split('\n') if l.strip()]
    return jsonify({'ok':True,'extracted':{
        'title': ls[0][:50] if ls else '',
        'event_time': tm.group(1) if tm else '',
        'total_amount': float(am.group(1).replace(',','')) if am else 0,
        'quantity': float(qm.group(1).replace(',','')) if qm else 0,
        'description': t[:500],
    }})



@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)

@app.route('/favicon.svg')
def serve_favicon():
    return send_from_directory(os.path.join(BASE_DIR, "assets"), "favicon.svg")

@app.route('/api/project-home')
@login_required
def api_project_home():
    conn=get_db()
    total=conn.execute("SELECT COUNT(*) FROM evidence WHERE is_deleted=0").fetchone()[0]
    by_project=rows_to_list(conn.execute("SELECT p.id,p.name,COUNT(e.id) as cnt,SUM(CASE WHEN e.status='已审核' THEN 1 ELSE 0 END) as approved FROM projects p LEFT JOIN evidence e ON p.id=e.project_id AND e.is_deleted=0 GROUP BY p.id ORDER BY p.name").fetchall())
    recent=rows_to_list(conn.execute("SELECT e.id,e.title,e.evidence_no,e.status,e.created_at,p.name as project_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id WHERE e.is_deleted=0 ORDER BY e.created_at DESC LIMIT 10").fetchall())
    alerts=rows_to_list(conn.execute("SELECT a.*,e.title as evidence_title FROM alerts a LEFT JOIN evidence e ON a.evidence_id=e.id WHERE a.is_dismissed=0 ORDER BY a.created_at DESC LIMIT 5").fetchall())
    conn.close()
    return jsonify({"total":total,"by_project":by_project,"recent":recent,"alerts":alerts})

@app.route('/api/settlement-packages')
@login_required
def api_settlement_packages():
    pid=request.args.get("project_id",type=int)
    conn=get_db();wh="";pr=[]
    if pid: wh=" WHERE sp.project_id=?";pr.append(pid)
    rows=rows_to_list(conn.execute(f"SELECT sp.*,p.name as project_name,u.display_name as creator_name,(SELECT COUNT(*) FROM settlement_package_items WHERE package_id=sp.id) as item_count FROM settlement_packages sp LEFT JOIN projects p ON sp.project_id=p.id LEFT JOIN users u ON sp.created_by=u.id{wh} ORDER BY sp.created_at DESC",pr).fetchall())
    conn.close()
    return jsonify({"data":rows})

@app.route('/api/settlement-packages',methods=["POST"])
@login_required
def api_settlement_package_create():
    d=request.get_json() or {}
    if not d.get("name") or not d.get("project_id"): return jsonify({"ok":False,"error":"名称和项目不能为空"}),400
    conn=get_db()
    conn.execute("INSERT INTO settlement_packages (name,project_id,description,status,created_by) VALUES (?,?,?,?,?)",(d["name"],d["project_id"],d.get("description",""),d.get("status","draft"),g.user_id))
    conn.commit();pid=conn.execute("SELECT last_insert_rowid()").fetchone()[0];conn.close()
    return jsonify({"ok":True,"package":{"id":pid}}),201

@app.route('/api/settlement-packages/<int:pid>',methods=["PUT"])
@login_required
def api_settlement_package_update(pid):
    d=request.get_json() or {};conn=get_db();up={}
    for f in ["name","description","status"]:
        if f in d: up[f]=d[f]
    if not up: conn.close(); return jsonify({"ok":False,"error":"没有更新字段"}),400
    up["updated_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cl=", ".join(f"{k}=?" for k in up)
    conn.execute(f"UPDATE settlement_packages SET {cl} WHERE id=?",list(up.values())+[pid])
    conn.commit();conn.close()
    return jsonify({"ok":True})

@app.route('/api/settlement-packages/<int:pid>',methods=["DELETE"])
@login_required
def api_settlement_package_delete(pid):
    conn=get_db();conn.execute("DELETE FROM settlement_packages WHERE id=?",[pid]);conn.commit();conn.close()
    return jsonify({"ok":True})

@app.route('/api/settlement-packages/<int:pid>/items')
@login_required
def api_settlement_package_items(pid):
    conn=get_db()
    rows=rows_to_list(conn.execute("SELECT spi.*,e.evidence_no,e.title as evidence_title,e.status as evidence_status,e.quantity,e.unit_price,e.total_amount,c.name as category_name FROM settlement_package_items spi JOIN evidence e ON spi.evidence_id=e.id LEFT JOIN categories c ON e.category_id=c.id WHERE spi.package_id=? ORDER BY spi.sort_order,spi.id",[pid]).fetchall())
    conn.close()
    return jsonify({"data":rows})

@app.route('/api/settlement-packages/<int:pid>/items',methods=["POST"])
@login_required
def api_settlement_package_add_item(pid):
    d=request.get_json() or {}
    if not d.get("evidence_id"): return jsonify({"ok":False,"error":"请选择证据"}),400
    conn=get_db()
    conn.execute("INSERT INTO settlement_package_items (package_id,evidence_id,sort_order,notes) VALUES (?,?,?,?)",(pid,d["evidence_id"],d.get("sort_order",0),d.get("notes","")))
    conn.commit();iid=conn.execute("SELECT last_insert_rowid()").fetchone()[0];conn.close()
    return jsonify({"ok":True,"item":{"id":iid}}),201

@app.route('/api/settlement-packages/<int:pid>/items/<int:iid>',methods=["DELETE"])
@login_required
def api_settlement_package_remove_item(pid,iid):
    conn=get_db();conn.execute("DELETE FROM settlement_package_items WHERE id=? AND package_id=?",[iid,pid]);conn.commit();conn.close()
    return jsonify({"ok":True})

@app.route('/api/settlement-packages/<int:pid>/export')
@login_required
def api_settlement_package_export(pid):
    conn=get_db()
    pkg=conn.execute("SELECT * FROM settlement_packages WHERE id=?",[pid]).fetchone()
    if not pkg: conn.close(); return jsonify({"ok":False,"error":"组卷不存在"}),404
    rows=conn.execute("SELECT e.*,p.name as project_name,c.name as category_name,spi.sort_order,spi.notes FROM settlement_package_items spi JOIN evidence e ON spi.evidence_id=e.id LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id WHERE spi.package_id=? ORDER BY spi.sort_order,spi.id",[pid]).fetchall()
    conn.close()
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(["序号","证据编号","项目","标题","分类","事件时间","描述","处理方案","工程量","单价","总金额","状态","备注"])
    for i,r in enumerate(rows,1):
        writer.writerow([i,r["evidence_no"],r["project_name"],r["title"],r["category_name"],r["event_time"],r["description"],r["solution"],r["quantity"],r["unit_price"],r["total_amount"],r["status"],r["notes"]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),mimetype="text/csv; charset=utf-8-sig",as_attachment=True,download_name=f"结算组卷_{pkg['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

@app.route('/api/search')
@login_required
def api_global_search():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"evidence":[],"projects":[]})
    like=f"%{q}%"
    conn=get_db()
    ev=rows_to_list(conn.execute("SELECT e.id,e.evidence_no,e.title,e.status,e.event_time,p.name as project_name,c.name as category_name FROM evidence e LEFT JOIN projects p ON e.project_id=p.id LEFT JOIN categories c ON e.category_id=c.id WHERE e.is_deleted=0 AND (e.title LIKE ? OR e.evidence_no LIKE ? OR e.description LIKE ? OR e.contract_no LIKE ?) LIMIT 20",[like,like,like,like]).fetchall())
    pr=rows_to_list(conn.execute("SELECT id,name,full_name,status FROM projects WHERE name LIKE ? OR full_name LIKE ? OR code LIKE ? LIMIT 10",[like,like,like]).fetchall())
    conn.close()
    return jsonify({"evidence":ev,"projects":pr})

if __name__=='__main__':
    init_database()
    print('** 证据链管理系统 v2.0')
    print(f'** 数据库: {DB_PATH}')
    print(f'** 上传目录: {UPLOAD_DIR}')
    print('** 启动服务器: http://localhost:5000')
    print('   KEY 默认账号: admin / admin123')
    app.run(host='0.0.0.0',port=5001,debug=True)