import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from "recharts";

const API = "http://localhost:8000";

// distinct colors — maximally different from each other
const COLORS = [
  "#4fc3f7", // sky blue
  "#ff5252", // red
  "#69f0ae", // mint green
  "#ffd740", // yellow
  "#e040fb", // magenta
  "#ff6d00", // deep orange
  "#40c4ff", // light blue  — paired with different dash so it's distinct from sky blue
  "#b2ff59", // light green — paired with different dash so it's distinct from mint
];

// different dash patterns per line — solid, dashed, dotted, dash-dot...
const DASHES = [
  "0",        // solid
  "6 3",      // dashed
  "2 3",      // dotted
  "8 3 2 3",  // dash-dot
  "0",        // solid (different color)
  "6 3",      // dashed (different color)
  "2 3",      // dotted (different color)
  "8 3 2 3",  // dash-dot (different color)
];

const PERIODS = [
  { label: "7 days",   days: 7   },
  { label: "1 month",  days: 30  },
  { label: "3 months", days: 90  },
  { label: "1 year",   days: 365 },
];

export default function CompareChart({ chemicals }) {
  const [selected, setSelected] = useState([]);  // list of chemical objects chosen for comparison
  const [days, setDays]         = useState(30);
  const [chartData, setChartData] = useState([]);

  // whenever selected chemicals or period changes — fetch all their histories and merge
  useEffect(() => {
    if (selected.length === 0) {
      setChartData([]);
      return;
    }

    Promise.all(
      selected.map(chem =>
        fetch(`${API}/chemicals/${chem.chemical_id}/history?days=${days}`)
          .then(res => res.json())
          .then(data => ({ name: chem.chemical_name, data }))
      )
    ).then(results => {
      // merge all results into one array keyed by date
      const merged = {};
      results.forEach(({ name, data }) => {
        data.forEach(row => {
          if (!merged[row.date]) merged[row.date] = { date: row.date };
          merged[row.date][name] = row.price;
        });
      });
      // sort by date ascending
      const sorted = Object.values(merged).sort((a, b) =>
        a.date.localeCompare(b.date)
      );
      setChartData(sorted);
    });
  }, [selected, days]);

  const toggleChemical = (chem) => {
    const isSelected = selected.some(s => s.chemical_id === chem.chemical_id);
    if (isSelected) {
      // remove it
      setSelected(selected.filter(s => s.chemical_id !== chem.chemical_id));
    } else {
      // add it (max 8)
      if (selected.length < 8) setSelected([...selected, chem]);
    }
  };

  const isSelected = (chem) => selected.some(s => s.chemical_id === chem.chemical_id);

  return (
    <div className="compare-box">
      <h2>Compare chemicals</h2>
      <p className="subtitle">Select 2–8 chemicals to compare on the same chart</p>

      {/* chemical toggle buttons */}
      <div className="compare-toggles">
        {chemicals.map((chem, i) => (
          <button
            key={chem.chemical_id}
            onClick={() => toggleChemical(chem)}
            className="compare-toggle"
            style={isSelected(chem) ? {
              borderColor: COLORS[selected.findIndex(s => s.chemical_id === chem.chemical_id)],
              color: COLORS[selected.findIndex(s => s.chemical_id === chem.chemical_id)],
              background: "#1a1a1a",
            } : {}}
          >
            {chem.chemical_name}
          </button>
        ))}
      </div>

      {/* period buttons */}
      {selected.length >= 2 && (
        <>
          <div className="period-buttons" style={{ marginBottom: "20px" }}>
            {PERIODS.map(p => (
              <button
                key={p.days}
                onClick={() => setDays(p.days)}
                className={days === p.days ? "period-btn active" : "period-btn"}
              >
                {p.label}
              </button>
            ))}
          </div>

          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="date" tick={{ fill: "#aaa", fontSize: 11 }} />
              <YAxis tick={{ fill: "#aaa", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333" }}
                labelStyle={{ color: "#fff" }}
              />
              <Legend wrapperStyle={{ color: "#aaa", fontSize: 13 }} />
              {selected.map((chem, i) => (
                <Line
                  key={chem.chemical_id}
                  type="monotone"
                  dataKey={chem.chemical_name}
                  stroke={COLORS[i]}
                  strokeWidth={2}
                  strokeDasharray={DASHES[i]}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </>
      )}

      {selected.length === 1 && (
        <p className="compare-hint">Select at least one more chemical to compare</p>
      )}
    </div>
  );
}
