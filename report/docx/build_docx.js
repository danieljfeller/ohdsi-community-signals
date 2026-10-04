const fs = require("fs"); const path = require("path");
const { Document, Packer, Paragraph, TextRun, ImageRun, HeadingLevel, AlignmentType, LevelFormat, BorderStyle, ShadingType, ExternalHyperlink } = require(process.argv[2] + "/node_modules/docx");
const ROOT = "/Users/daniel/Code/ohdsi-community-signals";
const blocks = JSON.parse(fs.readFileSync(path.join(ROOT, "report/docx/content.json"), "utf8"));
const FONT = "Georgia", SANS = "Calibri";
const runs = (rs, base = {}) => rs.map(r => r.link
  ? new ExternalHyperlink({ link: r.link, children: [new TextRun({ text: r.t, style: "Hyperlink", font: base.font || FONT, size: base.size || 22 })] })
  : new TextRun({ text: r.t, bold: !!r.b, italics: !!r.i, font: base.font || FONT, size: base.size || 22, color: base.color }));
const children = []; let figN = 0;
for (const b of blocks) {
  switch (b.k) {
    case "kicker": children.push(new Paragraph({ children: runs(b.runs, { font: SANS, size: 18, color: "555555" }), spacing: { after: 120 } })); break;
    case "title": children.push(new Paragraph({ children: runs(b.runs, { size: 40 }), spacing: { after: 200 } })); break;
    case "standfirst": children.push(new Paragraph({ children: runs(b.runs, { size: 26, color: "444444" }), spacing: { after: 160 } })); break;
    case "byline": children.push(new Paragraph({ children: [new TextRun({ text: b.text, font: SANS, size: 18, color: "777777" })], spacing: { after: 320 } })); break;
    case "abstract":
      children.push(new Paragraph({ children: [new TextRun({ text: "Abstract", font: SANS, size: 20, bold: true })], border: { top: { style: BorderStyle.SINGLE, size: 6, color: "222222" } }, spacing: { before: 200, after: 120 } }));
      for (const it of b.items) children.push(new Paragraph({ children: [new TextRun({ text: it.h + ". ", bold: true, font: FONT, size: 20 }), ...runs(it.runs, { size: 20 })], spacing: { after: 100 } }));
      children.push(new Paragraph({ children: [], border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" } }, spacing: { after: 240 } })); break;
    case "h2": children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(b.runs, { size: 30 }), spacing: { before: 360, after: 140 } })); break;
    case "h3": children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(b.runs, { size: 24 }), spacing: { before: 240, after: 100 } })); break;
    case "p": children.push(new Paragraph({ children: runs(b.runs), spacing: { after: 160, line: 300 } })); break;
    case "quote":
      children.push(new Paragraph({ children: [new TextRun({ text: b.text, italics: true, font: FONT, size: 22 })], indent: { left: 540 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: "2A78D6", space: 12 } }, shading: { type: ShadingType.CLEAR, fill: "EEF3FA" }, spacing: { before: 80, after: b.cite ? 20 : 160 } }));
      if (b.cite) children.push(new Paragraph({ children: [new TextRun({ text: b.cite, font: SANS, size: 17, color: "777777" })], indent: { left: 540 }, spacing: { after: 160 } }));
      break;
    case "ul": for (const li of b.items) children.push(new Paragraph({ children: runs(li), numbering: { reference: "bullets", level: 0 }, spacing: { after: 100, line: 290 } })); break;
    case "note": for (const p of b.paras) children.push(new Paragraph({ children: runs(p, { font: SANS, size: 19 }), shading: { type: ShadingType.CLEAR, fill: "F3F4F6" }, indent: { left: 200, right: 200 }, spacing: { after: 120, line: 280 } })); break;
    case "figure": {
      figN++; const img = fs.readFileSync(path.join(ROOT, b.png));
      const w = img.readUInt32BE(16), h = img.readUInt32BE(20); const W = 6.3 * 96, H = W * h / w;
      children.push(new Paragraph({ children: [new ImageRun({ type: "png", data: img, transformation: { width: Math.round(W), height: Math.round(H) } })], alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, keepNext: true }));
      children.push(new Paragraph({ children: runs(b.caption, { font: SANS, size: 18, color: "444444" }), spacing: { after: 280 } })); break; }
    case "foot": children.push(new Paragraph({ children: runs(b.runs, { font: SANS, size: 18, color: "666666" }), border: { top: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" } }, spacing: { before: 300 } })); break;
  }
}
const doc = new Document({
  creator: "Daniel Feller", title: "OHDSI Community Signals",
  styles: { default: { document: { run: { font: FONT, size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: false, color: "111111" }, paragraph: { outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: "111111" }, paragraph: { outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children }],
});
const out = path.join(ROOT, "deliverables/OHDSI_Community_Signals_blog_draft.docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("wrote", out, buf.length, "bytes", figN, "figures"); });
