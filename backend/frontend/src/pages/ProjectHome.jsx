import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Card, Row, Col, Statistic, Table, List, Tag, Typography, Select, Space } from "antd";
import { FileTextOutlined, CheckCircleOutlined, BellOutlined, ProjectOutlined } from "@ant-design/icons";
import { getProjectHome, getProjects } from "../api";

export default function ProjectHome() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(params.get("project_id") || null);

  useEffect(() => { getProjects().then((r) => setProjects(r.data.data)); }, []);
  useEffect(() => { getProjectHome().then((r) => setData(r.data)); }, []);

  if (!data) return <div style={{ textAlign: "center", padding: 48 }}>加载中...</div>;

  const statusColors = { "待提交": "default", "待审核": "processing", "已审核": "success", "退回": "error" };

  return (
    <div>
      <Typography.Title level={4}>项目主页</Typography.Title>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="总证据数" value={data.total} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="项目数" value={data.by_project?.length || 0} prefix={<ProjectOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="未处理预警" value={data.alerts?.length || 0} prefix={<BellOutlined />} valueStyle={{ color: "#faad14" }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="已完成审核" value={data.by_project?.reduce((a, b) => a + (b.approved || 0), 0) || 0} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="各项目统计" size="small">
            <Table dataSource={data.by_project} rowKey="id" pagination={false} size="small"
              columns={[
                { title: "项目", dataIndex: "name" },
                { title: "证据数", dataIndex: "cnt" },
                { title: "已审核", dataIndex: "approved", render: (v) => <Tag color="green">{v}</Tag> },
              ]}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最近提交证据" size="small" style={{ marginBottom: 16 }}>
            <Table dataSource={data.recent} rowKey="id" pagination={false} size="small" showHeader={false}
              columns={[
                { title: "", dataIndex: "title", ellipsis: true, render: (t, r) => <a href={"/evidence/" + r.id}>{t}</a> },
                { title: "", dataIndex: "project_name", width: 120 },
                { title: "", dataIndex: "status", width: 80, render: (s) => <Tag color={statusColors[s]}>{s}</Tag> },
              ]}
            />
          </Card>
          <Card title="未处理预警" size="small">
            <List size="small" dataSource={data.alerts}
              renderItem={(item) => (
                <List.Item>
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
