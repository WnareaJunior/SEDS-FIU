# Mission Control Frontend 🚀  
**Capstone Project – Self-Landing Amateur Rocket System**  

This repository contains the **frontend software** for a Mission Control system developed as part of a senior Capstone project. The full project involved designing and implementing a custom microcontroller board for amateur rocketry, with the goal of enabling **gas-propellant, self-landing rockets**.  

The Mission Control frontend is built in **Python** and provides real-time monitoring, control, and data recording functionality. It interfaces with onboard avionics to help operators observe telemetry, issue stop/abort commands, and log flight data for both **live operations** and **training simulations**.  

---

## 🎯 Project Overview

### Key Objectives
- Collaborate with a mechanical engineering team to develop a low-cost, modular telemetry and control system for rockets.  
- Build custom hardware (microcontroller-based avionics board) to control gas-propellant systems for soft landings.  
- Create a **Mission Control frontend** that enables:
  - Real-time rocket telemetry monitoring
  - Manual system stop/abort controls
  - Flight data recording for post-flight analysis
  - Training-mode simulation playback

---

## 🖥️ Features (Frontend)
- **Live Telemetry Visualization**: View real-time data from rocket sensors (altitude, velocity, orientation, etc.).  
- **Control Interface**: Send stop/abort commands to ensure safety during testing and launches.  
- **Data Recording**: Log flight data for debugging, engineering analysis, and training.  
- **Simulation/Training Mode**: Replay recorded missions for operator training.  
- **Python-based GUI**: Built for simplicity and portability.  

---

## 🔧 Tech Stack
| Component                | Technology                     |
|--------------------------|------------------------------|
| Frontend Language        | Python                       |
| GUI Framework            | Tkinter / PyQt / Custom (adjust if needed) |
| Communication Protocol   | Serial / USB / (adjust if custom) |
| Hardware Interface       | Custom microcontroller board |
| Deployment Environment   | Desktop (Windows/macOS/Linux) |

---

## 📂 Repository Structure

MissionControlFrontend/
├── src/ # Frontend source code
├── data/ # Recorded flight datasets
├── docs/ # Project documentation
└── README.md


---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+  
- `pip` package manager  
- Required libraries (install via `requirements.txt`):  
  ```bash
  pip install -r requirements.txt

Running the App
python src/main.py


This will launch the Mission Control interface.

🧩 Project Context

This frontend is part of a larger Capstone project:

Custom avionics board designed from scratch

Integration with mechanical and propulsion teams

Focus on affordable, modular hardware for amateur rocket teams

Goal: Build a platform for research, competition, and education in self-landing rocketry

🎓 Team
Name	Role
Wilson Narea	Software & Frontend Dev
[Teammate Names]	Avionics, Mechanical, etc.
📄 License

MIT License – Free to use, modify, and learn from.

📣 Notes

This repository only contains the frontend software.
Hardware schematics, embedded firmware, and mechanical CAD files are maintained in separate repositories.
