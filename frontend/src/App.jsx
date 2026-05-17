import React, { useState, useEffect } from 'react';
import { 
  Brain, FileText, Activity, AlertTriangle, ShieldAlert, 
  Database, Network, MessageSquare, BarChart3, LineChart, Server, Upload, Trash2, Play, Search, Loader2
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const API_BASE = 'https://neuralnexus-backend.onrender.com/api';

function App() {
  const [initialized, setInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState('query');
  const [loading, setLoading] = useState(false);

  // States for tabs
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [qualityData, setQualityData] = useState(null);
  const [contradictions, setContradictions] = useState(null);
  const [insights, setInsights] = useState(null);
  const [kgStats, setKgStats] = useState(null);
  const [lineageData, setLineageData] = useState(null);

  // Upload states
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadCred, setUploadCred] = useState(0.75);

  useEffect(() => {
    fetch('https://neuralnexus-backend.onrender.com/')
      .then(res => res.json())
      .then(data => {
        setInitialized(data.initialized);
      }).catch(err => console.error("API not reachable", err));
  }, []);

  const handleInitDemo = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/init_demo`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) setInitialized(true);
      else alert("Error: " + data.detail);
    } catch (e) {
      alert("Failed to connect to API");
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (uploadName) formData.append('source_name', uploadName);
    formData.append('credibility', uploadCred);
    
    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
      if (res.ok) {
        alert("File uploaded successfully! Run full analysis when ready.");
        setInitialized(true);
      } else {
        alert("Upload failed.");
      }
    } catch (e) {
      alert("Failed to connect to API");
    }
    setLoading(false);
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/analyze`, { method: 'POST' });
      if (res.ok) {
        alert("Full analysis complete!");
        // Refresh data
        setQualityData(null); setContradictions(null); setInsights(null);
        if (activeTab === 'quality') loadQualityDashboard();
        if (activeTab === 'conflict') loadContradictions();
        if (activeTab === 'alerts') loadInsights();
      } else {
        const data = await res.json();
        alert("Error: " + data.detail);
      }
    } catch (e) {
      alert("Failed to connect to API");
    }
    setLoading(false);
  };

  const handleClearData = async () => {
    if (!confirm("Are you sure you want to clear all data?")) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/clear`, { method: 'POST' });
      if (res.ok) {
        setInitialized(false);
        setChatHistory([]);
        setQualityData(null);
        setContradictions(null);
        setInsights(null);
        setActiveTab('query');
      }
    } catch (e) {
      alert("Failed to connect to API");
    }
    setLoading(false);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const newChat = { role: 'user', content: query };
    setChatHistory(prev => [...prev, newChat]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: newChat.content })
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        setChatHistory(prev => [...prev, { role: 'assistant', content: "Error: " + (errorData.detail || "Unknown error") }]);
        setLoading(false);
        return;
      }

      let assistantMessage = { role: 'assistant', content: '', meta: null };
      setChatHistory(prev => [...prev, assistantMessage]);
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;
      let buffer = '';
      
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // Keep the last incomplete line in buffer
          
          for (let line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);
              if (data.type === 'chunk') {
                assistantMessage.content += data.content;
              } else if (data.type === 'meta') {
                assistantMessage.meta = data.data;
              } else if (data.type === 'error') {
                assistantMessage.content += "\n\nError: " + data.content;
              }
              setChatHistory(prev => {
                const newHistory = [...prev];
                newHistory[newHistory.length - 1] = { ...assistantMessage };
                return newHistory;
              });
            } catch (e) {
              console.error("Error parsing chunk:", line);
            }
          }
        }
      }
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: "Failed to connect to API." }]);
    }
    setLoading(false);
  };

  const loadQualityDashboard = async () => {
    const res = await fetch(`${API_BASE}/quality_dashboard`);
    if (res.ok) setQualityData(await res.json());
  };

  const loadContradictions = async () => {
    const res = await fetch(`${API_BASE}/contradictions`);
    if (res.ok) setContradictions(await res.json());
  };

  const loadInsights = async () => {
    const res = await fetch(`${API_BASE}/proactive_insights`);
    if (res.ok) setInsights(await res.json());
  };

  const loadKgStats = async () => {
    const res = await fetch(`${API_BASE}/knowledge_graph`);
    if (res.ok) setKgStats(await res.json());
  };

  const loadLineage = async () => {
    const res = await fetch(`${API_BASE}/lineage`);
    if (res.ok) setLineageData(await res.json());
  };

  useEffect(() => {
    if (initialized) {
      if (activeTab === 'quality' && !qualityData) loadQualityDashboard();
      if (activeTab === 'conflict' && !contradictions) loadContradictions();
      if (activeTab === 'alerts' && !insights) loadInsights();
      if (activeTab === 'kg' && !kgStats) loadKgStats();
      if (activeTab === 'lineage' && !lineageData) loadLineage();
    }
  }, [activeTab, initialized]);

  const tabs = [
    { id: 'query', label: 'Intelligence Query', icon: <MessageSquare size={18} /> },
    { id: 'quality', label: 'Quality Dashboard', icon: <BarChart3 size={18} /> },
    { id: 'conflict', label: 'Contradictions', icon: <AlertTriangle size={18} /> },
    { id: 'alerts', label: 'Proactive Insights', icon: <ShieldAlert size={18} /> },
    { id: 'kg', label: 'Knowledge Graph', icon: <Network size={18} /> },
    { id: 'lineage', label: 'Data Lineage', icon: <FileText size={18} /> },
  ];

  return (
    <div className="min-h-screen bg-parchment-100 flex">
      {/* Sidebar */}
      <div className="w-64 bg-parchment-50 border-r border-parchment-200 p-6 flex flex-col z-10 shadow-[2px_0_10px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-3 mb-10">
          <Brain className="text-ink-900" size={28} />
          <div>
            <h1 className="font-serif font-semibold text-xl text-ink-950 tracking-tight">NeuralNexus</h1>
            <span className="text-xs font-bold tracking-widest uppercase">
              {initialized ? <span className="text-ink-500">Active</span> : <span className="text-crimson-600 opacity-70">Inactive</span>}
            </span>
          </div>
        </div>
        
        {initialized ? (
          <nav className="flex-1 space-y-2">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-md transition-colors text-sm font-medium
                  ${activeTab === t.id 
                    ? 'bg-ink-900 text-parchment-50 shadow-sm' 
                    : 'text-ink-700 hover:bg-parchment-200'}`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </nav>
        ) : (
          <div className="flex-1 flex flex-col justify-center text-ink-400 text-sm italic text-center px-4">
            Awaiting data ingestion or demo initialization to activate the intelligence fabric.
          </div>
        )}

        <div className="mt-auto pt-6 border-t border-parchment-200 text-xs text-ink-500 space-y-4">
          <form onSubmit={handleUpload} className="bg-parchment-100 p-3 rounded-md space-y-2 border border-parchment-200">
            <p className="font-semibold text-ink-900 mb-1 flex items-center gap-1"><Upload size={14}/> Upload Data</p>
            <input type="file" onChange={e => setUploadFile(e.target.files[0])} className="w-full text-[10px]" />
            <input type="text" placeholder="Source Name (opt)" value={uploadName} onChange={e => setUploadName(e.target.value)} className="w-full bg-parchment-50 border border-parchment-300 rounded px-2 py-1" />
            <div className="flex justify-between items-center">
              <span className="text-[10px]">Cred: {uploadCred}</span>
              <input type="range" min="0" max="1" step="0.05" value={uploadCred} onChange={e => setUploadCred(parseFloat(e.target.value))} className="w-16" />
            </div>
            <button type="submit" disabled={loading || !uploadFile} className="w-full bg-ink-900 text-parchment-50 rounded py-1 hover:bg-ink-800 transition-colors disabled:opacity-50">Ingest</button>
          </form>

          {initialized ? (
            <div className="flex gap-2">
              <button onClick={handleRunAnalysis} disabled={loading} className="flex-1 bg-ink-100 text-ink-900 border border-ink-300 rounded py-1.5 hover:bg-ink-200 transition-colors flex items-center justify-center gap-1">
                <Play size={12}/> Analyze
              </button>
              <button onClick={handleClearData} disabled={loading} className="bg-crimson-100 text-crimson-900 border border-crimson-300 rounded px-2 py-1.5 hover:bg-crimson-200 transition-colors">
                <Trash2 size={12}/>
              </button>
            </div>
          ) : (
            <div className="space-y-2 text-center">
              <p className="text-[11px] text-ink-400 italic">Or load demo data to start quickly.</p>
              <button 
                onClick={handleInitDemo} 
                disabled={loading}
                className="w-full bg-ink-100 text-ink-900 border border-ink-300 py-2 rounded-md hover:bg-ink-200 transition-colors flex items-center justify-center gap-2 font-medium shadow-sm"
              >
                {loading ? <Loader2 className="animate-spin" size={14}/> : <Database size={14}/>}
                Init Demo Data
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-10 overflow-y-auto">
        {!initialized ? (
          <div className="h-full flex flex-col justify-center max-w-4xl mx-auto space-y-16">
            <div className="text-center space-y-4">
              <h1 className="text-6xl font-serif text-ink-950 font-semibold tracking-tight flex justify-center items-center gap-4">
                <Brain className="text-ink-800" size={56} />
                Neural<span className="text-ink-500">Nexus</span>
              </h1>
              <p className="text-xl text-ink-700 font-serif italic max-w-2xl mx-auto leading-relaxed">
                Autonomous Financial Intelligence Fabric — 5 AI agents that detect contradictions, reconcile conflicts, forecast risks, and audit every answer with full data lineage.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="book-card border-t-4 border-t-ink-800">
                <h4 className="font-serif font-bold text-ink-900 mb-2 flex items-center gap-2"><AlertTriangle size={16}/> Contradiction Detection</h4>
                <p className="text-sm text-ink-600">Finds when your data sources disagree and reconciles conflicts with AI reasoning.</p>
              </div>
              <div className="book-card border-t-4 border-t-ink-600">
                <h4 className="font-serif font-bold text-ink-900 mb-2 flex items-center gap-2"><BarChart3 size={16}/> Quality Scoring</h4>
                <p className="text-sm text-ink-600">Completeness, consistency, and timeliness scoring for every data source.</p>
              </div>
              <div className="book-card border-t-4 border-t-parchment-600">
                <h4 className="font-serif font-bold text-ink-900 mb-2 flex items-center gap-2"><LineChart size={16}/> Proactive Forecasting</h4>
                <p className="text-sm text-ink-600">Trend analysis, risk scoring, and proactive alerts — without being asked.</p>
              </div>
              <div className="book-card border-t-4 border-t-ink-400">
                <h4 className="font-serif font-bold text-ink-900 mb-2 flex items-center gap-2"><Network size={16}/> Knowledge Graph</h4>
                <p className="text-sm text-ink-600">Auto-extracted entities and relations with contradiction edges.</p>
              </div>
            </div>

            <div className="text-center text-ink-500 italic bg-parchment-200 py-4 px-6 rounded-lg inline-block mx-auto border border-parchment-300">
              👈 Use the sidebar to upload a file or initialize the system with demo data.
            </div>
          </div>
        ) : (
          <div className="max-w-5xl mx-auto space-y-8">
          
          {/* Query Tab */}
          {activeTab === 'query' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-serif text-ink-950">Intelligence Query</h2>
                <p className="text-ink-600 mt-2">Ask anything about your enterprise data. The system automatically reasons, validates, and reviews before answering.</p>
              </div>

              <div className="flex gap-4">
                {["What is our Q3 revenue and should I trust it?", "Show me all contradictions in our financial data", "What anomalies and risks should we watch for next quarter?"].map((q, i) => (
                  <button 
                    key={i} 
                    onClick={() => setQuery(q)}
                    className="flex-1 text-xs bg-parchment-50 border border-parchment-200 hover:border-ink-400 hover:shadow-sm rounded-md p-3 text-left transition-all text-ink-700"
                  >
                    <Search size={14} className="inline mr-2 text-ink-400" />
                    {q}
                  </button>
                ))}
              </div>
              
              <div className="book-card min-h-[400px] flex flex-col">
                <div className="flex-1 space-y-6 mb-6 overflow-y-auto pr-4">
                  {chatHistory.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-ink-400">
                      <MessageSquare size={48} className="mb-4 opacity-50" />
                      <p>Start a conversation with the intelligence fabric.</p>
                    </div>
                  ) : (
                    chatHistory.map((msg, i) => (
                      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-4 ${msg.role === 'user' ? 'bg-ink-900 text-parchment-50' : 'bg-parchment-200 text-ink-900'}`}>
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                          {msg.meta && (
                            <div className="mt-3 pt-3 border-t border-ink-300/30 text-xs flex gap-4">
                              <span>Confidence: {(msg.meta.confidence * 100).toFixed(0)}%</span>
                              <span>Sources: {msg.meta.sources?.length || 0}</span>
                              <span className={msg.meta.contradictions_found > 0 ? "text-crimson-600 font-semibold" : ""}>
                                Conflicts: {msg.meta.contradictions_found}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                  {loading && (
                    <div className="flex items-center gap-2 text-ink-500 text-sm">
                      <Loader2 className="animate-spin" size={16} /> Orchestrating agents...
                    </div>
                  )}
                </div>
                
                <form onSubmit={handleQuery} className="relative mt-auto">
                  <input 
                    type="text" 
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder="E.g. What is our Q3 revenue and should I trust it?"
                    className="w-full bg-parchment-100 border border-parchment-300 rounded-md py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent text-sm shadow-inner"
                  />
                  <button type="submit" disabled={loading} className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-500 hover:text-ink-900">
                    <MessageSquare size={18} />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Quality Dashboard Tab */}
          {activeTab === 'quality' && (
            <div className="space-y-6">
               <div>
                <h2 className="text-3xl font-serif text-ink-950">Quality Dashboard</h2>
                <p className="text-ink-600 mt-2">Automated completeness, consistency, and timeliness scoring for all ingested data sources.</p>
              </div>
              
              {!qualityData ? (
                <div className="flex justify-center p-12"><Activity className="animate-spin text-ink-500" /></div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {qualityData.reports.slice(0, 3).map((rpt, i) => (
                      <div key={i} className="book-card flex flex-col items-center text-center">
                        <span className="text-sm text-ink-500 mb-2 truncate w-full">{rpt.source_name}</span>
                        <span className="text-4xl font-serif text-ink-900">{rpt.overall_score.toFixed(0)}</span>
                        <span className="text-xs font-medium uppercase tracking-widest text-ink-400 mt-1">Grade {rpt.grade}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="book-card h-80 pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={qualityData.reports} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e1d5c2" vertical={false} />
                        <XAxis dataKey="source_name" axisLine={false} tickLine={false} tick={{fill: '#7c6148', fontSize: 12}} />
                        <YAxis axisLine={false} tickLine={false} tick={{fill: '#7c6148', fontSize: 12}} domain={[0, 100]} />
                        <Tooltip contentStyle={{backgroundColor: '#fbfaf8', borderColor: '#eee8dd', borderRadius: '8px'}} />
                        <Legend wrapperStyle={{fontSize: '12px', paddingTop: '10px'}} />
                        <Bar dataKey="completeness_score" name="Completeness" fill="#36475a" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="consistency_score" name="Consistency" fill="#c2a581" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="timeliness_score" name="Timeliness" fill="#644e3b" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Contradictions Tab */}
          {activeTab === 'conflict' && (
            <div className="space-y-6">
               <div className="flex justify-between items-end">
                <div>
                  <h2 className="text-3xl font-serif text-ink-950">Cross-Source Contradictions</h2>
                  <p className="text-ink-600 mt-2">Conflicts automatically detected across data sets, prioritized by severity.</p>
                </div>
              </div>

              {!contradictions ? (
                <div className="flex justify-center p-12"><Activity className="animate-spin text-ink-500" /></div>
              ) : (
                <div className="space-y-4">
                  {contradictions.contradictions.length === 0 ? (
                    <div className="book-card text-center text-ink-500 py-12">No contradictions found across data sources.</div>
                  ) : (
                    contradictions.contradictions.map((c, i) => (
                      <div key={i} className="book-card border-l-4 border-l-crimson-600">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="font-semibold text-ink-900 flex items-center gap-2">
                            <AlertTriangle size={16} className={c.severity === 'high' ? 'text-crimson-600' : 'text-parchment-600'} />
                            {c.entity} → {c.attribute}
                          </h3>
                          <span className="text-xs font-bold uppercase tracking-widest text-crimson-600 bg-crimson-50 px-2 py-1 rounded">
                            {c.severity} severity
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-parchment-100 p-3 rounded border border-parchment-200">
                            <div className="text-xs text-ink-500 mb-1">{c.source_a_name}</div>
                            <div className="font-mono text-sm break-all">{String(c.source_a_value)}</div>
                          </div>
                          <div className="bg-parchment-100 p-3 rounded border border-parchment-200">
                            <div className="text-xs text-ink-500 mb-1">{c.source_b_name}</div>
                            <div className="font-mono text-sm break-all">{String(c.source_b_value)}</div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* Alerts Tab */}
          {activeTab === 'alerts' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-serif text-ink-950">Proactive Insights</h2>
                <p className="text-ink-600 mt-2">Insights surfaced autonomously by the Validator and Forecaster agents.</p>
              </div>

              {!insights ? (
                <div className="flex justify-center p-12"><Activity className="animate-spin text-ink-500" /></div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="book-card col-span-1 md:col-span-2 prose prose-sm max-w-none text-ink-800">
                    <h3 className="font-serif text-xl mb-4 border-b border-parchment-200 pb-2 flex items-center gap-2">
                      <AlertTriangle size={18}/> Anomaly Detection
                    </h3>
                    <div className="whitespace-pre-wrap leading-relaxed">{insights.insights.anomalies || "No anomalies detected."}</div>
                    
                    {insights.insights.anomaly_analysis && (
                      <div className="mt-4 p-4 bg-parchment-100 rounded-md border border-parchment-200 whitespace-pre-wrap italic">
                        <strong>AI Root-Cause Analysis:</strong><br/>
                        {insights.insights.anomaly_analysis}
                      </div>
                    )}
                  </div>

                  <div className="book-card col-span-1 md:col-span-2 prose prose-sm max-w-none text-ink-800">
                    <h3 className="font-serif text-xl mb-4 border-b border-parchment-200 pb-2 flex items-center gap-2">
                      <LineChart size={18}/> Trend Forecast
                    </h3>
                    <div className="whitespace-pre-wrap leading-relaxed">{insights.insights.forecast || "No forecast available."}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* KG Tab */}
          {activeTab === 'kg' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-serif text-ink-950">Knowledge Graph</h2>
                <p className="text-ink-600 mt-2">Entities, relationships, and contradiction edges extracted and visualized automatically.</p>
              </div>

              {!kgStats ? (
                <div className="flex justify-center p-12"><Activity className="animate-spin text-ink-500" /></div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="book-card text-center"><p className="text-sm text-ink-500">Entities</p><p className="text-4xl font-serif text-ink-900">{kgStats.stats?.total_entities || 0}</p></div>
                  <div className="book-card text-center"><p className="text-sm text-ink-500">Relations</p><p className="text-4xl font-serif text-ink-900">{kgStats.stats?.total_relations || 0}</p></div>
                  <div className="book-card text-center"><p className="text-sm text-ink-500">Contradictions</p><p className="text-4xl font-serif text-ink-900">{kgStats.stats?.contradiction_count || 0}</p></div>
                  <div className="book-card text-center"><p className="text-sm text-ink-500">Components</p><p className="text-4xl font-serif text-ink-900">{kgStats.stats?.connected_components || 0}</p></div>
                  
                  <div className="book-card col-span-2 md:col-span-4 mt-6">
                     <p className="text-ink-600 text-center py-12 border border-dashed border-parchment-300 rounded-lg">
                       PyVis interactive graph rendering is processed in Python.<br/>
                       <i>(This dashboard displays aggregate statistical graph data extracted via the API)</i>
                     </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Lineage Tab */}
          {activeTab === 'lineage' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-3xl font-serif text-ink-950">Data Lineage</h2>
                <p className="text-ink-600 mt-2">Every fact in every answer is traceable to the exact source file, row, and quality score.</p>
              </div>

              {!lineageData ? (
                <div className="flex justify-center p-12"><Activity className="animate-spin text-ink-500" /></div>
              ) : (
                <div className="space-y-6">
                  <h3 className="font-serif text-xl border-b border-parchment-200 pb-2">Ingested Sources</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {lineageData.sources?.map((s, i) => (
                      <div key={i} className="book-card p-4">
                        <div className="font-semibold text-ink-900 mb-1 flex items-center justify-between">
                          <span className="truncate pr-4">{s.name}</span>
                          <span className="text-[10px] font-bold bg-ink-200 text-ink-800 px-2 py-0.5 rounded uppercase tracking-wider">{s.type}</span>
                        </div>
                        <div className="text-xs text-ink-500 space-y-1 mt-3">
                          <p>Rows Indexed: <strong className="text-ink-700">{s.rows}</strong></p>
                          <p>Credibility Assigned: <strong className="text-ink-700">{(s.credibility * 100).toFixed(0)}%</strong></p>
                          <p>Ingested At: <span className="font-mono text-ink-600">{s.ingested || 'Unknown'}</span></p>
                        </div>
                      </div>
                    ))}
                    {(!lineageData.sources || lineageData.sources.length === 0) && (
                      <p className="text-ink-500">No sources ingested yet.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
        )}
      </div>
    </div>
  );
}

export default App;
