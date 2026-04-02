"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import {
  listCVFiles,
  getCVSource,
  saveCVSource,
  recompileCV,
  cvChatEdit,
  cvSourceDownloadUrl,
  type CVFile,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  Save,
  RefreshCw,
  Download,
  Send,
  FileText,
  Loader2,
  Bot,
  User,
} from "lucide-react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function CVEditorPage() {
  const [files, setFiles] = useState<CVFile[]>([]);
  const [selected, setSelected] = useState<CVFile | null>(null);
  const [latex, setLatex] = useState("");
  const [savedLatex, setSavedLatex] = useState("");
  const [loadingFile, setLoadingFile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [recompiling, setRecompiling] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  async function loadFiles() {
    try {
      const data = await listCVFiles();
      setFiles(data);
      if (data.length > 0 && !selected) {
        selectFile(data[0]);
      }
    } catch {
      toast.error("Failed to load CV files");
    }
  }

  async function selectFile(file: CVFile) {
    setSelected(file);
    setLoadingFile(true);
    setChatMessages([]);
    try {
      const data = await getCVSource(file.filename);
      setLatex(data.latex);
      setSavedLatex(data.latex);
    } catch {
      toast.error("Failed to load CV source");
    } finally {
      setLoadingFile(false);
    }
  }

  async function handleSave() {
    if (!selected) return;
    setSaving(true);
    try {
      await saveCVSource(selected.filename, latex);
      setSavedLatex(latex);
      toast.success("Saved");
    } catch {
      toast.error("Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleRecompile() {
    if (!selected) return;
    setRecompiling(true);
    try {
      await saveCVSource(selected.filename, latex);
      setSavedLatex(latex);
      await recompileCV(selected.filename);
      toast.success("PDF recompiled successfully");
      loadFiles();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Recompile failed");
    } finally {
      setRecompiling(false);
    }
  }

  async function handleChatSend() {
    if (!chatInput.trim() || !selected || chatLoading) return;
    const message = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: message }]);
    setChatLoading(true);
    try {
      const result = await cvChatEdit(selected.filename, latex, message);
      setLatex(result.latex);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Done! I've updated the CV in the editor. Review the changes and save when ready." },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't process that edit. Please try again." },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const isDirty = latex !== savedLatex;

  return (
    <div className="flex h-full overflow-hidden">
      {/* File List Sidebar */}
      <aside className="w-60 shrink-0 border-r flex flex-col bg-muted/30">
        <div className="px-4 py-3 border-b">
          <p className="text-sm font-semibold">Generated CVs</p>
          <p className="text-xs text-muted-foreground mt-0.5">{files.length} file{files.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
          {files.length === 0 && (
            <p className="text-xs text-muted-foreground px-2 py-4 text-center">
              No CVs yet. Generate one from a job.
            </p>
          )}
          {files.map((f) => (
            <button
              key={f.filename}
              onClick={() => selectFile(f)}
              className={`w-full text-left px-3 py-2.5 rounded-md text-xs transition-colors group ${
                selected?.filename === f.filename
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent text-muted-foreground hover:text-foreground"
              }`}
            >
              <div className="flex items-start gap-2">
                <FileText className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate leading-tight">{f.stem}</p>
                  <div className="flex gap-1 mt-1">
                    {f.has_pdf && (
                      <Badge
                        variant="secondary"
                        className={`text-[10px] px-1 py-0 h-4 ${
                          selected?.filename === f.filename ? "bg-primary-foreground/20 text-primary-foreground" : ""
                        }`}
                      >
                        PDF
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* Editor Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b bg-card shrink-0">
          <div className="flex-1 min-w-0">
            {selected ? (
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium truncate">{selected.stem}</p>
                {isDirty && (
                  <Badge variant="outline" className="text-xs shrink-0">unsaved</Badge>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Select a CV to edit</p>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={handleSave} disabled={!selected || saving || !isDirty}>
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save
          </Button>
          <Button variant="outline" size="sm" onClick={handleRecompile} disabled={!selected || recompiling}>
            {recompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Recompile PDF
          </Button>
          {selected?.has_pdf && (
            <a href={cvSourceDownloadUrl(selected.stem)} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" size="sm">
                <Download className="w-3.5 h-3.5" />
                Download PDF
              </Button>
            </a>
          )}
        </div>

        {/* Editor + Chat split */}
        <div className="flex-1 flex overflow-hidden">
          {/* Monaco Editor */}
          <div className="flex-1 min-w-0 overflow-hidden">
            {loadingFile ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
              </div>
            ) : !selected ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Select a CV from the sidebar
              </div>
            ) : (
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
            )}
          </div>

          <Separator orientation="vertical" />

          {/* AI Chat Panel */}
          <div className="w-80 shrink-0 flex flex-col bg-card">
            <div className="px-4 py-3 border-b shrink-0">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-primary" />
                <p className="text-sm font-semibold">AI Editor</p>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Tell the AI what to change
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
              {chatMessages.length === 0 && (
                <div className="text-xs text-muted-foreground text-center py-6 px-2">
                  <Bot className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>Describe any change you want.</p>
                  <p className="mt-1 opacity-70">e.g. "Make the summary shorter" or "Add more emphasis on Python skills"</p>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <div className={`w-6 h-6 rounded-full shrink-0 flex items-center justify-center ${
                    msg.role === "user" ? "bg-primary" : "bg-muted"
                  }`}>
                    {msg.role === "user"
                      ? <User className="w-3 h-3 text-primary-foreground" />
                      : <Bot className="w-3 h-3 text-foreground" />
                    }
                  </div>
                  <div className={`text-xs rounded-lg px-3 py-2 max-w-[200px] ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}>
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
                  placeholder={selected ? "Describe a change…" : "Select a CV first"}
                  disabled={!selected || chatLoading}
                  rows={3}
                  className="flex-1 resize-none text-xs rounded-md border bg-background px-3 py-2 placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
                />
                <Button
                  size="icon"
                  className="shrink-0 self-end"
                  onClick={handleChatSend}
                  disabled={!selected || !chatInput.trim() || chatLoading}
                >
                  <Send className="w-3.5 h-3.5" />
                </Button>
              </div>
              <p className="text-[10px] text-muted-foreground mt-1.5">Enter to send · Shift+Enter for newline</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
