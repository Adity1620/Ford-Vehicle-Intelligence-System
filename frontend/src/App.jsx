import { useState } from "react";
import axios from "axios";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Helpers ──────────────────────────────────────────────────────
function scoreClass(s) {
  if (s >= 0.65) return "score-high";
  if (s >= 0.55) return "score-mid";
  return "score-low";
}

function sourceLabel(s) {
  return { vehicle_specs: "VEHICLE SPECS", service_data: "SERVICE DATA", owner_manual: "OWNER MANUAL" }[s] || s.toUpperCase();
}

// ── Search Panel ─────────────────────────────────────────────────
function SearchPanel() {
  const [query, setQuery]     = useState("");
  const [filter, setFilter]   = useState("");
  const [topK, setTopK]       = useState(5);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true); setError(null); setResults(null);
    try {
      const { data } = await axios.post(`${API}/search`, {
        query, top_k: topK,
        source_filter: filter || null,
      });
      setResults(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to connect to backend.");
    } finally { setLoading(false); }
  }

  return (
    <>
      <h1 className="panel-title">Semantic Search</h1>
      <p className="panel-sub">Search across vehicle specs, service schedules, and owner manual using natural language.</p>

      <div className="input-row">
        <div className="input-wrap">
          <input className="input-field" placeholder='e.g. "Which Ford SUV has 7 seats?"'
            value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()} />
        </div>
        <button className="btn-primary" onClick={handleSearch} disabled={loading}>
          {loading ? <><span className="spinner" style={{width:14,height:14}} />Searching</> : "Search"}
        </button>
      </div>

      <div className="filter-row">
        <select className="select-field" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Sources</option>
          <option value="vehicle_specs">Vehicle Specs</option>
          <option value="service_data">Service Data</option>
          <option value="owner_manual">Owner Manual</option>
        </select>
        <select className="select-field" value={topK} onChange={e => setTopK(Number(e.target.value))}>
          {[3,5,8,10].map(n => <option key={n} value={n}>Top {n} results</option>)}
        </select>
      </div>

      {loading && <div className="loading"><div className="spinner" />Running semantic search...</div>}
      {error   && <div className="error-msg">⚠ {error}</div>}

      {results && (
        <>
          <div className="results-meta">{results.total_results} RESULTS FOR "{results.query.toUpperCase()}"</div>
          {results.results.map((r, i) => (
            <div className="card" key={i}>
              <div className="card-header">
                <span className="card-model">{r.model}</span>
                <span className={`score-badge ${scoreClass(r.score)}`}>{(r.score * 100).toFixed(1)}% match</span>
              </div>
              <div className="source-tag">{sourceLabel(r.source)}</div>
              <div className="card-text">{r.text}</div>
            </div>
          ))}
        </>
      )}

      {!loading && !error && !results && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <div className="empty-text">Enter a query to search the Ford knowledge base</div>
        </div>
      )}
    </>
  );
}

// ── Ask Panel ────────────────────────────────────────────────────
function AskPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult]     = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  const EXAMPLES = [
    "What does the engine oil pressure warning mean?",
    "What is the service interval for Ford Ranger?",
    "How do I jump start a Ford vehicle?",
    "Which Ford truck is best for towing?",
  ];

  async function handleAsk(q) {
    const q_ = q || question;
    if (!q_.trim()) return;
    setQuestion(q_);
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/ask`, { question: q_ });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to connect to backend.");
    } finally { setLoading(false); }
  }

  return (
    <>
      <h1 className="panel-title">Ask FVIS</h1>
      <p className="panel-sub">Ask anything about Ford vehicles. Answers are grounded in the knowledge base — no hallucinations.</p>

      <div className="input-row">
        <div className="input-wrap">
          <input className="input-field" placeholder='e.g. "What does the engine warning light mean?"'
            value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAsk()} />
        </div>
        <button className="btn-primary" onClick={() => handleAsk()} disabled={loading}>
          {loading ? <><span className="spinner" style={{width:14,height:14}} />Thinking</> : "Ask"}
        </button>
      </div>

      <div className="filter-row" style={{marginBottom: 28}}>
        {EXAMPLES.map((ex, i) => (
          <button key={i} className="select-field" style={{cursor:"pointer", fontSize:12}}
            onClick={() => handleAsk(ex)}>
            {ex}
          </button>
        ))}
      </div>

      {loading && <div className="loading"><div className="spinner" />Retrieving context and generating answer...</div>}
      {error   && <div className="error-msg">⚠ {error}</div>}

      {result && (
        <>
          <div className="answer-card">
            <div className="answer-label">▎ FVIS ANSWER</div>
            <div className="answer-text">{result.answer}</div>
            {result.sources_used?.length > 0 && (
              <div className="sources-list">
                {result.sources_used.map((s, i) => (
                  <span className="source-chip" key={i}>{s}</span>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {!loading && !error && !result && (
        <div className="empty-state">
          <div className="empty-icon">💬</div>
          <div className="empty-text">Ask a question or click an example above</div>
        </div>
      )}
    </>
  );
}

// ── Recommend Panel ──────────────────────────────────────────────
function RecommendPanel() {
  const [req, setReq]         = useState("");
  const [budget, setBudget]   = useState("");
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const EXAMPLES = [
    "I need a family SUV with 7 seats",
    "I want a pickup truck for towing",
    "Suggest an electric SUV",
    "Affordable hybrid with best mileage",
  ];

  async function handleRec(r) {
    const r_ = r || req;
    if (!r_.trim()) return;
    setReq(r_);
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/recommend`, {
        requirement: r_,
        budget_lakhs: budget ? parseFloat(budget) : null,
      });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to connect to backend.");
    } finally { setLoading(false); }
  }

  return (
    <>
      <h1 className="panel-title">Vehicle Recommender</h1>
      <p className="panel-sub">Describe what you need — the system matches your requirements to the best Ford vehicles.</p>

      <div className="input-row">
        <div className="input-wrap">
          <input className="input-field" placeholder='e.g. "I need a family SUV with 7 seats"'
            value={req} onChange={e => setReq(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleRec()} />
        </div>
        <div className="budget-wrap">
          <label>Budget (₹ Lakhs)</label>
          <input className="budget-input" type="number" placeholder="Any"
            value={budget} onChange={e => setBudget(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={() => handleRec()} disabled={loading}>
          {loading ? <><span className="spinner" style={{width:14,height:14}} />Matching</> : "Find"}
        </button>
      </div>

      <div className="filter-row" style={{marginBottom: 28}}>
        {EXAMPLES.map((ex, i) => (
          <button key={i} className="select-field" style={{cursor:"pointer", fontSize:12}}
            onClick={() => handleRec(ex)}>
            {ex}
          </button>
        ))}
      </div>

      {loading && <div className="loading"><div className="spinner" />Scoring vehicles against your requirements...</div>}
      {error   && <div className="error-msg">⚠ {error}</div>}

      {result && (
        <>
          <div className="results-meta">TOP MATCHES FOR "{result.requirement.toUpperCase()}"</div>
          <div className="rec-grid">
            {result.recommendations.map((r, i) => (
              <div className="rec-card" key={i}>
                <div className="rec-rank">RECOMMENDATION #{i + 1}</div>
                <div className="rec-model">{r.model}</div>
                <div className="rec-specs">
                  <div className="rec-spec"><span className="rec-spec-key">Body Style</span><span className="rec-spec-val">{r.body_style}</span></div>
                  <div className="rec-spec"><span className="rec-spec-key">Fuel Type</span><span className="rec-spec-val">{r.fuel_type}</span></div>
                  <div className="rec-spec"><span className="rec-spec-key">Seating</span><span className="rec-spec-val">{r.seating} seats</span></div>
                  <div className="rec-spec"><span className="rec-spec-key">Price</span><span className="rec-spec-val">₹{r.price_lakhs}L</span></div>
                </div>
                <hr className="rec-divider" />
                <span className="rec-reason-label">Why this vehicle</span>
                <div className="rec-reason">{r.reason.replace(/\|/g, "·")}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && !error && !result && (
        <div className="empty-state">
          <div className="empty-icon">🚗</div>
          <div className="empty-text">Describe your requirements or click an example</div>
        </div>
      )}
    </>
  );
}

// ── App Shell ────────────────────────────────────────────────────
const TABS = [
  { id: "search",    label: "Semantic Search",   icon: "🔍", desc: "Search vehicle knowledge base" },
  { id: "ask",       label: "Ask FVIS",           icon: "💬", desc: "RAG-powered Q&A assistant"    },
  { id: "recommend", label: "Recommender",        icon: "🚗", desc: "Find your ideal Ford vehicle" },
];

export default function App() {
  const [tab, setTab] = useState("search");

  return (
    <>
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">F</div>
          <div className="header-title">FVIS — <span>Ford</span> Vehicle Intelligence System</div>
        </div>
        <div className="header-badge">● SYSTEM ONLINE</div>
      </header>

      <div className="layout">
        <nav className="sidebar">
          <div className="sidebar-label">Navigation</div>
          {TABS.map(t => (
            <div key={t.id}>
              <button className={`tab-btn ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
                <span className="tab-icon">{t.icon}</span>
                {t.label}
              </button>
              <div className="tab-desc">{t.desc}</div>
            </div>
          ))}
        </nav>

        <main className="main">
          {tab === "search"    && <SearchPanel />}
          {tab === "ask"       && <AskPanel />}
          {tab === "recommend" && <RecommendPanel />}
        </main>
      </div>
    </>
  );
}