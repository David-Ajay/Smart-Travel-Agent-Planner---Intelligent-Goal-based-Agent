# Smart Travel Agent Planner – Intelligent Goal-Based Agent

## Project Overview
The Smart Travel Agent Planner is an AI-based system designed to optimize daily travel by intelligently grouping people heading toward the same destination. The system promotes carpooling and bike-sharing while minimizing total travel distance, fuel consumption, and travel time.

This project uses a goal-based intelligent agent that evaluates multiple travel possibilities and selects the most optimal plan based on distance, vehicle availability, and minimal detours.

---

## Problem Statement
In urban environments, individuals often travel alone despite having similar destinations, leading to increased fuel usage, traffic congestion, and environmental impact. Manually planning shared travel is inefficient and often results in suboptimal decisions.

This project addresses the problem by automatically planning optimal travel groups and routes using artificial intelligence and optimization techniques.

---

## Solution Approach
The system acts as a goal-based rational agent that:
- Collects traveler location and vehicle availability data
- Generates all feasible pooling combinations
- Evaluates each option based on distance and detour cost
- Selects the globally optimal solution using constraint optimization

Both carpooling and bike-sharing are supported, with intelligent decisions made on whether to pool or split travelers based on route efficiency.

---

## Agent Type
- Goal-Based Rational Agent
- Multi-Agent Planning Environment
- Optimization-Based Decision Making (OR-Tools CP-SAT Solver)

---

## Technologies Used
- Python
- Flask (Web Framework)
- Google OR-Tools (Optimization Solver)
- Pandas (Data Handling)
- Geopy (Distance Calculation)
- Google Maps (Route Visualization)

---

## System Features
- Intelligent carpooling and bike-sharing
- Detour-aware route planning
- Flexible decision-making for splitting or pooling travelers
- Real-time route visualization
- Eco-friendly and cost-efficient travel planning

---

## Project Structure
Smart Travel Agent Planner/
│
├── app.py
├── Dataset.xlsx
├── requirements.txt
├── README.md
├── templates/
│ ├── index.html
│ ├── destination.html
│ ├── select_students.html
│ └── results.html
└── static/

---

## How to Run the Project
1. Clone the repository:
git clone <repository-url>

2. Navigate to the project folder:
cd Smart-Travel-Agent-Planner

3. Install dependencies:
pip install -r requirements.txt

4. Run the application:
python app.py

5. Open the browser and visit:
http://127.0.0.1:5000


---

## Applications
- College and university travel planning
- Office and workplace commuting
- Group travel coordination
- Sustainable transportation systems

---

## Conclusion
The Smart Travel Agent Planner demonstrates how artificial intelligence and optimization can be applied to real-world transportation problems. By acting as a goal-based intelligent agent, the system provides efficient, scalable, and environmentally friendly travel solutions.