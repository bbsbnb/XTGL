import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Button, Space, Upload, List, Typography, Modal, message, Spin } from "antd";
import { EditOutlined, UploadOutlined, DeleteOutlined } from "@ant-design/icons";
import { getEvidenceDetail, submitApproval, uploadAttachment, deleteAttachment } from "../api";

export default function EvidenceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getEvidenceDetail(id).then(r => setData(r.data)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [id]);

  const handleSubmitApproval = async () => {
    await submitApproval(id);
    message.success("已提交审核"); load();
  };

  const handleUpload = async (file) => {
    try {
      await uploadAttachment(id, file);
      message.success("上传成功"); load();
    } catch { message.error("上传失败"); }
    return false;
  };

  const handleDeleteAtt = async (aid) => {
    Modal.confirm({ title: "确定删除附件?", onOk: async () => {
      await deleteAttachment(aid); message.success("已删除"); load();
    }});
  };

  if (loading) return <Spin style={{ display: "block", padding: 48 }} />;
  if (!data) return <div>记录不存在</div>;

  const statusColors = { "待提交": "default", "待审核": "processing", "已审核": "success", "退回": "error" };

  return (
    <div style={{ maxWidth: 900 }}>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>{data.title}</Typography.Title>
        <Tag color={statusColors[data.status]}>{data.status}</Tag>
      </Space>

      <Card size="small" title="基本信息" extra={
        <Space>
          {data.status === "待提交" && <Button type="primary" size="small" onClick={handleSubmitApproval}>提交审核</Button>}
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate("/evidence/" + id + "/edit")}>编辑</Button>
        </Space>
      }>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="证据编号">{data.evidence_no}</Descriptions.Item>
          <Descriptions.Item label="项目">{data.project_name}</Descriptions.Item>
          <Descriptions.Item label="分类">{data.category_name}</Descriptions.Item>
          <Descriptions.Item label="事件时间">{data.event_time}</Descriptions.Item>
          <Descriptions.Item label="工程量">{data.quantity}</Descriptions.Item>
          <Descriptions.Item label="单价">{data.unit_price}</Descriptions.Item>
          <Descriptions.Item label="总金额">{data.total_amount}</Descriptions.Item>
          <Descriptions.Item label="合同编号">{data.contract_no || "-"}</Descriptions.Item>
          <Descriptions.Item label="事件描述" span={2}>{data.description || "-"}</Descriptions.Item>
          <Descriptions.Item label="处理方案" span={2}>{data.solution || "-"}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card size="small" title="附件" style={{ marginTop: 16 }}
        extra={<Upload showUploadList={false} beforeUpload={handleUpload}><Button size="small" icon={<UploadOutlined />}>上传附件</Button></Upload>}>
        <List size="small" dataSource={data.attachments || []}
          renderItem={(att) => (
            <List.Item actions={[
              <Button type="link" size="small" href={"/api/attachments/" + att.id + "/download"}>下载</Button>,
              <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteAtt(att.id)} />
            ]}>
              {att.original_name}
            </List.Item>
          )}
        />
      </Card>

      <Card size="small" title="审核记录" style={{ marginTop: 16 }}>
        <List size="small" dataSource={data.approval_records || []}
          renderItem={(item) => (
            <List.Item>
              <Tag>{item.approval_level}</Tag>
              <Tag color={item.result === "通过" ? "success" : item.result === "待审核" ? "processing" : "error"}>{item.result}</Tag>
              <Typography.Text>{item.approver_name || "-"}</Typography.Text>
              <Typography.Text type="secondary" style={{ marginLeft: 8 }}>{item.comment}</Typography.Text>
            </List.Item>
          )}
        />
      </Card>

      <Card size="small" title="预警" style={{ marginTop: 16 }}>
        <List size="small" dataSource={data.alerts || []}
          renderItem={(item) => (
            <List.Item>
              <Tag color={item.severity === "高" ? "red" : item.severity === "中" ? "orange" : "blue"}>{item.severity}</Tag>
              {item.message}
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}
