import React, { useState, useEffect } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider, App as AntApp, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProjectHome from "./pages/ProjectHome";
import EvidenceList from "./pages/EvidenceList";
import EvidenceForm from "./pages/EvidenceForm";
import EvidenceDetail from "./pages/EvidenceDetail";
import Approvals from "./pages/Approvals";
import Alerts from "./pages/Alerts";
import SettlementPackages from "./pages/SettlementPackages";
import Settings from "./pages/Settings";
import MainLayout from "./components/MainLayout";
import { getMe } from "./api";

function ProtectedRoute({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getMe().then(r => { setUser(r.data.user); setLoading(false); }).catch(() => setLoading(false));
  }, []);
  if (loading) return <div style={{display:"flex",height:"100vh",justifyContent:"center",alignItems:"center",color:"#666"}}>加载中...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <MainLayout user={user}>{children}</MainLayout>;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{ algorithm: theme.darkAlgorithm, token: { colorPrimary: "#1677ff" } }}>
      <AntApp>
        <HashRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/project-home" element={<ProtectedRoute><ProjectHome /></ProtectedRoute>} />
            <Route path="/evidence" element={<ProtectedRoute><EvidenceList /></ProtectedRoute>} />
            <Route path="/evidence/new" element={<ProtectedRoute><EvidenceForm /></ProtectedRoute>} />
            <Route path="/evidence/:id" element={<ProtectedRoute><EvidenceDetail /></ProtectedRoute>} />
            <Route path="/evidence/:id/edit" element={<ProtectedRoute><EvidenceForm /></ProtectedRoute>} />
            <Route path="/approvals" element={<ProtectedRoute><Approvals /></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
            <Route path="/settlement-packages" element={<ProtectedRoute><SettlementPackages /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </HashRouter>
      </AntApp>
    </ConfigProvider>
  );
}
