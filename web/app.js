/* Browser-only calculator. No external APIs or patient-data transmission. */
(function (root) {
  "use strict";

  function numberField(value, name, optional, allowZero) {
    if (value === undefined || value === null || String(value).trim() === "") {
      if (optional) return null;
      throw new Error(name + " is required.");
    }
    if (typeof value === "boolean") throw new Error(name + " must be numeric.");
    var n = Number(value);
    if (!Number.isFinite(n) || (allowZero ? n < 0 : n <= 0)) {
      throw new Error(name + " must be a finite " + (allowZero ? "non-negative" : "positive") + " number.");
    }
    return n;
  }

  function calculate(values) {
    var hr = numberField(values.hr, "Heart rate", false, false);
    var sbp = numberField(values.sbp, "Systolic BP", false, false);
    var dbp = numberField(values.dbp, "Diastolic BP", true, true);
    var age = numberField(values.age, "Age", true, false);
    if (dbp !== null && dbp > sbp) throw new Error("Diastolic BP cannot exceed systolic BP.");
    var si = hr / sbp;
    var map = dbp === null ? null : dbp + (sbp - dbp) / 3;
    var msi = map === null ? null : hr / map;
    var rsi = sbp / hr;
    var ageSi = age === null ? null : age * si;
    if ([si, rsi, map, msi, ageSi].some(function (x) { return x !== null && !Number.isFinite(x); })) {
      throw new Error("Input magnitudes produced an out-of-range calculation.");
    }
    return { si: si, msi: msi, map: map, age_si: ageSi, reverse_si: rsi, age: age };
  }

  function parseCsv(text) {
    if (typeof text !== "string") throw new Error("CSV content must be text.");
    var rows = [];
    var row = [];
    var cell = "";
    var quoted = false;
    var afterQuote = false;
    var source = text.replace(/^\uFEFF/, "");
    for (var i = 0; i < source.length; i++) {
      var ch = source[i];
      if (quoted) {
        if (ch === '"' && source[i + 1] === '"') { cell += '"'; i++; }
        else if (ch === '"') { quoted = false; afterQuote = true; }
        else { cell += ch; }
      } else if (ch === ',' || ch === '\n' || ch === '\r') {
        row.push(cell);
        cell = "";
        afterQuote = false;
        if (ch !== ',') {
          if (ch === '\r' && source[i + 1] === '\n') i++;
          if (row.some(function (x) { return x !== ""; })) rows.push(row);
          row = [];
        }
      } else if (ch === '"') {
        if (cell !== "" || afterQuote) throw new Error("Malformed CSV quote at character " + (i + 1) + ".");
        quoted = true;
      } else {
        if (afterQuote) throw new Error("Unexpected characters after a CSV quoted field.");
        cell += ch;
      }
    }
    if (quoted) throw new Error("Unclosed quoted field in CSV.");
    row.push(cell);
    if (row.some(function (x) { return x !== ""; })) rows.push(row);
    return rows;
  }

  function safeSpreadsheetCell(value) {
    var s = value === null || value === undefined ? "" : String(value);
    return /^[\s]*[=+\-@]/.test(s) ? "'" + s : s;
  }

  function toCsv(rows) {
    return rows.map(function (row) {
      return row.map(function (value) {
        var cell = safeSpreadsheetCell(value);
        return /[",\r\n]/.test(cell) ? '"' + cell.replace(/"/g, '""') + '"' : cell;
      }).join(",");
    }).join("\r\n") + "\r\n";
  }

  function processCsv(text) {
    var parsed = parseCsv(text);
    if (!parsed.length) throw new Error("CSV is empty.");
    var headers = parsed[0].map(function (name) { return name.trim(); });
    var normalized = headers.map(function (name) { return name.toLowerCase(); });
    if (headers.some(function (name) { return !name; }) || new Set(normalized).size !== normalized.length) {
      throw new Error("CSV column names must be nonempty and unique.");
    }
    var hrCol = normalized.indexOf("hr");
    if (hrCol < 0) hrCol = normalized.indexOf("heart_rate");
    var sbpCol = normalized.indexOf("sbp");
    if (hrCol < 0 || sbpCol < 0) throw new Error("CSV must contain 'hr' (or 'heart_rate') and 'sbp'.");
    var dbpCol = normalized.indexOf("dbp");
    var ageCol = normalized.indexOf("age");
    if (parsed.length > 2001) throw new Error("CSV contains more than 2,000 records.");

    var outputHeaders = headers.concat(["shock_index", "modified_si", "map_mmhg", "age_adjusted_si", "reverse_si", "error"]);
    var out = [outputHeaders];
    var summary = [];
    var ok = 0;
    for (var r = 1; r < parsed.length; r++) {
      var original = parsed[r].slice();
      var result = ["", "", "", "", "", ""];
      try {
        if (original.length !== headers.length) throw new Error("Row has " + original.length + " fields; expected " + headers.length + ".");
        var values = calculate({
          hr: original[hrCol],
          sbp: original[sbpCol],
          dbp: dbpCol < 0 ? null : original[dbpCol],
          age: ageCol < 0 ? null : original[ageCol]
        });
        result = [
          values.si.toFixed(3),
          values.msi === null ? "" : values.msi.toFixed(3),
          values.map === null ? "" : values.map.toFixed(1),
          values.age_si === null ? "" : values.age_si.toFixed(3),
          values.reverse_si.toFixed(3),
          ""
        ];
        ok++;
      } catch (err) {
        result[5] = err.message;
      }
      var padded = original.slice(0, headers.length);
      while (padded.length < headers.length) padded.push("");
      out.push(padded.concat(result));
      summary.push({row: r + 1, si: result[0], msi: result[1], ageSi: result[3], status: result[5] || "Calculated"});
    }
    return { output: toCsv(out), summary: summary, success: ok, total: parsed.length - 1 };
  }

  var calculator = { calculate: calculate, parseCsv: parseCsv, processCsv: processCsv, toCsv: toCsv };
  if (typeof module !== "undefined" && module.exports) module.exports = calculator;
  if (typeof document === "undefined") return;

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("calculator");
    if (!form) return;
    var errorBox = document.getElementById("form-error");
    var status = document.getElementById("result-status");
    var interpretation = document.getElementById("interpretation");
    var download = document.getElementById("download-csv");
    var fileInput = document.getElementById("csv-file");
    var batchMessage = document.getElementById("batch-message");
    var tbody = document.querySelector("#preview tbody");
    var csvData = null;

    function setText(id, value) { document.getElementById(id).textContent = value; }
    function format(value, digits) { return value === null ? "—" : value.toFixed(digits); }
    function clearResults() {
      ["out-si", "out-msi", "out-map", "out-age", "out-rsi"].forEach(function (id) { setText(id, "—"); });
      interpretation.textContent = "";
      status.textContent = "Invalid input";
    }
    function render() {
      try {
        var result = calculate({
          hr: document.getElementById("hr").value,
          sbp: document.getElementById("sbp").value,
          dbp: document.getElementById("dbp").value,
          age: document.getElementById("age").value
        });
        errorBox.hidden = true;
        errorBox.textContent = "";
        status.textContent = "Calculated";
        setText("out-si", format(result.si, 3));
        setText("out-msi", format(result.msi, 3));
        setText("out-map", format(result.map, 1));
        setText("out-age", format(result.age_si, 3));
        setText("out-rsi", format(result.reverse_si, 3));

        var statements = [];
        if (result.age !== null && result.age < 18) {
          statements.push("Pediatric result: adult interpretive SI ranges are not applicable.");
        } else if (result.si > 0.9) {
          statements.push("SI exceeds 0.9, a commonly studied adult threshold; this alone does not identify a diagnosis.");
        } else {
          statements.push("SI should be interpreted alongside clinical findings; a lower value does not exclude serious illness.");
        }
        if (result.msi !== null && (result.msi < 0.7 || result.msi > 1.3)) {
          statements.push("MSI lies outside 0.7–1.3, a range studied in emergency department cohorts.");
        }
        interpretation.textContent = statements.join(" ");
      } catch (err) {
        clearResults();
        errorBox.textContent = err.message;
        errorBox.hidden = false;
      }
    }

    form.addEventListener("submit", function (event) { event.preventDefault(); render(); });
    document.getElementById("reset").addEventListener("click", function () {
      form.reset();
      render();
    });
    fileInput.addEventListener("change", async function () {
      csvData = null;
      download.disabled = true;
      tbody.replaceChildren();
      if (!fileInput.files || !fileInput.files[0]) { batchMessage.textContent = "No file selected."; return; }
      var file = fileInput.files[0];
      if (file.size > 2 * 1024 * 1024) {
        batchMessage.textContent = "File exceeds 2 MB limit.";
        return;
      }
      try {
        var data = processCsv(await file.text());
        csvData = data.output;
        download.disabled = false;
        batchMessage.textContent = data.success + " of " + data.total + " records calculated; " + (data.total - data.success) + " invalid.";
        data.summary.slice(0, 10).forEach(function (record) {
          var tr = document.createElement("tr");
          [record.row, record.si || "—", record.msi || "—", record.ageSi || "—", record.status].forEach(function (value) {
            var td = document.createElement("td");
            td.textContent = String(value);
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
        if (!data.summary.length) {
          var tr = document.createElement("tr");
          var td = document.createElement("td");
          td.colSpan = 5;
          td.textContent = "The CSV contains headers but no records.";
          tr.appendChild(td);
          tbody.appendChild(tr);
        }
      } catch (err) {
        batchMessage.textContent = err.message;
      }
    });
    download.addEventListener("click", function () {
      if (csvData === null) return;
      var url = URL.createObjectURL(new Blob(["\uFEFF", csvData], {type: "text/csv;charset=utf-8"}));
      var link = document.createElement("a");
      link.href = url;
      link.download = "shock-index-results.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
    render();
  });
})(typeof window === "undefined" ? globalThis : window);
