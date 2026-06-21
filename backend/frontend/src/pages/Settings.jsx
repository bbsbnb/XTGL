import React, { useState, useEffect } from "react";
import { Tabs, Card, Table, Button, Modal, Form, Input, InputNumber, Select, message, Tag, Space, Typography } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, KeyOutlined } from "@ant-design/icons";
import { getProjects, createProject, updateProject, deleteProject, getUsers, createUser, updateUser, deleteUser, getAlertRules, createAlertRule, updateAlertRule, deleteAlertRule, getCategories, getSettings, updateSettings } from "../api";

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

export default 
function LLMSettings() {
  const L = {
    desc: '配置 AI 接口，用于智能填充表单和自动推荐证据关联。',
    provider: '快速选择提供商',
    enterKey: '输入你的 API 密钥',
    save: '保存配置',
    test: '测试连接',
    status: '查看配置状态',
  };
  const [settings, setSettings] = useState({ llm_api_key: "", llm_model: "gpt-4o-mini", llm_endpoint: "https://api.openai.com/v1" });
  const [form] = Form.useForm();
  const [testLoading, setTestLoading] = useState(false);
  const load = () => { getSettings().then(r => { if (r.data.settings) { setSettings(r.data.settings); form.setFieldsValue(r.data.settings); } }); };
  useEffect(() => { load(); }, []);
  const handlePreset = (key) => {
    const presets = {
      openai: { label: "OpenAI", endpoint: "https://api.openai.com/v1", model: "gpt-4o-mini" },
      qwen: { label: "通义千问 (Alibaba)", endpoint: "https://dashscope.aliyuncs.com/compatible-mode/v1", model: "qwen-plus" },
      deepseek: { label: "DeepSeek", endpoint: "https://api.deepseek.com/v1", model: "deepseek-chat" },
      glm: { label: "智谱清言 (GLM)", endpoint: "https://open.bigmodel.cn/api/paas/v4", model: "glm-4-flash" },
      kimi: { label: "月之暗面 (Kimi)", endpoint: "https://api.moonshot.cn/v1", model: "moonshot-v1-8k" },
      baidu: { label: "百度千帆", endpoint: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat", model: "ernie-speed-8k" },
    };
    if (presets[key]) form.setFieldsValue({ llm_endpoint: presets[key].endpoint, llm_model: presets[key].model });
  };
  const handleSave = async () => {
    const v = form.getFieldsValue();
    try { await updateSettings(v); message.success(L.save); setSettings(v); } catch (e) { message.error(e.response?.data?.error || "保存失败"); }
  };
  const handleTest = async () => {
    const v = form.getFieldsValue();
    if (!v.llm_api_key) { message.warning("请先输入 API Key"); return; }
    setTestLoading(true);
    try {
      const res = await fetch("/api/settings/test-llm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ api_key: v.llm_api_key, model: v.llm_model, endpoint: v.llm_endpoint }), credentials: "include" });
      const data = await res.json();
      if (data.ok) message.success(data.message || "连接成功");
      else message.error(data.error || "测试失败");
    } catch (e) { message.error("测试失败: " + (e.message || "")); }
    setTestLoading(false);
  };
  return (
    <div style={{ maxWidth: 600 }}>
      <Typography.Text type="secondary" style={{ display: "block", marginBottom: 16 }}>{L.desc}</Typography.Text>
      <Form form={form} layout="vertical" initialValues={settings} onFinish={handleSave}>
        <Form.Item label={L.provider}>
          <Select placeholder="选择提供商..." onChange={handlePreset}>
            {Object.entries({ openai: "OpenAI", qwen: "通义千问", deepseek: "DeepSeek", glm: "智谱", kimi: "Kimi", baidu: "百度" }).map(([k, v]) => 
              <Select.Option key={k} value={k}>{v}</Select.Option>
            )}
          </Select>
        </Form.Item>
        <Form.Item name="llm_api_key" label="API Key">
          <Input.Password placeholder={L.enterKey} prefix={<KeyOutlined />} />
        </Form.Item>
        <Form.Item name="llm_endpoint" label="API 端点">
          <Input placeholder="https://api.openai.com/v1" />
        </Form.Item>
        <Form.Item name="llm_model" label="模型名称">
          <Input placeholder="gpt-4o-mini" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">{L.save}</Button>
          <Button style={{ marginLeft: 8 }} onClick={handleTest} loading={testLoading}>{L.test}</Button>
          <Button style={{ marginLeft: 8 }} onClick={() => { if (settings.llm_api_key) message.success("API 密钥已配置"); else message.info("未配置 API Key"); }}>{L.status}</Button>
        </Form.Item>
      </Form>
    </div>
  );
}
function Settings() {
  return (
    <div>
      <Typography.Title level={4}>系统设置</Typography.Title>
      <Card size="small">
        <Tabs items={[
          { key: "projects", label: "项目管理", children: <ProjectSettings /> },
          { key: "users", label: "用户管理", children: <UserSettings /> },
          { key: "rules", label: "预警规则", children: <AlertRuleSettings /> },
          { key: "llm", label: "LLM 配置", children: <LLMSettings /> },
        ]} />
      </Card>
    </div>
  );
}
