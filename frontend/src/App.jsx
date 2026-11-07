
import { useRef, useState } from "react";

import {
  LayoutDashboard,
  Files,
  MessageSquare,
  Mic,
  Settings,
  Bell,
  Plus,
  ArrowRight,
  FileText,
  Database,
  Sparkles,
  Upload,
  FolderOpen,
  ShieldCheck,
  Activity,
  ChevronRight,
  Send,
  Bot,
  LoaderCircle,
  BookOpen,
  CheckCircle2,
  Clock3,
  X,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

// Frontend limits improve user experience. The backend must enforce
// the same limits because browser-side checks can be bypassed.
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const MAX_QUESTION_LENGTH = 500;

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Documents", icon: Files },
  { label: "AI Workspace", icon: MessageSquare },
  { label: "Voice Assistant", icon: Mic },
];

function App() {
  const fileInputRef = useRef(null);
  const askSectionRef = useRef(null);
  const documentsSectionRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState(false);
  const [documents, setDocuments] = useState([]);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [askError, setAskError] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [questionsAsked, setQuestionsAsked] = useState(0);

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function openAskSection() {
    askSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function openDocumentsSection() {
    documentsSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");
    const hasPdfMimeType =
      !file.type || file.type === "application/pdf";

    if (!hasPdfExtension || !hasPdfMimeType) {
      setUploadError(true);
      setUploadMessage("Only PDF files are allowed. Please select a valid PDF.");
      event.target.value = "";
      return;
    }

    if (file.size === 0) {
      setUploadError(true);
      setUploadMessage("The selected file is empty.");
      event.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError(true);
      setUploadMessage("The PDF must be 10 MB or smaller.");
      event.target.value = "";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setUploadError(false);
    setUploadMessage("Uploading and processing your PDF...");

    try {
      const response = await fetch(`${API_URL}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setDocuments((previousDocuments) => [
        {
          ...data,
          uploadedAt: new Date().toLocaleString(),
        },
        ...previousDocuments,
      ]);

      setSelectedDocumentId(data.document_id);
      setUploadMessage("Document uploaded and indexed successfully!");
      setUploadError(false);
    } catch (error) {
      setUploadError(true);
      setUploadMessage(
        error.message || "Unable to connect to the backend."
      );
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleAskQuestion(event) {
    event.preventDefault();

    if (!question.trim()) {
      setAskError("Please enter a question.");
      return;
    }

    if (question.trim().length > MAX_QUESTION_LENGTH) {
      setAskError(`Your question cannot exceed ${MAX_QUESTION_LENGTH} characters.`);
      return;
    }

    if (!selectedDocumentId) {
      setAskError("Please upload and select a document first.");
      return;
    }

    setAsking(true);
    setAskError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch(`${API_URL}/documents/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question.trim(),
          document_id: selectedDocumentId,
          top_k: 3,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to generate an answer.");
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
      setQuestionsAsked((previousCount) => previousCount + 1);
    } catch (error) {
      setAskError(
        error.message || "Unable to connect to the AI backend."
      );
    } finally {
      setAsking(false);
    }
  }

  const totalDocuments = documents.length;

  const totalChunks = documents.reduce(
    (total, document) => total + document.stored_chunks,
    0
  );

  return (
    <div className="app-shell">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileUpload}
      />

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={21} strokeWidth={1.8} />
          </div>

          <div>
            <h1>NEXORA AI</h1>
            <p>Document Intelligence</p>
          </div>
        </div>

        <div className="sidebar-group">
          <p className="sidebar-heading">WORKSPACE</p>

          <nav className="sidebar-nav">
            {navItems.map((item, index) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  onClick={
                    index === 1
                      ? openDocumentsSection
                      : index === 2
                      ? openAskSection
                      : undefined
                  }
                  className={`sidebar-link ${
                    index === 0 ? "sidebar-link-active" : ""
                  }`}
                >
                  <Icon size={18} strokeWidth={1.7} />
                  <span>{item.label}</span>

                  {index === 2 && (
                    <span className="sidebar-link-dot" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="sidebar-group sidebar-preferences">
          <p className="sidebar-heading">PREFERENCES</p>

          <button className="sidebar-link">
            <Settings size={18} strokeWidth={1.7} />
            <span>Settings</span>
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="profile-card">
            <div className="profile-avatar">U</div>

            <div className="profile-info">
              <p>My Workspace</p>
              <span>Personal account</span>
            </div>

            <ChevronRight size={17} />
          </div>

          <p className="sidebar-footer">NEXORA AI · 2026</p>
        </div>
      </aside>

      {/* MAIN AREA */}
      <main className="main-area">
        {/* TOP BAR */}
        <header className="topbar">
          <div className="breadcrumb">
            <span>NEXORA AI</span>
            <ChevronRight size={14} />
            <strong>Overview</strong>
          </div>

          <div className="topbar-actions">
            <div className="system-indicator">
              <span />
              System ready
            </div>

            <button className="icon-button" aria-label="Notifications">
              <Bell size={19} />
            </button>

            <div className="topbar-avatar">U</div>
          </div>
        </header>

        {/* PAGE CONTENT */}
        <div className="page-content">
          {/* INTRODUCTION */}
          <section className="welcome-section">
            <div className="welcome-copy">
              <p className="eyebrow">
                <span className="eyebrow-line" />
                ADVANCED AI DOCUMENT INTELLIGENCE
              </p>

              <h2>
                Welcome to
                <br />
                <span>NEXORA AI.</span>
              </h2>

              <p className="welcome-description">
                Intelligent Knowledge. Grounded Answers.
                <br />
                Your advanced RAG-powered document intelligence
                platform. Upload documents, discover insights,
                and receive accurate answers grounded in your
                own knowledge base.
              </p>

              <button
                onClick={openFilePicker}
                disabled={uploading}
                className="primary-button"
              >
                <Plus size={18} />
                {uploading ? "Uploading..." : "Upload a document"}
                <ArrowRight size={16} />
              </button>
            </div>

            <div className="welcome-art">
              <div className="art-circle art-circle-one" />
              <div className="art-circle art-circle-two" />

              <div className="art-document">
                <FileText size={65} strokeWidth={1.1} />
                <div className="art-document-lines">
                  <span />
                  <span />
                  <span />
                </div>
              </div>

              <div className="art-floating art-floating-top">
                <Sparkles size={19} />
              </div>

              <div className="art-floating art-floating-bottom">
                <ShieldCheck size={20} />
              </div>
            </div>
          </section>

          {/* UPLOAD STATUS */}
          {uploadMessage && (
            <div
              className={`status-message ${
                uploadError
                  ? "status-error"
                  : uploading
                  ? "status-loading"
                  : "status-success"
              }`}
            >
              <div className="status-icon">
                {uploadError ? (
                  <X size={18} />
                ) : uploading ? (
                  <LoaderCircle size={18} className="animate-spin" />
                ) : (
                  <CheckCircle2 size={18} />
                )}
              </div>

              <div className="status-copy">
                <strong>
                  {uploading
                    ? "Processing document"
                    : uploadError
                    ? "Upload failed"
                    : "Upload successful"}
                </strong>

                <p>{uploadMessage}</p>

                {documents.length > 0 &&
                  !uploadError &&
                  !uploading && (
                    <div className="upload-details">
                      <span>Latest file: {documents[0].filename}</span>

                      <span>
                        {documents[0].total_pages} pages ·{" "}
                        {documents[0].stored_chunks} chunks
                      </span>

                      <span className="document-id">
                        Document ID: {documents[0].document_id}
                      </span>
                    </div>
                  )}
              </div>
            </div>
          )}

          {/* STATISTICS */}
          <section className="stats-grid">
            <StatCard
              icon={Files}
              label="Documents"
              value={totalDocuments}
              note="Files in your workspace"
            />

            <StatCard
              icon={Database}
              label="Indexed chunks"
              value={totalChunks}
              note="Knowledge segments"
            />

            <StatCard
              icon={MessageSquare}
              label="Questions asked"
              value={questionsAsked}
              note="Queries processed"
            />

            <StatCard
              icon={Activity}
              label="System status"
              value="Ready"
              note="Local AI workspace"
              status
            />
          </section>

          {/* DOCUMENTS AND QUICK ACTIONS */}
          <section
            ref={documentsSectionRef}
            className="content-grid section-anchor"
          >
            <div className="surface-card library-card">
              <div className="section-topline">
                <div>
                  <p className="eyebrow">YOUR KNOWLEDGE BASE</p>
                  <h3>Recent documents</h3>

                  <p className="section-description">
                    Your uploaded files, organised and ready for
                    intelligent retrieval.
                  </p>
                </div>

                <button
                  onClick={openDocumentsSection}
                  className="text-link"
                >
                  View library <ArrowRight size={16} />
                </button>
              </div>

              {documents.length === 0 ? (
                <div className="empty-library">
                  <div className="empty-icon">
                    <FolderOpen size={27} />
                  </div>

                  <h4>Your knowledge base is waiting</h4>

                  <p>
                    Upload your first PDF to start building your
                    searchable knowledge base.
                  </p>

                  <button
                    onClick={openFilePicker}
                    disabled={uploading}
                    className="secondary-button"
                  >
                    <Upload size={16} />
                    {uploading ? "Uploading..." : "Choose a PDF"}
                  </button>
                </div>
              ) : (
                <div className="document-list">
                  {documents.map((document) => (
                    <div
                      key={document.document_id}
                      className={`document-row ${
                        selectedDocumentId === document.document_id
                          ? "document-row-selected"
                          : ""
                      }`}
                    >
                      <div className="document-icon">
                        <FileText size={22} />
                      </div>

                      <div className="document-info">
                        <p>{document.filename}</p>

                        <span>
                          {document.total_pages} pages
                          <span className="metadata-separator">·</span>
                          {document.stored_chunks} chunks
                        </span>

                        <small>
                          <Clock3 size={12} />
                          {document.uploadedAt}
                        </small>
                      </div>

                      <button
                        onClick={() =>
                          setSelectedDocumentId(document.document_id)
                        }
                        className={`select-button ${
                          selectedDocumentId === document.document_id
                            ? "selected"
                            : ""
                        }`}
                      >
                        {selectedDocumentId === document.document_id
                          ? "Selected"
                          : "Select"}
                      </button>
                    </div>
                  ))}

                  <button
                    onClick={openFilePicker}
                    disabled={uploading}
                    className="add-document-button"
                  >
                    <Plus size={17} />
                    Add another document
                  </button>
                </div>
              )}
            </div>

            <div className="surface-card actions-card">
              <p className="eyebrow">GET STARTED</p>

              <h3>Make more of your documents.</h3>

              <p className="section-description">
                Choose what you would like to do next.
              </p>

              <div className="quick-actions">
                <QuickAction
                  icon={Upload}
                  title="Upload documents"
                  description="Add PDFs to your workspace"
                  onClick={openFilePicker}
                />

                <QuickAction
                  icon={MessageSquare}
                  title="Ask your documents"
                  description="Get grounded answers with AI"
                  onClick={openAskSection}
                />

                <QuickAction
                  icon={Mic}
                  title="Voice interaction"
                  description="Voice assistant coming soon"
                />
              </div>
            </div>
          </section>

          {/* AI WORKSPACE */}
          <section
            ref={askSectionRef}
            className="surface-card ai-section section-anchor"
          >
            <div className="ai-section-heading">
              <div>
                <p className="eyebrow">NEXORA AI ASSISTANT</p>

                <h3>Ask your documents.</h3>

                <p className="section-description">
                  Retrieve relevant information and receive
                  source-grounded answers from your documents.
                </p>
              </div>

              <div className="model-label">
                <span />
                Local AI · Llama 3.2
              </div>
            </div>

            <form onSubmit={handleAskQuestion} className="question-form">
              <div className="form-field">
                <label htmlFor="document-select">
                  Choose a document
                </label>

                <select
                  id="document-select"
                  value={selectedDocumentId}
                  onChange={(event) =>
                    setSelectedDocumentId(event.target.value)
                  }
                  className="form-select"
                >
                  <option value="">Select an uploaded document</option>

                  {documents.map((document) => (
                    <option
                      key={document.document_id}
                      value={document.document_id}
                    >
                      {document.filename}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="question-input">Your question</label>

                <div className="question-input-wrap">
                  <input
                    id="question-input"
                    type="text"
                    value={question}
                    maxLength={MAX_QUESTION_LENGTH}
                    onChange={(event) => {
                      setQuestion(event.target.value);
                      if (askError) setAskError("");
                    }}
                    placeholder="Ask Nexora anything about your document..."
                    disabled={asking}
                    aria-describedby="question-character-count"
                  />

                  <button
                    type="submit"
                    disabled={
                      asking || !question.trim() || !selectedDocumentId
                    }
                    className="ask-button"
                  >
                    {asking ? (
                      <>
                        <LoaderCircle
                          size={17}
                          className="animate-spin"
                        />
                        Thinking
                      </>
                    ) : (
                      <>
                        Ask AI
                        <ArrowRight size={17} />
                      </>
                    )}
                  </button>
                </div>

                <p id="question-character-count" className="form-hint">
                  {question.length}/{MAX_QUESTION_LENGTH} characters
                </p>
              </div>
            </form>

            {documents.length === 0 && (
              <p className="form-hint">
                Upload a PDF before asking questions.
              </p>
            )}

            {askError && (
              <div className="ask-error">{askError}</div>
            )}

            {asking && (
              <div className="answer-loading">
                <LoaderCircle
                  size={22}
                  className="animate-spin"
                />

                <div>
                  <strong>Nexora is working on your answer</strong>
                  <p>
                    Retrieving relevant information from your document.
                  </p>
                </div>
              </div>
            )}

            {answer && !asking && (
              <div className="answer-area">
                <div className="answer-card">
                  <div className="answer-heading">
                    <div className="answer-avatar">
                      <Bot size={21} />
                    </div>

                    <div>
                      <strong>Nexora AI Response</strong>
                      <span>
                        Generated from your document context
                      </span>
                    </div>
                  </div>

                  <div className="answer-text">{answer}</div>
                </div>

                {sources.length > 0 && (
                  <div className="sources-area">
                    <div className="sources-heading">
                      <div>
                        <BookOpen size={18} />
                        <strong>Retrieved Sources</strong>
                        <span>{sources.length} references</span>
                      </div>
                    </div>

                    <div className="source-list">
                      {sources.map((source, index) => {
                        const sourceDocument = documents.find(
                          (document) =>
                            document.document_id === source.document_id
                        );

                        return (
                          <details
                            key={`${source.document_id}-${source.page_number}-${index}`}
                            className="source-item"
                          >
                            <summary>
                              <div className="source-summary-left">
                                <FileText size={17} />
                                <span>Source {index + 1}</span>

                                <small>
                                  {sourceDocument?.filename ||
                                    "Uploaded document"}
                                </small>
                              </div>

                              <div className="source-summary-right">
                                <span>Page {source.page_number}</span>
                                <ChevronRight size={17} />
                              </div>
                            </summary>

                            <div className="source-content">
                              {source.text}
                            </div>
                          </details>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!answer && !asking && !askError && (
              <div className="ai-empty-state">
                <div className="ai-empty-icon">
                  <Sparkles size={22} />
                </div>

                <strong>Your Nexora assistant is ready.</strong>

                <p>
                  Select a document and enter a question to get
                  started.
                </p>
              </div>
            )}
          </section>

          {/* FOOTER */}
          <footer className="page-footer">
            <span>NEXORA AI © 2026</span>
            <span>
              ADVANCED RAG-POWERED DOCUMENT INTELLIGENCE PLATFORM
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, note, status }) {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <span>{label}</span>
        <Icon size={19} strokeWidth={1.7} />
      </div>

      <div className="stat-value">
        {status && <span className="ready-dot" />}
        {String(value).padStart(typeof value === "number" ? 2 : 1, "0")}
      </div>

      <p>{note}</p>
    </div>
  );
}

function QuickAction({ icon: Icon, title, description, onClick }) {
  return (
    <button
      onClick={onClick}
      className="quick-action"
      disabled={!onClick}
    >
      <div className="quick-action-icon">
        <Icon size={19} strokeWidth={1.8} />
      </div>

      <div>
        <strong>{title}</strong>
        <span>{description}</span>
      </div>

      <ArrowRight size={17} className="quick-action-arrow" />
    </button>
  );
}

export default App;
