"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { toast } from "sonner";
import {
  generateCustomCV,
  cvPreviewUrl,
  cvSourceDownloadUrl,
  getCVSource,
  saveCVSource,
  recompileCV,
  cvChatEdit,
  type CVGenerateResponse,
} from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Download,
  FileText,
  Loader2,
  Send,
  Bot,
  User,
  ArrowLeft,
  Save,
  RefreshCw,
  Eye,
  EyeOff,
  PanelRightOpen,
  PanelRightClose,
} from "lucide-react";
import { cn } from "@/lib/utils";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

const TEMPLATES = [
  { id: "t1", label: "Template 1", desc: "Classic single-column" },
  { id: "t2", label: "Template 2", desc: "Modern two-column" },
  { id: "t3", label: "Template 3", desc: "Minimal clean" },
] as const;

type TemplateId = "t1" | "t2" | "t3";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function CustomCVPage() {
  // Phase 1: Form state
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId>("t1");
  const [generating, setGenerating] = useState(false);

  // Phase 2: Editor state
  const [result, setResult] = useState<CVGenerateResponse | null>(null);
  const [latex, setLatex] = useState("");
  const [savedLatex, setSavedLatex] = useState("");
  const [filename, setFilename] = useState("");
  const [stem, setStem] = useState("");
  const [saving, setSaving] = useState(false);
  const [recompiling, setRecompiling] = useState(false);
  const [previewKey, setPreviewKey] = useState(0);
  const [showPreview, setShowPreview] = useState(true);
  const [showChat, setShowChat] = useState(true);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const canSubmit = title.trim() && companyName.trim() && description.trim() && !generating;
  const isDirty = latex !== savedLatex;
  const isEditorPhase = result !== null;

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateCustomCV({
        title: title.trim(),
        company_name: companyName.trim(),
        description: description.trim(),
        template: selectedTemplate,
      });
      setResult(res);

      // Load the generated LaTeX source
      const pdfPath = res.pdf_path;
      const texFile = pdfPath.replace(/\\/g, "/").split("/").pop()!.replace(".pdf", ".tex");
      const stemName = texFile.replace(".tex", "");
      setFilename(texFile);
      setStem(stemName);

      const source = await getCVSource(texFile);
      setLatex(source.latex);
      setSavedLatex(source.latex);
      setPreviewKey((k) => k + 1);

      toast.success("CV generated! You can now edit and preview it.");
    } catch (e) {
      toast.error(`Generation failed: ${(e as Error).message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!filename) return;
    setSaving(true);
    try {
      await saveCVSource(filename, latex);
      setSavedLatex(latex);
      toast.success("Saved");
    } catch {
      toast.error("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleRecompile = useCallback(async () => {
    if (!filename) return;
    setRecompiling(true);
    try {
      await saveCVSource(filename, latex);
      setSavedLatex(latex);
      await recompileCV(filename);
      setPreviewKey((k) => k + 1);
      toast.success("PDF recompiled");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Recompile failed");
    } finally {
      setRecompiling(false);
    }
  }, [filename, latex]);

  const handleChatSend = async () => {
    if (!chatInput.trim() || !filename || chatLoading) return;
    const message = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: message }]);
    setChatLoading(true);
    try {
      const res = await cvChatEdit(filename, latex, message);
      setLatex(res.latex);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Updated the CV. Click Recompile to see the preview, or keep chatting." },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't process that. Please try again." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleBack = () => {
    setResult(null);
    setLatex("");
    setSavedLatex("");
    setFilename("");
    setStem("");
    setChatMessages([]);
    setChatInput("");
    setPreviewKey(0);
  };

  // ─── Phase 1: Form ────────────────────────────────────────────────────────────
  if (!isEditorPhase) {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <TopBar title="Custom CV" />
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-3xl mx-auto space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="h-4 w-4" /> Job Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Job Title</Label>
                    <Input
                      id="title"
                      placeholder="e.g. Full Stack Developer"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company">Company Name</Label>
                    <Input
                      id="company"
                      placeholder="e.g. Google"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Job Description</Label>
                  <textarea
                    id="description"
                    rows={14}
                    placeholder="Paste the full job circular / description here..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y min-h-[120px]"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Select Template</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  {TEMPLATES.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTemplate(t.id)}
                      className={cn(
                        "border rounded-lg p-3 text-left transition-colors",
                        selectedTemplate === t.id
                          ? "border-primary bg-primary/5 ring-1 ring-primary"
                          : "hover:bg-accent"
                      )}
                    >
                      <p className="font-medium text-sm">{t.label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{t.desc}</p>
                    </button>
                  ))}
                </div>
                <Button onClick={handleGenerate} disabled={!canSubmit} size="lg">
                  {generating && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  {generating ? "Generating CV..." : "Generate CV"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // ─── Phase 2: Editor + Preview + Chat ─────────────────────────────────────────
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b bg-card shrink-0">
        <Button variant="ghost" size="sm" onClick={handleBack}>
          <ArrowLeft className="w-3.5 h-3.5 mr-1" /> New
        </Button>
        <Separator orientation="vertical" className="h-5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">
              {result.job_title} — {result.company_name}
            </p>
            {isDirty && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300 font-medium">
                unsaved
              </span>
            )}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleSave} disabled={saving || !isDirty}>
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          Save
        </Button>
        <Button variant="outline" size="sm" onClick={handleRecompile} disabled={recompiling}>
          {recompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          Recompile
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowPreview((p) => !p)}
          title={showPreview ? "Hide preview" : "Show preview"}
        >
          {showPreview ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          Preview
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowChat((c) => !c)}
          title={showChat ? "Hide chat" : "Show chat"}
        >
          {showChat ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
          Chat
        </Button>
        <a href={cvSourceDownloadUrl(stem)} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <Download className="w-3.5 h-3.5" /> PDF
          </Button>
        </a>
      </div>

      {/* Main content: Editor | Preview | Chat */}
      <div className="flex-1 flex overflow-hidden">
        {/* Monaco Editor */}
        <div className="flex-1 min-w-0 overflow-hidden">
          <MonacoEditor
            height="100%"
            language="latex"
            value={latex}
            onChange={(val) => setLatex(val ?? "")}
            theme="vs-dark"
            options={{
              fontSize: 13,
              minimap: { enabled: false },
              wordWrap: "on",
              scrollBeyondLastLine: false,
              lineNumbers: "on",
              renderWhitespace: "none",
              padding: { top: 12, bottom: 12 },
            }}
          />
        </div>

        {/* PDF Preview */}
        {showPreview && (
          <>
            <Separator orientation="vertical" />
            <div className="w-[45%] shrink-0 flex flex-col bg-muted/20">
              <div className="px-4 py-2 border-b flex items-center gap-2 shrink-0">
                <Eye className="w-3.5 h-3.5 text-muted-foreground" />
                <p className="text-xs font-medium text-muted-foreground">PDF Preview</p>
                <p className="text-[10px] text-muted-foreground ml-auto">Click Recompile to refresh</p>
              </div>
              <div className="flex-1 overflow-hidden">
                <iframe
                  key={previewKey}
                  src={`${cvPreviewUrl(stem)}#toolbar=0&navpanes=0`}
                  className="w-full h-full border-0"
                  title="CV Preview"
                />
              </div>
            </div>
          </>
        )}

        {/* AI Chat Panel */}
        {showChat && (
          <>
            <Separator orientation="vertical" />
            <div className="w-80 shrink-0 flex flex-col bg-card">
              <div className="px-4 py-3 border-b shrink-0">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-primary" />
                  <p className="text-sm font-semibold">AI Editor</p>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Ask to add, remove, or change anything
                </p>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
                {chatMessages.length === 0 && (
                  <div className="text-xs text-muted-foreground text-center py-6 px-2">
                    <Bot className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>Describe any change you want.</p>
                    <p className="mt-1 opacity-70">
                      e.g. &quot;Add my research projects&quot; or &quot;Remove certifications section&quot;
                    </p>
                  </div>
                )}
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full shrink-0 flex items-center justify-center ${
                        msg.role === "user" ? "bg-primary" : "bg-muted"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <User className="w-3 h-3 text-primary-foreground" />
                      ) : (
                        <Bot className="w-3 h-3 text-foreground" />
                      )}
                    </div>
                    <div
                      className={`text-xs rounded-lg px-3 py-2 max-w-[220px] ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-foreground"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex gap-2">
                    <div className="w-6 h-6 rounded-full shrink-0 flex items-center justify-center bg-muted">
                      <Bot className="w-3 h-3" />
                    </div>
                    <div className="bg-muted rounded-lg px-3 py-2">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Input */}
              <div className="p-3 border-t shrink-0">
                <div className="flex gap-2">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleChatSend();
                      }
                    }}
                    placeholder="Describe a change..."
                    disabled={chatLoading}
                    rows={3}
                    className="flex-1 resize-none text-xs rounded-md border bg-background px-3 py-2 placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
                  />
                  <Button
                    size="icon"
                    className="shrink-0 self-end"
                    onClick={handleChatSend}
                    disabled={!chatInput.trim() || chatLoading}
                  >
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
                <p className="text-[10px] text-muted-foreground mt-1.5">
                  Enter to send · Shift+Enter for newline
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
