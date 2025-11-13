import fs from "fs";
import path from "path";
import fetch from "node-fetch";
import { parse } from "csv-parse/sync";
import { stringify } from "csv-stringify/sync";

const SERPAPI_KEY = "cb4bf8ec9830cb36ef5ac3394a5c401bebfc5c38de3e208632e7691c171bc5d4";

const inputCsv = "items.csv";
const outputCsv = "items_with_images.csv";

const rows = parse(fs.readFileSync(inputCsv, "utf8"), {
  columns: true,
  skip_empty_lines: true
});

async function getFirstImage(query) {
  const url = `https://serpapi.com/search.json?q=${encodeURIComponent(
    query
  )}&engine=google_images&api_key=${SERPAPI_KEY}`;

  try {
    const res = await fetch(url);
    const json = await res.json();

    if (json.images_results && json.images_results.length > 0) {
      return json.images_results[0].original || json.images_results[0].thumbnail;
    }
  } catch (e) {
    console.error("Erro buscando", query, e);
  }

  return "";
}

async function main() {
  const out = [];

  for (const r of rows) {
    const query = `${r.Title} Logo Figure`.trim();
    console.log("Buscando:", query);

    const imageUrl = await getFirstImage(query);

    out.push({
      ...r,
      ImageURL: imageUrl
    });

    await new Promise((res) => setTimeout(res, 150)); // evita limites
  }

  const output = stringify(out, { header: true });
  fs.writeFileSync(outputCsv, output);

  console.log("Finalizado →", outputCsv);
}

main();
