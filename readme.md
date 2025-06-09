ATP Resolution WebApp is a web-based educational tool developed as part of a bachelor’s thesis. The application demonstrates Automated Theorem Proving (ATP) using the resolution method, and serves as a learning aid for the "Logic for IT Students" course .

#Features

*Input of propositional logic formulas in CNF (Conjunctive Normal Form)

*Step-by-step resolution proof visualization

*Detection of unsatisfiability via deriving the empty clause

#Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Infinitiv525/atp-resolution-webapp.git
   cd atp-resolution-webapp
   ```

2. **Create & activate a virtual environment (optional but recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux  
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py    # or flask run / uvicorn main:app --reload
   ```

5. **Open in your browser**
   Navigate to `http://localhost:5000` (or as indicated by the server output).

# Usage

* Enter one or more CNF clauses (e.g. `A or ¬B`, `¬A or C or D`, etc.).
* Click **"Run Resolution"** to let the ATP engine derive the empty clause, or **"Step-by-step"** to walk through the process manually.
* Visual feedback shows which two clauses resolved, the resulting resolvent clause, and if a contradiction (empty clause) is reached.
