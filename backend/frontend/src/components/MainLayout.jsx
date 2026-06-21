import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Dropdown, Typography, Space } from "antd";
import {
  DashboardOutlined, FileTextOutlined, CheckCircleOutlined, BellOutlined,
  SettingOutlined, LogoutOutlined, UserOutlined, HomeOutlined,
  FolderOpenOutlined, SearchOutlined
} from "@ant-design/icons";
import { logout } from "../api";
import GlobalSearch from "./GlobalSearch";

const { Header, Sider, Content } = Layout;

export default function MainLayout({ user, children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "仪表板" },
    { key: "/project-home", icon: <HomeOutlined />, label: "项目主页" },
    { key: "/evidence", icon: <FileTextOutlined />, label: "证据管理" },
    { key: "/settlement-packages", icon: <FolderOpenOutlined />, label: "结算组卷" },
    { key: "/approvals", icon: <CheckCircleOutlined />, label: "审核管理" },
    { key: "/alerts", icon: <BellOutlined />, label: "预警提醒" },
    { key: "/settings", icon: <SettingOutlined />, label: "系统设置" },
  ];

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const selectedKey = "/" + location.pathname.split("/")[1];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark" width={220}>
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center", borderBottom: "1px solid #303030" }}>
          <Typography.Title level={5} style={{ color: "#fff", margin: 0, fontSize: collapsed ? 14 : 16 }}>
            {collapsed ? "EC" : "证据链系统"}
          </Typography.Title>
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[selectedKey]} items={menuItems} onClick={(e) => navigate(e.key)} />
      </Sider>
      <Layout>
        <Header style={{ background: "#141414", padding: "0 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #303030" }}>
          <GlobalSearch />
          <Dropdown menu={{ items: [{ key: "logout", icon: <LogoutOutlined />, label: "退出登录", onClick: handleLogout }] }}>
            <Button type="text" style={{ color: "#fff" }} icon={<UserOutlined />}>
              {user.display_name} ({user.role})
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, minHeight: 280 }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
