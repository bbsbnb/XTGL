import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Input, List, Tag, Space, Typography } from "antd";
import { SearchOutlined, FileTextOutlined, ProjectOutlined } from "@ant-design/icons";
import { globalSearch } from "../api";

export default function GlobalSearch() {
  const [results, setResults] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSearch = async (value) => {
    if (!value.trim()) { setResults(null); setOpen(false); return; }
    setLoading(true);
    try {
      const res = await globalSearch({ q: value });
      setResults(res.data);
      setOpen(true);
    } catch {}
    setLoading(false);
  };

  return (
    <div ref={ref} style={{ position: "relative", width: 300 }}>
      <Input.Search placeholder="全局搜索证据、项目..." prefix={<SearchOutlined />}
        onSearch={handleSearch} onChange={(e) => { if (!e.target.value) { setResults(null); setOpen(false); } }}
        loading={loading} style={{ width: "100%" }} />
      {open && results && (
        <div style={{
          position: "absolute", top: "100%", left: 0, right: 0, zIndex: 1000,
          background: "#1e1e2e", border: "1px solid #303030", borderRadius: 8,
          marginTop: 4, maxHeight: 400, overflow: "auto", boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
        }}>
          {results.evidence?.length > 0 && (
            <div style={{ padding: "8px 12px" }}>
              <Typography.Text strong style={{ color: "#8b8fa8", fontSize: 12 }}>证据 ({results.evidence.length})</Typography.Text>
              <List size="small" dataSource={results.evidence.slice(0, 8)}
                renderItem={(item) => (
                  <List.Item style={{ cursor: "pointer", padding: "4px 0" }}
                    onClick={() => { setOpen(false); navigate("/evidence/" + item.id); }}>
                    <Space size={4}>
                      <FileTextOutlined style={{ color: "#1677ff" }} />
                      <Typography.Text style={{ fontSize: 13 }}>{item.title}</Typography.Text>
                      <Tag style={{ fontSize: 11, lineHeight: "18px", padding: "0 4px" }}>{item.status}</Tag>
                    </Space>
                  </List.Item>
                )} />
            </div>
          )}
          {results.projects?.length > 0 && (
            <div style={{ padding: "8px 12px", borderTop: "1px solid #303030" }}>
              <Typography.Text strong style={{ color: "#8b8fa8", fontSize: 12 }}>项目 ({results.projects.length})</Typography.Text>
              <List size="small" dataSource={results.projects.slice(0, 5)}
                renderItem={(item) => (
                  <List.Item style={{ cursor: "pointer", padding: "4px 0" }}
                    onClick={() => { setOpen(false); navigate("/project-home?project_id=" + item.id); }}>
                    <Space size={4}>
                      <ProjectOutlined style={{ color: "#52c41a" }} />
                      <Typography.Text style={{ fontSize: 13 }}>{item.name}</Typography.Text>
                    </Space>
                  </List.Item>
                )} />
            </div>
          )}
          {results.evidence?.length === 0 && results.projects?.length === 0 && (
            <div style={{ padding: 16, textAlign: "center", color: "#8b8fa8" }}>未找到结果</div>
          )}
        </div>
      )}
    </div>
  );
}
