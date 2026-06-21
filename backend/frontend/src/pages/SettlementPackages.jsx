import React, { useState, useEffect } from "react";
import { Table, Button, Modal, Form, Input, Select, Space, Tag, Typography, Card, message, List } from "antd";
import { PlusOutlined, DeleteOutlined, DownloadOutlined, InboxOutlined } from "@ant-design/icons";
import { getSettlementPackages, createSettlementPackage, updateSettlementPackage, deleteSettlementPackage, getSettlementPackageItems, addSettlementPackageItem, removeSettlementPackageItem, exportSettlementPackage, getProjects, getEvidence } from "../api";

export default function SettlementPackages() {
  const [packages, setPackages] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [detailPkg, setDetailPkg] = useState(null);
  const [detailItems, setDetailItems] = useState([]);
  const [addEvidenceModal, setAddEvidenceModal] = useState(false);
  const [evidenceList, setEvidenceList] = useState([]);
  const [form] = Form.useForm();

  const load = () => {
    setLoading(true);
    getSettlementPackages().then((r) => setPackages(r.data.data)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); getProjects().then((r) => setProjects(r.data.data)); }, []);

  const handleSave = async () => {
    const v = form.getFieldsValue();
    try {
      if (editing) {
        await updateSettlementPackage(editing.id, v);
        message.success("已更新");
      } else {
        await createSettlementPackage(v);
        message.success("已创建");
      }
      setModalOpen(false);
      load();
    } catch (e) {
      message.error(e.response?.data?.error || "操作失败");
    }
  };

  const handleDelete = (id) => {
    Modal.confirm({ title: "确认删除组卷?", onOk: async () => { await deleteSettlementPackage(id); message.success("已删除"); load(); } });
  };

  const showDetail = async (pkg) => {
    setDetailPkg(pkg);
    const res = await getSettlementPackageItems(pkg.id);
    setDetailItems(res.data.data);
  };

  const handleRemoveItem = async (iid) => {
    await removeSettlementPackageItem(detailPkg.id, iid);
    const res = await getSettlementPackageItems(detailPkg.id);
    setDetailItems(res.data.data);
    message.success("已移除");
  };

  const handleExport = async (pid, name) => {
    try {
      const res = await exportSettlementPackage(pid);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "结算组卷_" + name + "_" + new Date().toISOString().slice(0, 10) + ".csv";
      a.click();
      message.success("已导出");
    } catch {
      message.error("导出失败");
    }
  };

  const openAddEvidence = async () => {
    const res = await getEvidence({ project_id: detailPkg.project_id, page_size: 200 });
    setEvidenceList(res.data.data);
    setAddEvidenceModal(true);
  };

  const handleAddEvidence = async (evidenceId) => {
    try {
      await addSettlementPackageItem(detailPkg.id, { evidence_id: evidenceId });
      message.success("已添加");
      const res = await getSettlementPackageItems(detailPkg.id);
      setDetailItems(res.data.data);
    } catch (e) {
      message.error(e.response?.data?.error || "添加失败");
    }
  };

  const columns = [
    { title: "名称", dataIndex: "name" },
    { title: "项目", dataIndex: "project_name", width: 150 },
    { title: "状态", dataIndex: "status", width: 100, render: (s) => <Tag color={s === "draft" ? "default" : "success"}>{s === "draft" ? "草稿" : "已完成"}</Tag> },
    { title: "证据数", dataIndex: "item_count", width: 80 },
    { title: "创建人", dataIndex: "creator_name", width: 100 },
    { title: "创建时间", dataIndex: "created_at", width: 170 },
    {
      title: "操作", width: 200,
      render: (_, r) => (
        <Space>
          <Button size="small" onClick={() => showDetail(r)}>管理证据</Button>
          <Button size="small" onClick={() => handleExport(r.id, r.name)} icon={<DownloadOutlined />} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>结算组卷</Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />}
          onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>新建组卷</Button>
      </Space>
      <Card size="small">
        <Table columns={columns} dataSource={packages} rowKey="id" loading={loading} size="small" pagination={false} />
      </Card>

      <Modal title={editing ? "编辑组卷" : "新建组卷"} open={modalOpen} onOk={handleSave} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="组卷名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="project_id" label="项目" rules={[{ required: true }]}>
            <Select placeholder="选择项目">
              {projects.map((p) => <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="status" label="状态">
            <Select><Select.Option value="draft">草稿</Select.Option><Select.Option value="completed">已完成</Select.Option></Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={"组卷: " + (detailPkg?.name || "")} open={!!detailPkg} onCancel={() => setDetailPkg(null)} width={700} footer={null}>
        <Space style={{ marginBottom: 16 }}>
          <Button size="small" onClick={openAddEvidence} icon={<PlusOutlined />}>添加证据</Button>
          <Button size="small" onClick={() => handleExport(detailPkg?.id, detailPkg?.name)} icon={<DownloadOutlined />}>导出CSV</Button>
          <Button size="small" onClick={async () => { await updateSettlementPackage(detailPkg?.id, { status: "completed" }); message.success("已标记完成"); }}>
            标记完成
          </Button>
        </Space>
        <Table dataSource={detailItems} rowKey="id" size="small" pagination={false}
          columns={[
            { title: "证据编号", dataIndex: "evidence_no", width: 150 },
            { title: "标题", dataIndex: "evidence_title", ellipsis: true },
            { title: "分类", dataIndex: "category_name", width: 100 },
            { title: "工程量", dataIndex: "quantity", width: 80 },
            { title: "金额", dataIndex: "total_amount", width: 100 },
            { title: "操作", width: 60, render: (_, r) => (
              <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleRemoveItem(r.id)} />
            )},
          ]}
        />
      </Modal>

      <Modal title="选择证据添加到组卷" open={addEvidenceModal} onCancel={() => setAddEvidenceModal(false)} width={600} footer={null}>
        <Table dataSource={evidenceList} rowKey="id" size="small" pagination={{ pageSize: 10 }}
          columns={[
            { title: "证据编号", dataIndex: "evidence_no", width: 150 },
            { title: "标题", dataIndex: "title", ellipsis: true },
            { title: "状态", dataIndex: "status", width: 80, render: (s) => <Tag>{s}</Tag> },
            { title: "操作", width: 80, render: (_, r) => (
              <Button size="small" type="primary" onClick={() => handleAddEvidence(r.id)}>添加</Button>
            )},
          ]}
        />
      </Modal>
    </div>
  );
}
