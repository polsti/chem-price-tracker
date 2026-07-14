import { useEffect, useState } from "react";
import PriceChart from "./components/PriceChart";
import "./App.css";

const API = "http://localhost:8000";

export default function App() {
  const [chemicals, setChemicals]   = useState([]);
  const [selected, setSelected]     = useState(null);
  const [history, setHistory]       = useState([]);
  const [activeDays, setActiveDays] = useState(30);   // default period: 1 month
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);

  // fetch latest prices for all chemicals on page load
  useEffect(() => {
    fetch(`${API}/chemicals`)
      .then(res => res.json())
      .then(data => {
        setChemicals(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Cannot reach API. Make sure the backend is running on port 8000.");
        setLoading(false);
      });
  }, []);

  // re-fetch history whenever selected chemical OR active period changes
  useEffect(() => {
    if (!selected) return;
    fetch(`${API}/chemicals/${selected.chemical_id}/history?days=${activeDays}`)
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

  if (loading) return <div className="center">Loading...</div>;
  if (error)   return <div className="center error">{error}</div>;

  return (
    <div className="container">
      <h1>Chemical Price Tracker</h1>
      <p className="subtitle">Click a row to see price history chart</p>

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
    </div>
  );
}
