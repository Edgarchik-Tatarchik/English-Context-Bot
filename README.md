<h1 align="center">English Context Bot</h1>

<p align="center">
  A Telegram bot that explains English words/phrases in simple English and generates contextual example sentences.
  <br />
  Built with <b>Python</b> + <b>aiogram</b> + <b>OpenAI API</b> + <b>SQLite</b>.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3.x-2ea44f" />
</p>

<p align="center">
  You can test this bot in Telegram app by following link:
  <a href="https://t.me/@EnglishContextBot">
    <img src="https://img.shields.io/badge/Telegram-Try%20the%20bot-2CA5E0?logo=telegram&logoColor=white" />
  </a>
</p>

<hr />

<h2>🎯 Problem</h2>
<p>
  When learning English daily, it’s easy to collect words but hard to <b>repeat them in context</b> and
  keep them <b>organized</b>. This bot helps by generating:
</p>
<ul>
  <li><b>Simple explanation</b> (CEFR B1 level)</li>
  <li><b>10 natural example sentences</b> that include the term exactly as written</li>
  <li><b>Save</b> feature to build a personal vocabulary bank</li>
  <li><b>Quiz</b> feature to practice meanings with multiple-choice questions</li>
</ul>

<h2>✨ Features</h2>
<ul>
  <li><b>Explain + 10 examples</b>: send a word/short phrase (1–4 words) and get a simple explanation + examples</li>
  <li><b>More examples</b>: generate another set of examples on demand</li>
  <li><b>Save</b>: store terms and generated content in SQLite per user</li>
  <li><b>Saved words</b>: browse saved terms with pagination</li>
  <li><b>Quiz</b>: multiple-choice quiz generated from saved terms (per-term quiz)</li>
  <li><b>Input validation</b>: rejects overly long or invalid inputs</li>
</ul>

<h2>🧩 How It Works</h2>
<ol>
  <li>User sends a term (e.g., <code>take a break</code>).</li>
  <li>Bot calls the OpenAI API to generate structured JSON:
    <ul>
      <li>Simple explanation</li>
      <li>Exactly 10 examples</li>
    </ul>
  </li>
  <li>User can save the result to SQLite.</li>
  <li>User can run a quiz for that saved term (the bot generates 2 plausible distractors).</li>
</ol>

<h2>🛠 Tech Stack</h2>
<ul>
  <li><b>Python</b> 3.10+</li>
  <li><b>aiogram</b> (Telegram Bot API framework)</li>
  <li><b>OpenAI API</b> (LLM responses in JSON schema format)</li>
  <li><b>SQLite</b> (local storage for saved terms and quiz attempts)</li>
  <li><b>dotenv</b> for environment variables</li>
</ul>




<h2>🤖 Bot Usage</h2>
<ul>
  <li>Start: <code>/start</code></li>
  <li>Send a word/phrase: <code>take a break</code>, <code>reliable</code>, <code>make up</code></li>
  <li>Use buttons under the answer:
    <ul>
      <li><b>💾 Save</b> — saves term + explanation + examples</li>
      <li><b>🧠 Quiz</b> — quiz for the saved term</li>
      <li><b>➕ More examples</b> — generates more sentences</li>
      <li><b>📚 Saved words</b> — opens saved list with pages</li>
    </ul>
  </li>
</ul>

<h2>🗃 Data Storage</h2>
<p>
  The project uses <b>SQLite</b> for a lightweight, server-friendly storage approach.
  Saved terms and quiz attempts are stored per Telegram user.
</p>

<h2>🧭 Roadmap</h2>
<ul>
  <li>Better quiz UX: per-term quiz from saved list (tap term → quiz)</li>
  <li>Tagging and search for saved terms</li>
</ul>


