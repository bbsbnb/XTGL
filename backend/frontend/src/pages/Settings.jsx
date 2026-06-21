import React, { useState, useEffect } from "react";
import { Tabs, Card, Table, Button, Modal, Form, Input, InputNumber, Select, message, Tag, Space, Typography } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { getProjects, createProject, updateProject, deleteProject, getUsers, createUser, updateUser, deleteUser, getAlertRules, createAlertRule, updateAlertRule, deleteAlertRule, getCategories } from "../api";

function ProjectSettings() {
  const [data, setData] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();
  const load = () => getProjects().then(r => setData(r.data.data));
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    const v = form.getFieldsValue();
    try {
      if (editing) { await updateProject(editing.id, v); message.success("已更新"); }
      else { await createProject(v); message.success("已创建"); }
      setModalOpen(false); load();
    } catch (e) { message.error(e.response?.data?.error || "操作失败"); }
  };

  const handleDelete = (id) => {
    Modal.confirm({ title: "确定删除?", onOk: async () => { await deleteProject(id); message.success("已删除"); load(); } });
  };

  const columns = [
    { title: "名称", dataIndex: "name" }, { title: "全称", dataIndex: "full_name" },
    { title: "合同额", dataIndex: "contract_amount", render: (v) => v ? v + "" : "-" },
    { title: "状态", dataIndex: "status", width: 80, render: (s) => <Tag>{s}</Tag> },
    { title: "证据数", dataIndex: "evidence_count", width: 80 },
    {
      title: "操作", width: 120,
      render: (_, r) => (<Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
      </Space>)
    },
  ];

  return (<div>
    <Space style={{ marginBottom: 16 }}>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>新建项目</Button>
    </Space>
    <Table columns={columns} dataSource={data} rowKey="id" size="small" pagination={false} />
    <Modal title={editing ? "编辑项目" : "新建项目"} open={modalOpen} onOk={handleSave} onCancel={() => setModalOpen(false)}>
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="full_name" label="全称"><Input /></Form.Item>
        <Form.Item name="contract_amount" label="合同金额"><InputNumber style={{ width: "100%" }} /></Form.Item>
        <Form.Item name="status" label="状态"><Select><Select.Option value="进行中">进行中</Select.Option><Select.Option value="已结算">已结算</Select.Option></Select></Form.Item>
      </Form>
    </Modal>
  </div>);
}

function UserSettings() {
  const [data, setData] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();
  const load = () => getUsers().then(r => setData(r.data.data));
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    const v = form.getFieldsValue();
    try {
      if (editing) { await updateUser(editing.id, v); message.success("已更新"); }
      else { await createUser(v); message.success("已创建"); }
      setModalOpen(false); load();
    } catch (e) { message.error(e.response?.data?.error || "操作失败"); }
  };

  const handleDelete = (id) => {
    Modal.confirm({ title: "确定删除用户?", onOk: async () => { await deleteUser(id); message.success("已删除"); load(); } });
  };

  const columns = [
    { title: "用户名", dataIndex: "username" }, { title: "显示名", dataIndex: "display_name" },
    { title: "角色", dataIndex: "role", width: 100, render: (s) => <Tag>{s}</Tag> },
    { title: "电话", dataIndex: "phone", width: 130 },
    { title: "状态", dataIndex: "is_active", width: 80, render: (v) => <Tag color={v ? "green" : "red"}>{v ? "活跃" : "禁用"}</Tag> },
    {
      title: "操作", width: 120,
      render: (_, r) => (<Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
      </Space>)
    },
  ];

  return (<div>
    <Space style={{ marginBottom: 16 }}>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>新建用户</Button>
    </Space>
    <Table columns={columns} dataSource={data} rowKey="id" size="small" pagination={false} />
    <Modal title={editing ? "编辑用户" : "新建用户"} open={modalOpen} onOk={handleSave} onCancel={() => setModalOpen(false)}>
      <Form form={form} layout="vertical">
        {!editing && <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>}
        {!editing && <Form.Item name="password" label="密码" rules={[{ required: true }]}><Input.Password /></Form.Item>}
        <Form.Item name="display_name" label="显示名"><Input /></Form.Item>
        <Form.Item name="role" label="角色"><Select>
          <Select.Option value="施工员">施工员</Select.Option>
          <Select.Option value="资料员">资料员</Select.Option>
          <Select.Option value="预算员">预算员</Select.Option>
          <Select.Option value="项目经理">项目经理</Select.Option>
        </Select></Form.Item>
        <Form.Item name="phone" label="电话"><Input /></Form.Item>
      </Form>
    </Modal>
  </div>);
}

function AlertRuleSettings() {
  const [data, setData] = useState([]);
  const [categories, setCategories] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();
  const load = () => { getAlertRules().then(r => setData(r.data.data)); getCategories().then(r => setCategories(r.data.data.filter(c => c.level === 2))); };
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    const v = form.getFieldsValue();
    try {
      if (editing) { await updateAlertRule(editing.id, v); message.success("已更新"); }
      else { await createAlertRule(v); message.success("已创建"); }
      setModalOpen(false); load();
    } catch (e) { message.error(e.response?.data?.error || "操作失败"); }
  };

  const handleDelete = (id) => {
    Modal.confirm({ title: "确定删除规则?", onOk: async () => { await deleteAlertRule(id); message.success("已删除"); load(); } });
  };

  const columns = [
    { title: "规则名称", dataIndex: "name" },
    { title: "关联分类", dataIndex: "category_name" },
    { title: "必填项", dataIndex: "required_items", render: (v) => { try { return JSON.parse(v).join(", "); } catch { return v; } } },
    { title: "启用", dataIndex: "is_active", width: 80, render: (v) => <Tag color={v ? "green" : "red"}>{v ? "启用" : "停用"}</Tag> },
    {
      title: "操作", width: 120,
      render: (_, r) => (<Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); try { r.required_items = JSON.parse(r.required_items); } catch {} form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
      </Space>)
    },
  ];

  return (<div>
    <Space style={{ marginBottom: 16 }}>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>新建规则</Button>
    </Space>
    <Table columns={columns} dataSource={data} rowKey="id" size="small" pagination={false} />
    <Modal title={editing ? "编辑规则" : "新建规则"} open={modalOpen} onOk={handleSave} onCancel={() => setModalOpen(false)}>
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="规则名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="category_id" label="关联分类"><Select allowClear placeholder="选择分类">
          {categories.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
        </Select></Form.Item>
        <Form.Item name="required_items" label="必填项（逗号分隔）" rules={[{ required: true }]}>
          <Input placeholder="例如: 联系单, 照片佐证, 工程量, 单价" />
        </Form.Item>
        <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
      </Form>
    </Modal>
  </div>);
}

export default function Settings() {
  return (
    <div>
      <Typography.Title level={4}>系统设置</Typography.Title>
      <Card size="small">
        <Tabs items={[
          { key: "projects", label: "项目管理", children: <ProjectSettings /> },
          { key: "users", label: "用户管理", children: <UserSettings /> },
          { key: "rules", label: "预警规则", children: <AlertRuleSettings /> },
        ]} />
      </Card>
    </div>
  );
}
