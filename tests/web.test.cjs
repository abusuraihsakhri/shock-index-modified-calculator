const test = require("node:test");
const assert = require("node:assert/strict");
const app = require("../web/app.js");

test("single case uses the published Age-SI formula", () => {
  const v = app.calculate({hr:80, sbp:120, dbp:80, age:50});
  assert.ok(Math.abs(v.si - 2/3) < 1e-12);
  assert.ok(Math.abs(v.map - (80+40/3)) < 1e-12);
  assert.ok(Math.abs(v.msi - 80/(80+40/3)) < 1e-12);
  assert.ok(Math.abs(v.age_si - 100/3) < 1e-12);
  assert.equal(v.reverse_si, 1.5);
});

test("optional DBP and age remain absent", () => {
  const v = app.calculate({hr:"90", sbp:"90"});
  assert.equal(v.si, 1);
  assert.equal(v.msi, null);
  assert.equal(v.age_si, null);
});

test("invalid and nonfinite values are rejected", () => {
  for (const v of [
    {hr:"",sbp:100}, {hr:0,sbp:100}, {hr:"Infinity",sbp:100},
    {hr:80,sbp:120,dbp:121}, {hr:80,sbp:120,dbp:-1},
    {hr:80,sbp:120,age:0}, {hr:80,sbp:120,age:"NaN"}
  ]) assert.throws(() => app.calculate(v));
});

test("quoted CSV fields, BOM and newlines are supported", () => {
  const rows = app.parseCsv('\uFEFFhr,sbp,note\r\n80,120,"a,b"\r\n100,90,"line 1\nline 2"\r\n');
  assert.deepEqual(rows, [
    ["hr","sbp","note"], ["80","120","a,b"], ["100","90","line 1\nline 2"]
  ]);
  assert.throws(() => app.parseCsv('hr,sbp\n"80,120'));
});

test("batch marks invalid rows and protects CSV output", () => {
  const result = app.processCsv('hr,sbp,note\n80,120,"=2+2"\n0,120,ignored\n');
  assert.equal(result.total, 2);
  assert.equal(result.success, 1);
  assert.match(result.output, /'=2\+2/);
  assert.match(result.output, /Heart rate must be a finite positive number/);
  assert.equal(result.summary[0].si, "0.667");
  assert.match(result.summary[1].status, /Heart rate/);
});

test("missing headers, duplicate columns, surplus records fail", () => {
  assert.throws(() => app.processCsv("pulse,sbp\n80,120"), /must contain/);
  assert.throws(() => app.processCsv("hr,HR,sbp\n80,90,120"), /unique/);
  assert.throws(() => app.processCsv("hr,sbp\n" + "80,120\n".repeat(2001)), /2,000/);
});
