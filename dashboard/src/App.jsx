import { useEffect, useState } from "react";
import PriceChart from "./components/PriceChart";
import CompareChart from "./components/CompareChart";
import ExportButton from "./components/ExportButton";
import Login from "./components/Login";
import { supabase, authFetch } from "./supabaseClient";
import "./App.css";

// Falls back to localhost for local development; set VITE_API_URL in
// Vercel's project settings to point the deployed site at the real backend.
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  // session === undefined  → we haven't checked yet (show nothing/a loader)
  // session === null       → checked, nobody's logged in (show Login)
  // session === {...}      → logged in (show the dashboard)
  const [session, setSession] = useState(undefined);

  const [chemicals, setChemicals]   = useState([]);
  const [selected, setSelected]     = useState(null);
  const [history, setHistory]       = useState([]);
  const [activeDays, setActiveDays] = useState(30);   // default period: 1 month
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);

  // On page load: check if there's already a logged-in session (e.g. from
  // a previous visit). Then keep listening for login/logout events so the
  // screen updates immediately without needing a page refresh.
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  // fetch latest prices for all chemicals — only once we know who's logged in
  useEffect(() => {
    if (!session) return;
    authFetch(`${API}/chemicals`)
      .then(res => res.json())
      .then(data => {
        setChemicals(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Cannot reach API. Make sure the backend is running on port 8000.");
        setLoading(false);
      });
  }, [session]);

  // re-fetch history whenever selected chemical OR active period changes
  useEffect(() => {
    if (!selected) return;
    authFetch(`${API}/chemicals/${selected.chemical_id}/history?days=${activeDays}`)
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(() => setHistory([]));
  }, [selected, activeDays]);  // ← both dependencies listed here

  const handleSelectChemical = (chem) => {
    setSelected(chem);
    setActiveDays(30);   // reset to 1 month when switching to a different chemical
    setHistory([]);
  };

  const changeColor = (val) => {
    if (val > 0) return "positive";
    if (val < 0) return "negative";
    return "";
  };

  // Still checking whether a session already exists (page just loaded)
  if (session === undefined) return <div className="center">Loading...</div>;

  // Checked, and nobody's logged in — show the login form instead of any data
  if (session === null) return <Login />;

  if (loading) return <div className="center">Loading...</div>;
  if (error)   return <div className="center error">{error}</div>;

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <h1>Chemical Price Tracker</h1>
          <p className="subtitle">Click a row to see price history chart</p>
        </div>
        <div className="header-actions">
          <span className="logged-in-as">{session.user.email}</span>
          <button className="logout-btn" onClick={() => supabase.auth.signOut()}>
            Log out
          </button>
          <ExportButton year={new Date().getFullYear()} month={new Date().getMonth() + 1} />
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Chemical</th>
            <th>Date</th>
            <th>Price (CNY/t)</th>
            <th>Change</th>
            <th>Change %</th>
            <th>7d Average</th>
          </tr>
        </thead>
        <tbody>
          {chemicals.map(chem => (
            <tr
              key={chem.chemical_id}
              onClick={() => handleSelectChemical(chem)}
              className={selected?.chemical_id === chem.chemical_id ? "active" : ""}
            >
              <td>{chem.chemical_name}</td>
              <td>{chem.date}</td>
              <td>{chem.price.toLocaleString()}</td>
              <td className={changeColor(chem.change_abs)}>
                {chem.change_abs > 0 ? "+" : ""}{chem.change_abs}
              </td>
              <td className={changeColor(chem.change_pct)}>
                {chem.change_pct > 0 ? "+" : ""}{chem.change_pct}%
              </td>
              <td>{chem.avg_price_7d.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <PriceChart
          data={history}
          chemicalName={selected.chemical_name}
          activeDays={activeDays}
          onPeriodChange={setActiveDays}
        />
      )}

      <CompareChart chemicals={chemicals} />
    </div>
  );
}
