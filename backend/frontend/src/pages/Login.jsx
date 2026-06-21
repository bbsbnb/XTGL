import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Form, Input, Button, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { login } from "../api";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const res = await login(values.username, values.password);
      if (res.data.ok) {
        message.success("登录成功");
        navigate("/");
      }
    } catch (e) {
      message.error(e.response?.data?.error || "登录失败");
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "#0f1117" }}>
      <Card style={{ width: 400, boxShadow: "0 4px 24px rgba(0,0,0,0.3)" }}>
        <Typography.Title level={3} style={{ textAlign: "center", marginBottom: 32 }}>
          工程项目证据链管理系统
        </Typography.Title>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>登 录</Button>
          </Form.Item>
        </Form>
        <Typography.Text type="secondary" style={{ display: "block", textAlign: "center", fontSize: 12 }}>
          默认账号: admin / admin123
        </Typography.Text>
      </Card>
    </div>
  );
}
