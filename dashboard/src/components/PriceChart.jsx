import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

const PERIODS = [
  { label: "7 days",   days: 7   },
  { label: "1 month",  days: 30  },
  { label: "3 months", days: 90  },
  { label: "1 year",   days: 365 },
];

export default function PriceChart({ data, chemicalName, activeDays, onPeriodChange }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="chart-box">
      <div className="chart-header">
        <h2>{chemicalName} — price history</h2>

        {/* period buttons */}
        <div className="period-buttons">
          {PERIODS.map(p => (
            <button
              key={p.days}
              onClick={() => onPeriodChange(p.days)}
              className={activeDays === p.days ? "period-btn active" : "period-btn"}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey="date" tick={{ fill: "#aaa", fontSize: 12 }} />
          <YAxis tick={{ fill: "#aaa", fontSize: 12 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333" }}
            labelStyle={{ color: "#fff" }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#4fc3f7"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
