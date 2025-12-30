# ✅ How to Build and Run Deep Agents with the UI (Deep Agents + LangGraph + Deep Agents UI)

This guide walks you through:

1. Setting up the **Deep Agents backend example** (`deepagents-quickstarts`)
2. Running it via the **LangGraph dev server**
3. Setting up and running the **Deep Agents UI**
4. Applying a fix for the **fetch history bug**

---

## ✅ Prerequisites

Make sure you have installed:

- **Python 3.10+**
- **Node.js 18+**
- **uv** (Python package manager)
- **git**
- **npm** or **yarn**

---

# Part 1 — Setup & Run the Deep Agents Backend

## 1) Clone the Deep Agents Quickstart Repo

'''bash
git clone https://github.com/langchain-ai/deepagents-quickstarts.git
'''

---

## 2) Navigate to the Deep Research Example Folder

'''bash
cd PATH_TO_REPO/deepagents-quickstarts/deep_research
'''

---

## 3) Sync the `uv` Environment

This installs the dependencies into `.venv`.

'''bash
uv sync
'''

---

## 4) Configure Environment Variables

You can either:

✅ Copy and edit `.env`  
or  
✅ Export environment variables directly

You will need values for:

- **LangSmith**
- **Tavily**
- **OpenAI OR Anthropic**

### Option A: Create `.env`

Copy the template and fill in values:

'''bash
cp .env.example .env
'''

Then update `.env` with correct keys, e.g.:

'''ini
LANGSMITH_API_KEY=...
TAVILY_API_KEY=...
OPENAI_API_KEY=...
'''

---

## 5) If Using OpenAI Instead of Anthropic

If the project defaults to Anthropic, install the OpenAI integration:

'''bash
pip install langchain-openai
'''

Then update your agent creation code to use `ChatOpenAI`.

Example:

'''python
from langchain_openai import ChatOpenAI

agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-4o"),
    tools=[tavily_search, think_tool],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)
'''

> ✅ Note: If you're not using Anthropic, make sure any Anthropic model initialization code is replaced with OpenAI equivalents.

---

## 6) Activate the Virtual Environment

'''bash
source .venv/bin/activate
'''

---

## 7) Run the Backend Dev Server

This starts the LangGraph backend server.

'''bash
langgraph dev
'''

By default, the backend runs at:

- **http://127.0.0.1:2024**

---

# Part 2 — Setup & Run Deep Agents UI

## 1) Clone the UI Repo

'''bash
git clone https://github.com/langchain-ai/deep-agents-ui
'''

---

## 2) Install Dependencies

Choose either npm or yarn:

'''bash
npm install
'''

or

'''bash
yarn install
'''

---

## 3) Create `.env.local`

Inside the UI repo, create a file named:

'''bash
.env.local
'''

Add the following variables:

'''ini
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
NEXT_PUBLIC_AGENT_ID=research
'''

✅ `NEXT_PUBLIC_DEPLOYMENT_URL` should point to the LangGraph backend server  
✅ `NEXT_PUBLIC_AGENT_ID` should match your agent name (e.g. `research`)

---

# Part 3 — Fix the “Fetch History” Bug

There is a known issue where chat history is not fetched correctly.

### ✅ Fix by enabling `fetchStateHistory: true`

Open:

'''
src/app/hooks/useChat
'''

Find the `useStream` call and add:

'''ts
fetchStateHistory: true,
'''

Full example:

'''ts
const stream = useStream<StateType>({
  assistantId: activeAssistant?.assistant_id || "",
  client: client ?? undefined,
  reconnectOnMount: true,
  threadId: threadId ?? null,
  onThreadId: setThreadId,
  defaultHeaders: { "x-auth-scheme": "langsmith" },
  fetchStateHistory: true,

  // Revalidate thread list when stream finishes, errors, or creates new thread
  onFinish: onHistoryRevalidate,
  onError: onHistoryRevalidate,
  onCreated: onHistoryRevalidate,
  experimental_thread: thread,
});
'''

---

# Part 4 — Start the UI

Run:

'''bash
npm run dev
'''

or

'''bash
yarn dev
'''

The UI usually starts at:

- **http://localhost:3000**

---

# ✅ Final Checklist

✅ Backend runs via:

'''bash
langgraph dev
'''

✅ Backend available at:

- **http://127.0.0.1:2024**

✅ UI runs via:

'''bash
npm run dev
'''

✅ UI available at:

- **http://localhost:3000**

✅ `.env.local` correctly points UI → backend  
✅ `fetchStateHistory: true` added to fix history issues  
✅ Model updated correctly if using OpenAI
