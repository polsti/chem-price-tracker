import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

const API = "http://localhost:8000";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

async function fetchSummary(year, month) {
  const res = await fetch(`${API}/export/summary?year=${year}&month=${month}`);
  if (!res.ok) throw new Error("No data for this period");
  return res.json();
}

function buildRows(chemicals) {
  return chemicals.map(c => [
    c.chemical_name,
    c.first_date,
    c.last_date,
    c.trading_days,
    c.first_price?.toLocaleString() ?? "—",
    c.last_price?.toLocaleString()  ?? "—",
    c.min_price?.toLocaleString()   ?? "—",
    c.max_price?.toLocaleString()   ?? "—",
    c.avg_price?.toLocaleString()   ?? "—",
    c.change_pct != null ? `${c.change_pct > 0 ? "+" : ""}${c.change_pct}%` : "—",
  ]);
}

const HEADERS = [
  "Chemical", "From", "To", "Days",
  "Start price", "End price", "Min", "Max", "Avg", "Change %"
];

export default function ExportButton({ year, month }) {
  const label = `${MONTHS[month - 1]} ${year}`;

  const exportPDF = async () => {
    try {
      const data = await fetchSummary(year, month);
      const doc = new jsPDF({ orientation: "landscape" });

      doc.setFontSize(16);
      doc.text(`Chemical Price Summary — ${label}`, 14, 16);
      doc.setFontSize(10);
      doc.setTextColor(120);
      doc.text("Prices in CNY/tonne. Source: sci99.com", 14, 23);

      autoTable(doc, {
        head: [HEADERS],
        body: buildRows(data.chemicals),
        startY: 28,
        styles: { fontSize: 9 },
        headStyles: { fillColor: [30, 30, 30], textColor: 200 },
        alternateRowStyles: { fillColor: [245, 245, 245] },
      });

      doc.save(`chemical-summary-${year}-${String(month).padStart(2,"0")}.pdf`);
    } catch (e) {
      alert(e.message);
    }
  };

  const exportExcel = async () => {
    try {
      const data = await fetchSummary(year, month);
      const rows = buildRows(data.chemicals);

      const ws = XLSX.utils.aoa_to_sheet([HEADERS, ...rows]);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, label);

      // auto column widths
      ws["!cols"] = HEADERS.map((h, i) => ({
        wch: Math.max(h.length, ...rows.map(r => String(r[i]).length)) + 2
      }));

      XLSX.writeFile(wb, `chemical-summary-${year}-${String(month).padStart(2,"0")}.xlsx`);
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="export-group">
      <span className="export-label">Export {label}:</span>
      <button className="export-btn" onClick={exportPDF}>↓ PDF</button>
      <button className="export-btn" onClick={exportExcel}>↓ Excel</button>
    </div>
  );
}
