import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Button, Space, Upload, List, Typography, Modal, Input, message, Spin } from "antd";
import { EditOutlined, UploadOutlined, DeleteOutlined, LinkOutlined, BulbOutlined } from "@ant-design/icons";
import { getEvidenceDetail, submitApproval, uploadAttachment, deleteAttachment, getEvidenceLinks, addEvidenceLink, removeEvidenceLink, suggestLinks, getEvidence } from "../api";

const statusColors = { "待提交": "default", "待审核": "processing", "已审核": "success", "退回": "error" };
const linkColors = { "关联": "blue", "引用": "green", "补充": "orange", "相同合同": "purple" };

export default function EvidenceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [links, setLinks] = useState([]);
  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [linkSearch, setLinkSearch] = useState("");
  const [linkCandidates, setLinkCandidates] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [suggLoading, setSuggLoading] = useState(false);

  const load = () => {
    setLoading(true);
    getEvidenceDetail(id).then(r => setData(r.data)).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [id]);
  useEffect(() => { if (id) getEvidenceLinks(id).then(r => setLinks(r.data.data)); }, [id]);
  useEffect(() => {
    if (!linkSearch.trim()) { setLinkCandidates([]); return; }
    const t = setTimeout(() => { getEvidence({ search: linkSearch, page_size: 10 }).then(r => setLinkCandidates(r.data.data)); }, 300);
    return () => clearTimeout(t);
  }, [linkSearch]);

  const handleSubmitApproval = async () => {
    await submitApproval(id);
    message.success("已提交审核"); load();
  };
  const handleUpload = async (file) => {
    try { await uploadAttachment(id, file); message.success("上传成功"); load(); } catch { message.error("上传失败"); }
    return false;
  };
  const handleDeleteAtt = async (aid) => {
    Modal.confirm({ title: "确定删除附件?", onOk: async () => { await deleteAttachment(aid); message.success("已删除"); load(); }});
  };
  const handleAddLink = async (tid, rt) => {
    try { await addEvidenceLink(id, { target_id: tid, relation_type: rt || "关联" }); message.success("已关联"); getEvidenceLinks(id).then(r => setLinks(r.data.data)); } catch (e) { message.error(e.response?.data?.error || "关联失败"); }
  };
  const handleRemoveLink = async (lid) => {
    Modal.confirm({ title: "解除关联?", onOk: async () => { await removeEvidenceLink(id, lid); message.success("已解除"); getEvidenceLinks(id).then(r => setLinks(r.data.data)); }});
  };
  const handleSuggest = async () => {
    setSuggLoading(true);
    try { const res = await suggestLinks(id); setSuggestions(res.data.data || []); if (res.data.data?.length === 0) message.info("未找到建议"); } catch { message.error("获取建议失败"); }
    setSuggLoading(false);
  };
  const handleAcceptSuggestion = async (sug) => {
    await handleAddLink(sug.id, sug.relation_type || "关联");
    setSuggestions(prev => prev.filter(s => s.id !== sug.id));
  };

  if (loading) return <Spin style={{ display: "block", padding: 48 }} />;
  if (!data) return <div>记录不存在</div>;

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
            ]}>{att.original_name}</List.Item>
          )} />
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
          )} />
      </Card>

      <Card size="small" title="关联证据" style={{ marginTop: 16 }}
        extra={<Space><Button size="small" icon={<BulbOutlined />} onClick={handleSuggest} loading={suggLoading}>AI 推荐</Button><Button size="small" icon={<LinkOutlined />} onClick={() => setLinkModalOpen(true)}>添加关联</Button></Space>}>
        {suggestions.length > 0 && <div style={{ marginBottom: 12, padding: 8, background: "#1a1a2e", borderRadius: 6 }}>
          <Typography.Text strong style={{ color: "#8b8fa8", fontSize: 12 }}>AI 推荐关联:</Typography.Text>
          {suggestions.map(s => (
            <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0" }}>
              <Space><Tag color={linkColors[s.relation_type]}>{s.relation_type}</Tag><Typography.Text>{s.title}</Typography.Text><Typography.Text type="secondary" style={{ fontSize: 12 }}>{s.reason}</Typography.Text></Space>
              <Button size="small" type="primary" onClick={() => handleAcceptSuggestion(s)}>接受</Button>
            </div>
          ))}
        </div>}
        <List size="small" dataSource={links}
          renderItem={(item) => (
            <List.Item actions={[
              <Button type="link" size="small" onClick={() => navigate("/evidence/" + item.linked_id)}>查看</Button>,
              <Button type="link" size="small" danger onClick={() => handleRemoveLink(item.id)}>解除</Button>
            ]}>
              <Space><Tag color={linkColors[item.relation_type]}>{item.relation_type}</Tag><Typography.Text>{item.title}</Typography.Text></Space>
            </List.Item>
          )}
          locale={{ emptyText: "暂无关联证据" }} />
      </Card>

      <Card size="small" title="预警" style={{ marginTop: 16 }}>
        <List size="small" dataSource={data.alerts || []}
          renderItem={(item) => (
            <List.Item>
              <Tag color={item.severity === "高" ? "red" : item.severity === "中" ? "orange" : "blue"}>{item.severity}</Tag>
              {item.message}
            </List.Item>
          )} />
      </Card>

      <Modal title="添加关联证据" open={linkModalOpen} onCancel={() => setLinkModalOpen(false)} footer={null} width={500}>
        <Input.Search placeholder="搜索证据..." value={linkSearch} onChange={e => setLinkSearch(e.target.value)} style={{ marginBottom: 12 }} />
        <List size="small" dataSource={linkCandidates}
          renderItem={(item) => (
            <List.Item actions={[<Button size="small" type="primary" onClick={() => handleAddLink(item.id, "关联")}>关联</Button>]}>
              <Typography.Text>{item.evidence_no} - {item.title}</Typography.Text>
            </List.Item>
          )}
          locale={{ emptyText: linkSearch ? "无匹配结果" : "请输入搜索关键词" }} />
      </Modal>
    </div>
  );
}
