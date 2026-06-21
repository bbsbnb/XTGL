import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Table, Button, Input, Select, Tag, Space, Typography, Card, Modal, Upload, message } from "antd";
import { PlusOutlined, UploadOutlined, InboxOutlined, SearchOutlined } from "@ant-design/icons";
import { getEvidence, getProjects, getCategories, batchUploadEvidence } from "../api";

const { Dragger } = Upload;

export default function EvidenceList() {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [projects, setProjects] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ project_id: undefined, category_id: undefined, status: "", search: "" });
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadProject, setUploadProject] = useState(null);
  const [uploadCategory, setUploadCategory] = useState(null);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => { getProjects().then(r => setProjects(r.data.data)); }, []);
  useEffect(() => { getCategories().then(r => setCategories(r.data.data.filter(c => c.level === 2))); }, []);

  const fetchData = () => {
    setLoading(true);
    getEvidence({ ...filters, page, page_size: 20 }).then(r => {
      setData(r.data.data);
      setTotal(r.data.total);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page, filters]);

  const handleBatchUpload = async () => {
    if (!uploadProject) { message.warning("请选择项目"); return; }
    if (uploadFiles.length === 0) { message.warning("请选择文件"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("project_id", uploadProject);
      if (uploadCategory) fd.append("category_id", uploadCategory);
      uploadFiles.forEach(f => fd.append("files", f.originFileObj || f));
      const res = await batchUploadEvidence(fd);
      message.success("上传完成: " + res.data.results.length + " 个文件");
      setUploadOpen(false);
      setUploadFiles([]);
      fetchData();
    } catch (e) {
      message.error(e.response?.data?.error || "上传失败");
    }
    setUploading(false);
  };

  const statusColors = { "待提交": "default", "待审核": "processing", "已审核": "success", "退回": "error", "已归档": "purple", "存疑": "warning" };

  const columns = [
    { title: "证据编号", dataIndex: "evidence_no", width: 180 },
    { title: "标题", dataIndex: "title", ellipsis: true },
    { title: "项目", dataIndex: "project_name", width: 160 },
    { title: "分类", dataIndex: "category_name", width: 120 },
    { title: "事件时间", dataIndex: "event_time", width: 110 },
    { title: "状态", dataIndex: "status", width: 100, render: (s) => <Tag color={statusColors[s]}>{s}</Tag> },
    {
      title: "操作", width: 120,
      render: (_, r) => <Button type="link" onClick={() => navigate("/evidence/" + r.id)}>查看</Button>
    },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}>证据管理</Typography.Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select allowClear placeholder="选择项目" style={{ width: 180 }} onChange={(v) => setFilters(f => ({ ...f, project_id: v }))}>
            {projects.map(p => <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>)}
          </Select>
          <Select allowClear placeholder="选择分类" style={{ width: 150 }} onChange={(v) => setFilters(f => ({ ...f, category_id: v }))}>
            {categories.filter(c => c.level === 2).map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
          </Select>
          <Select allowClear placeholder="选择状态" style={{ width: 120 }} onChange={(v) => setFilters(f => ({ ...f, status: v || "" }))}>
            {["待提交", "待审核", "已审核", "退回", "已归档", "存疑"].map(s =>
              <Select.Option key={s} value={s}>{s}</Select.Option>
            )}
          </Select>
          <Input.Search placeholder="搜索" style={{ width: 250 }} onSearch={(v) => setFilters(f => ({ ...f, search: v }))} />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/evidence/new")}>新增证据</Button>
          <Button icon={<UploadOutlined />} onClick={() => setUploadOpen(true)}>上传文档</Button>
        </Space>
      </Card>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} size="small"
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }} />

      <Modal title="批量上传文档" open={uploadOpen} onCancel={() => { setUploadOpen(false); setUploadFiles([]); }}
        onOk={handleBatchUpload} confirmLoading={uploading} okText="开始上传" width={600}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Space>
            <Select placeholder="选择项目" style={{ width: 240 }} value={uploadProject} onChange={setUploadProject}>
              {projects.map(p => <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>)}
            </Select>
            <Select placeholder="选择分类" style={{ width: 240 }} value={uploadCategory} onChange={setUploadCategory} allowClear>
              {categories.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Space>
          <Dragger multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.zip,.rar,.dwg"
            fileList={uploadFiles} onChange={({ fileList }) => setUploadFiles(fileList)}
            beforeUpload={(file) => { setUploadFiles(prev => [...prev, { ...file, uid: file.uid }]); return false; }}>
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">支持 PDF, Word, Excel, 图片, ZIP 等格式</p>
          </Dragger>
        </Space>
      </Modal>
    </div>
  );
}
