import React, { useState, useEffect } from "react";
import { Card, Row, Col, Statistic, Table, Tag, List, Typography, Button, Space } from "antd";
import { FileTextOutlined, CheckCircleOutlined, BellOutlined, ExclamationCircleOutlined } from "@ant-design/icons";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getDashboard } from "../api";

export default function Dashboard() {
  const [data, setData] = useState(null);
  useEffect(() => { getDashboard().then(r => setData(r.data)); }, []);

  if (!data) return <div style={{textAlign:"center",padding:48}}>加载中...</div>;

  const statusColors = { "待提交": "default", "待审核": "processing", "已审核": "success", "退回": "error", "已归档": "purple", "存疑": "warning" };

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}>仪表板</Typography.Title>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="总证据数" value={data.total} prefix={<FileTextOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="待审核" value={data.pending_approval} prefix={<CheckCircleOutlined />} valueStyle={{color:"#1677ff"}} /></Card></Col>
        <Col span={6}><Card><Statistic title="未处理预警" value={data.alert_count} prefix={<BellOutlined />} valueStyle={{color:"#faad14"}} /></Card></Col>
        <Col span={6}>
          <Card>
            <Statistic title="项目数" value={data.by_project?.length || 0} prefix={<ExclamationCircleOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="按状态统计" size="small">
            <Table dataSource={data.by_status} rowKey="status" pagination={false} size="small"
              columns={[
                { title: "状态", dataIndex: "status", render: (s) => <Tag color={statusColors[s]}>{s}</Tag> },
                { title: "数量", dataIndex: "cnt" },
              ]}
            />
          </Card>
          <Card title="各项目统计" size="small" style={{ marginTop: 16 }}>
            <Table dataSource={data.by_project} rowKey="name" pagination={false} size="small"
              columns={[
                { title: "项目", dataIndex: "name" },
                { title: "证据数", dataIndex: "cnt" },
              ]}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最近活动" size="small">
            <List size="small" dataSource={data.recent_activity}
              renderItem={(item) => (
                <List.Item>
                  <Typography.Text strong>{item.user_name || "系统"}</Typography.Text>
                  <Typography.Text style={{ marginLeft: 8 }}>{item.action}</Typography.Text>
                  <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>{item.created_at}</Typography.Text>
                </List.Item>
              )}
            />
          </Card>
          <Card title="未处理预警" size="small" style={{ marginTop: 16 }}>
            <List size="small" dataSource={data.alerts}
              renderItem={(item) => (
                <List.Item>
                  <Tag color={item.severity === "高" ? "red" : item.severity === "中" ? "orange" : "blue"}>{item.severity}</Tag>
                  <Typography.Text>{item.title}</Typography.Text>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
