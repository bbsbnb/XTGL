import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Input, InputNumber, Select, DatePicker, Button, Upload, message, Space, Typography } from "antd";
import { UploadOutlined, InboxOutlined } from "@ant-design/icons";
import { getEvidenceDetail, createEvidence, updateEvidence, getProjects, getCategories, llmExtract, uploadAttachment } from "../api";

const { Dragger } = Upload;

export default function EvidenceForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [categories, setCategories] = useState([]);
  const [fileList, setFileList] = useState([]);
  const [savedEid, setSavedEid] = useState(null);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const isEdit = !!id;

  useEffect(() => {
    getProjects().then(r => setProjects(r.data.data));
    getCategories().then(r => setCategories(r.data.data.filter(c => c.level === 2)));
    if (isEdit) {
      getEvidenceDetail(id).then(r => {
        const d = r.data;
        form.setFieldsValue({ ...d, event_time: null });
      });
    }
  }, [id]);

  const handleLLMExtract = async () => {
    const desc = form.getFieldValue("description");
    if (!desc) { message.warning("请先输入事件描述"); return; }
    try {
      const res = await llmExtract(desc);
      if (res.data.ok && res.data.extracted) {
        const e = res.data.extracted;
        const fields = {};
        if (e.title && !form.getFieldValue("title")) fields.title = e.title;
        if (e.total_amount) fields.total_amount = e.total_amount;
        if (e.quantity) fields.quantity = e.quantity;
        form.setFieldsValue(fields);
        message.success("AI 提取完成");
      }
    } catch { message.error("AI 提取失败"); }
  };

  const uploadFiles = async (eid) => {
    if (fileList.length === 0) return;
    setUploadingFiles(true);
    let success = 0;
    for (const f of fileList) {
      try {
        await uploadAttachment(eid, f.originFileObj || f);
        success++;
      } catch { /* skip failed files */ }
    }
    setUploadingFiles(false);
    if (success > 0) message.success(`已上传 ${success} 个附件`);
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const payload = { ...values, event_time: values.event_time ? values.event_time.format("YYYY-MM-DD") : "" };
      let eid;
      if (isEdit) {
        await updateEvidence(id, payload);
        eid = id;
        message.success("更新成功");
      } else {
        const res = await createEvidence(payload);
        eid = res.data.data.id;
        message.success("创建成功");
      }
      await uploadFiles(eid);
      navigate("/evidence");
    } catch (e) {
      message.error(e.response?.data?.error || "操作失败");
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <Typography.Title level={4}>{isEdit ? "编辑证据" : "新增证据"}</Typography.Title>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="project_id" label="项目" rules={[{ required: true }]}>
            <Select placeholder="选择项目">
              {projects.map(p => <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="category_id" label="分类" rules={[{ required: true }]}>
            <Select placeholder="选择分类">
              {categories.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="证据标题" />
          </Form.Item>
          <Form.Item name="event_time" label="事件时间" rules={[{ required: true }]}>
            <DatePicker style={{ width: "100%" }} placeholder="选择日期" />
          </Form.Item>
          <Form.Item name="description" label="事件描述">
            <Input.TextArea rows={3} placeholder="描述事件原由" />
          </Form.Item>
          <Form.Item name="solution" label="处理方案">
            <Input.TextArea rows={3} placeholder="处理方案" />
          </Form.Item>
          <Space style={{ width: "100%" }} size={16}>
            <Form.Item name="quantity" label="工程量"><InputNumber style={{ width: "100%" }} /></Form.Item>
            <Form.Item name="unit_price" label="单价"><InputNumber style={{ width: "100%" }} /></Form.Item>
            <Form.Item name="total_amount" label="总金额"><InputNumber style={{ width: "100%" }} /></Form.Item>
          </Space>
          <Form.Item name="contract_no" label="合同编号"><Input placeholder="可选" /></Form.Item>
          <Form.Item name="location" label="地点"><Input placeholder="可选" /></Form.Item>

          <Card title="附件文件" size="small" style={{ marginBottom: 16 }}>
            <Dragger multiple fileList={fileList} onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={(file) => { setFileList(prev => [...prev, { ...file, uid: file.uid }]); return false; }}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.zip,.rar,.dwg">
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p className="ant-upload-hint">支持 PDF、Word、Excel、图片等格式，保存证据时自动上传</p>
            </Dragger>
          </Card>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading || uploadingFiles}>保存并上传附件</Button>
              <Button onClick={() => navigate("/evidence")}>取消</Button>
              <Button onClick={handleLLMExtract}>AI 提取信息</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
