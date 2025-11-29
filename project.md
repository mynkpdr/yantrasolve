# Project: LLM Analysis Quiz

In this project, students will build an application that can solve a quiz that involves data sourcing, preparation, analysis, and visualization using LLMs.
You should implement an API endpoint that can receive quiz tasks, solve them using LLMs and headless browsers, and submit the answers back to the quiz system.

## Tech Stack
- Python 3.11+
- FastAPI for building the API endpoint
- LangGraph and LangChain for LLM orchestration
- Playwright for headless browser automation
- Pandas for data manipulation and analysis
- Matplotlib/Seaborn/Plotly for data visualization
- Uvicorn for running the FastAPI server
- Pydantic for data validation
- Any other libraries as needed for specific tasks (e.g., PDF parsing, audio processing)

## API Endpoint Quiz Tasks

Your API endpoint will receive a POST request with a JSON payload containing your email, secret and a quiz URL, like this:

```jsonc
{
  "email": "your email", // Student email ID
  "secret": "your secret", // Student-provided secret
  "url": "https://example.com/quiz-834 " // A unique task URL
}
```

Your endpoint must:

1. Verify the `secret` matches what you provided in the Google Form.
2. Respond with a HTTP 200 JSON response if the secret matches. Respond with HTTP 400 for invalid JSON and HTTP 403 for invalid secrets. (We'll check this with incorrect payloads.)
3. Visit the `url` and solve the quiz on that page.

The quiz page will be a human-readable JavaScript-rendered HTML page with a data-related task.

Here's a **sample** quiz page (not the actual quiz you will receive). (This requires DOM execution, hence a headless browser.)

```html
<div id="result"></div>

<script>
  document.querySelector("#result").innerHTML = atob(`
UTgzNC4gRG93bmxvYWQgPGEgaHJlZj0iaHR0cHM6Ly9leGFtcGxlLmNvbS9kYXRhLXE4MzQucGRmIj5
maWxlPC9hPi4KV2hhdCBpcyB0aGUgc3VtIG9mIHRoZSAidmFsdWUiIGNvbHVtbiBpbiB0aGUgdGFibG
Ugb24gcGFnZSAyPwoKUG9zdCB5b3VyIGFuc3dlciB0byBodHRwczovL2V4YW1wbGUuY29tL3N1Ym1pd
CB3aXRoIHRoaXMgSlNPTiBwYXlsb2FkOgoKPHByZT4KewogICJlbWFpbCI6ICJ5b3VyLWVtYWlsIiwK
ICAic2VjcmV0IjogInlvdXIgc2VjcmV0IiwKICAidXJsIjogImh0dHBzOi8vZXhhbXBsZS5jb20vcXV
pei04MzQiLAogICJhbnN3ZXIiOiAxMjM0NSAgLy8gdGhlIGNvcnJlY3QgYW5zd2VyCn0KPC9wcmU+`);
</script>
```

Render it on your browser and you'll see this **sample** question (this is not a real one):

> Q834. Download [file](https://example.com/data-q834.pdf ). What is the sum of the "value" column in the table on page 2?
>
> Post your answer to https://example.com/submit  with this JSON payload:
>
> ```jsonc
> {
>   "email": "your email",
>   "secret": "your secret",
>   "url": "https://example.com/quiz-834 ",
>   "answer": 12345 // the correct answer
> }
> ```

Here is another sample:
```html
<p><audio src="demo-audio.opus" controls></audio></p>

<p><a href="demo-audio-data.csv">CSV file</a></p>
<p>Cutoff: <span id="cutoff"></span></p>

<p>POST to JSON to <span class="origin"></span>/submit</p>

<pre>
{
  "email": "your email",
  "secret": "your secret",
  "url": "<span class="origin"></span>/demo-audio",
  "answer": ...
}
</pre>

<script type="module">
import { emailNumber, getEmail, sha1 } from "./utils.js";
document.querySelector("#cutoff").innerHTML = (await emailNumber())
  || "Please provide ?email=";
for (const el of document.querySelectorAll(".origin")) {
  el.innerHTML = window.location.origin;
}
</script>
```
you'll see this sample:
> <audio src="https://tds-llm-analysis.s-anand.net/demo-audio.opus " controls></audio>
>
> [CSV file](https://tds-llm-analysis.s-anand.net/demo-audio-data.csv )
> 
> Cutoff: 63395
> 
> POST to JSON to https://tds-llm-analysis.s-anand.net/submit 
> ```jsonc
> {
>   "email": "your email",
>   "secret": "your secret",
>   "url": "https://tds-llm-analysis.s-anand.net/demo-audio ",
>   "answer": ...
> }
> ```



Your script must follow the instructions and submit the correct answer to the specified endpoint within 3 minutes of the POST reaching our server. The quiz page **always** includes the submit URL to use. **Do not hardcode any URLs**.

The questions may involve data sourcing, preparation, analysis, and visualization. The `"answer"` may need to be a boolean, number, string, base64 URI of a file attachment, or a JSON object with a combination of these. Your JSON payload **must be under 1MB**.

The endpoint will respond with a HTTP 200 and a JSON payload indicating whether your answer is correct and may include another quiz URL to solve. For example:

```jsonc
{
  "correct": true,
  "url": "https://example.com/quiz-942 ",
  "reason": null
  "// ... other fields"
}
```

```jsonc
{
  "correct": false,
  "reason": "The sum you provided is incorrect."
  // maybe with no new url provided
}
```

If your answer is wrong:

- you are allowed to re-submit, as long as it is _still_ within 3 minutes of the _original_ POST reaching our server. Only the last submission within 3 minutes will be considered for evaluation.
- you _may_ receive the next `url` to proceed to. If so, you can choose to skip to that URL instead of re-submitting to the current one or work on both in parallel.

If your answer is correct, you will receive a new `url` to solve unless the quiz is over.

When you receive a new `url`, your script must visit the `url` and solve the quiz on that page. Here's a sample sequence:

1. We send you to `url: https://example.com/quiz-834 `
2. You solve it wrongly. You get `url: https://example.com/quiz-942 ` and solve it.
3. You solve it wrongly. You re-submit. Now it's correct and you get `url: https://example.com/quiz-123 ` and solve it.
4. You solve it correctly and get no new URL, ending the quiz.

Here are some types of questions you can expect:
- Scraping a website (which may require JavaScript) for information
- Intelligent Web crawling
- Sourcing from an API (with **API-specific headers** provided where required)
- Cleansing text / data / PDF / ... you retrieved
- Processing the data (e.g. data transformation, transcription, vision)
- Analysing by filtering, sorting, aggregating, reshaping, or applying statistical / ML models. Includes geo-spatial / network analysis
- Visualizing by generating charts (as images or interactive), narratives, slides
- Extracting complex tables from PDFs (rotated, multi-column, or scanned).
- OCR on scanned pages, images, or charts.
- Base64-encoded HTML/JSON decoding.
- Gzip, ZIP, or AES-encrypted payload decoding.
- Reverse-engineering encoded JavaScript blobs.
- Navigating paginated or multi-step websites.
- Scraping canvas-rendered charts (D3, Plotly, Chart.js).
- Extracting values from interactive visualizations (hover tooltips, legends).
- Geospatial analysis on GeoJSON/KML (distances, intersections).
- Scraping JavaScript-rendered tables requiring headless browser.
- Transcribing audio files (speech-to-text).
- Detecting loudest/quietest timestamp in waveform data.
- Combining CSV + audio metadata to compute answers.
- Reading data embedded inside images (QR code, barcode).
- Extracting numbers from screenshots or plotted charts.
- Machine learning tasks like regression, clustering, classification.
- Text cleaning and entity extraction from long documents.
- Sentiment or topic classification on scraped text.
- Joining multiple datasets: CSV + API + HTML table.
- Crawling a website with dynamic links or filters.
- Handling CAPTCHAs (simple text/visual).
- Identifying the largest/smallest value in visual charts.
- Currency conversion or unit transformation.
- Parsing messy CSVs (bad delimiters, merged columns).
- Parsing Excel files with merged cells or formulas.
- Summarizing long text and extracting key facts.
- Solving logic puzzles encoded in HTML.
- Extracting timelines from a list of events in text.
- Sorting, filtering, and aggregating tabular data.
- Computing statistical metrics (median, IQR, mode).
- Creating visualizations (PNG charts, SVG charts).
- Returning plots encoded as base64 URIs.
- Creating PDF reports and returning them.
- Generating ZIP files containing result data.
- Parsing time-series data and detecting anomalies.
- Fetching APIs requiring specific headers/cookies.
- OAuth-style token extraction from page scripts.
- Analyzing network graphs (edges/nodes) from JSON files.
- Computing shortest paths in graph datasets.
- Merging or splitting JSON objects.
- Extracting numeric answers hidden inside JS variables.
- Dealing with script tags building DOM dynamically.
- Extracting tables from iframes or shadow DOM.
- Parsing HTML with broken markup or weird encoding.
- Scraping data from PDF embedded images (charts/screenshots).
- Counting frequencies of words, names, entities.
- Language translation before analysis.
- Identifying language of given text.
- Normalizing inconsistent date/time formats.
- Hashing or checksumming files (MD5/SHA1).
- Following redirect chains and meta refresh.
- Solving riddles hidden in the quiz page.
- Extracting data from localStorage/sessionStorage.
- Reading hidden fields or comments containing data.
- Parsing audio spectrogram images.
- Extracting values hidden in CSS (e.g., content: "123";).
- Handling mathematical expressions or LaTeX.
- Performing symbolic math (integrals, derivatives).
- Detecting duplicates across datasets.
- Merging multiple PDFs before analysis.
- Image similarity detection or clustering.
- Cropping specific areas of images for OCR.
- Extracting structured data from unstructured reports.
- Searching the web (if explicitly permitted by quiz page).
- Reading EXIF metadata from images.
- Parsing unusual file formats (YAML, TOML, NDJSON).
- Extracting timestamps from logs.
- Handling email-based dynamic thresholds or seeds.
- Reconstructing missing data using interpolation.
- Reverse engineering a mini puzzle inside JavaScript code.