import React, { useState, useEffect } from "react";
import { Table, Button, Tag, Modal, Input, message, Typography, Card, Space } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { getPendingApprovals, reviewApproval } from "../api";

export default function Approvals() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentAid, setCurrentAid] = useState(null);
  const [currentAction, setCurrentAction] = useState("");
  const [comment, setComment] = useState("");

  const fetchData = () => {
    setLoading(true);
    getPendingApprovals().then(r => setData(r.data.data)).finally(() => setLoading(false));
  };
  useEffect(() => { fetchData(); }, []);

  const handleReview = async () => {
    try {
      await reviewApproval(currentAid, currentAction, comment);
      message.success(currentAction === "通过" ? "已通过" : "已退回");
      setModalVisible(false);
      fetchData();
    } catch (e) { message.error(e.response?.data?.error || "操作失败"); }
  };

  const columns = [
    { title: "证据编号", dataIndex: "evidence_no", width: 180 },
    { title: "标题", dataIndex: "evidence_title", ellipsis: true },
    { title: "项目", dataIndex: "project_name", width: 160 },
    { title: "审核级别", dataIndex: "approval_level", width: 100, render: (v) => <Tag>{v}</Tag> },
    { title: "提交人", dataIndex: "creator_name", width: 100 },
    { title: "提交时间", dataIndex: "created_at", width: 170 },
    {
      title: "操作", width: 160,
      render: (_, r) => (
        <Space>
          <Button type="primary" size="small" icon={<CheckCircleOutlined />}
            onClick={() => { setCurrentAid(r.id); setCurrentAction("通过"); setModalVisible(true); }}>通过</Button>
          <Button danger size="small" icon={<CloseCircleOutlined />}
            onClick={() => { setCurrentAid(r.id); setCurrentAction("退回"); setModalVisible(true); }}>退回</Button>
        </Space>
      )
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>审核管理</Typography.Title>
      <Card size="small">
        <Table columns={columns} dataSource={data} rowKey="id" loading={loading} size="small" pagination={false} />
      </Card>
      <Modal title="审核意见" open={modalVisible} onOk={handleReview} onCancel={() => setModalVisible(false)}>
        <Input.TextArea rows={3} placeholder="请输入审核意见（可选）" value={comment} onChange={(e) => setComment(e.target.value)} />
      </Modal>
    </div>
  );
}
