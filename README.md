# Cartora — E-Commerce Customer Support AI

> **Shop simply. Support that remembers.**

Cartora is a fictional e-commerce portal featuring an intelligent customer support assistant powered by persistent, customer-specific conversational memory. Unlike standard chatbots that forget previous interactions once a session ends, Cartora retains context across visits—recalling preferences, past queries, order details, and resolution history to deliver personalized, proactive support.

---

## 🚀 Tech Stack

- **Backend:** Python 3.10+, Flask
- **LLM Engine:** Groq API (`llama-3.3-70b-versatile`)
- **Persistent Memory:** Hindsight Cloud (`hindsight-client`)
- **Frontend:** Responsive HTML5, Modern CSS, Vanilla JavaScript
- **Production Server:** Gunicorn

---

## 🛠️ Setup Instructions

Follow these steps to run Cartora locally:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CARTORA
   ```

2. **Create and activate a virtual environment**
   - On Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Copy `.env.example` to `.env` and provide your API keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your keys:
   - `GROQ_API_KEY`: Your Groq Cloud API key.
   - `HINDSIGHT_API_KEY`: Your Hindsight Cloud API key.

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   Navigate to [http://localhost:5000](http://localhost:5000) to access the store and chat with the AI assistant.

---

## 👥 Demo Accounts

Use any of the following pre-configured demo credentials to sign in:

| Customer Name | Email | Password | Customer ID | Tier | Location |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Maya Sharma** | `maya.sharma@cartora.example` | `CartoraDemo#1` | `C1001` | Cartora Plus | Hyderabad |
| **Arjun Verma** | `arjun.verma@cartora.example` | `CartoraDemo#2` | `C1002` | Standard | Bengaluru |

---

## 📂 Project Structure Overview

```
CARTORA/
├── .env.example              # Template environment configuration
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation and quickstart
├── app.py                    # Main Flask application entrypoint
├── data/                     # Application data stores (JSON-based)
│   ├── demo_users.json       # Demo user credentials and mapping
│   ├── customers.json        # Customer profiles and membership tiers
│   ├── products.json         # Product catalog and specifications
│   ├── orders.json           # Order history, timeline steps, tracking
│   ├── returns.json          # Return requests records
│   ├── warranties.json       # Warranty claims and status
│   └── cases.json            # Support case tickets
├── static/                   # Static assets (CSS, client JS, images)
└── templates/                # Jinja2 HTML templates
```

---

## 🏗️ Architecture & Memory Flow

```
[ User Action / Prompt ]
          │
          ▼
┌─────────────────────────────────┐
│     Cartora Web Portal          │
│   (Login / Authenticated Session)│
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│   Context Assembler             │
│   • Customer Profile & Tier     │
│   • Active Orders & Returns     │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│   Hindsight Cloud: Recall       │
│   • Retrieve past customer      │
│     context, issues, sentiment  │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│   Groq LLM Engine               │
│   (llama-3.3-70b-versatile)     │
│   • Synthesize response using   │
│     order context + recalled    │
│     memories                    │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│   Hindsight Cloud: Retain       │
│   • Store conversation insights │
│     and key customer facts      │
└─────────────────────────────────┘
          │
          ▼
[ Customer Receives Contextual Support Response ]
```

---

## ⚠️ Prototype Disclaimer

> **Note:** Cartora is a hackathon prototype built for demonstration and evaluation purposes.
> - **Authentication:** Uses simulated demo login credentials; do not use for production authentication.
> - **Transactions:** All orders, prices, and tracking IDs are simulated; no real payment processing is executed.
