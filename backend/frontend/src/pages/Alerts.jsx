import React, { useState, useEffect } from "react";
import { Table, Tag, Button, message, Typography, Card, Space } from "antd";
import { ReloadOutlined, CheckOutlined } from "@ant-design/icons";
import { getAlerts, dismissAlert, checkAlerts } from "../api";

export default function Alerts() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("0");

  const fetchData = () => {
    setLoading(true);
    getAlerts({ dismissed: tab }).then(r => setData(r.data.data)).finally(() => setLoading(false));
  };
  useEffect(() => { fetchData(); }, [tab]);

  const handleDismiss = async (id) => {
    await dismissAlert(id);
    message.success("已忽略");
    fetchData();
  };

  const handleCheck = async () => {
    try {
      const res = await checkAlerts();
      message.success("检查完成，产生 " + res.data.alerts_generated + " 条新预警");
      fetchData();
    } catch { message.error("检查失败"); }
  };

  const columns = [
    { title: "标题", dataIndex: "title", ellipsis: true },
    { title: "关联证据", dataIndex: "evidence_title", ellipsis: true },
    { title: "级别", dataIndex: "severity", width: 80, render: (v) => <Tag color={v === "高" ? "red" : v === "中" ? "orange" : "blue"}>{v}</Tag> },
    { title: "消息", dataIndex: "message", ellipsis: true },
    { title: "时间", dataIndex: "created_at", width: 170 },
    {
      title: "操作", width: 100,
      render: (_, r) => !r.is_dismissed && <Button size="small" icon={<CheckOutlined />} onClick={() => handleDismiss(r.id)}>忽略</Button>
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>
        <Space>
          <span>预警提醒</span>
          <Button size="small" icon={<ReloadOutlined />} onClick={handleCheck}>扫描检查</Button>
        </Space>
      </Typography.Title>
      <Card size="small">
        <Space style={{ marginBottom: 16 }}>
          <Button type={tab === "0" ? "primary" : "default"} size="small" onClick={() => setTab("0")}>未处理</Button>
          <Button type={tab === "1" ? "primary" : "default"} size="small" onClick={() => setTab("1")}>已忽略</Button>
        </Space>
        <Table columns={columns} dataSource={data} rowKey="id" loading={loading} size="small" pagination={false} />
      </Card>
    </div>
  );
}
