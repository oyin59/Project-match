<div align="center">
  <h1>✨ ProjectMatch ✨</h1>
  <p><i>A smart, aesthetic, and automated university project allocation system.</i></p>
  
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
  ![Bootstrap](https://img.shields.io/badge/Bootstrap_5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

  <p>Say goodbye to messy spreadsheets! ProjectMatch is a seamless, Django-based platform designed to match university students to their final-year academic projects with fairness, speed, and style. 💜</p>
</div>

---

## 🌟 Features

*   👩‍🎓 **Smart Role Routing:** A beautiful, centralized login page that intelligently directs Students, Supervisors, and Administrators straight to their personalized dashboards.
*   🖱️ **Drag-and-Drop Magic:** Students can effortlessly select and rank their top 3 project preferences using our tactile, interactive drag-and-drop UI. 
*   ⚖️ **The Fairness Engine:** Our custom algorithmic matching engine calculates profile suitability and strict project quotas to allocate the entire cohort automatically!
*   📊 **Suitability Checker & Dashboards:** Dynamic Chart.js visuals and progress bars give supervisors real-time insights into student prerequisite matches. 
*   🔔 **Real-Time Notifications:** A friendly navbar bell alerts users of new actions (like preference reminders or successful allocations) alongside animated SweetAlert2 modals!
*   💅 **Premium 3D Aesthetic:** Built with the official Aston University color palette, featuring deep purples, soft gradients, and interactive push-buttons for a satisfying UX.

---

## 🛠️ How to Run Locally

Want to take ProjectMatch for a spin? It's super easy! We use `pipenv` to manage our Python magic. 🪄

### 📋 Prerequisites
*   **Python 3.x** installed on your machine.
*   **Pipenv** installed (`pip install pipenv`).

### 🚀 Setup Guide

**1. Clone & Enter**
Grab the repository and open up your terminal:
```bash
git clone https://github.com/oyin59/Project-match.git
cd Project-match
```

**2. Install Dependencies**
Let Pipenv handle the heavy lifting:
```bash
pipenv install
```

**3. Activate the Environment**
Step into the virtual shell:
```bash
pipenv shell
```

**4. Setup the Database**
Apply the migrations to get your local SQLite database ready:
```bash
python manage.py migrate
```

**5. 🧪 Seed the Data (Highly Recommended!)**
We built a handy script to generate dummy data so you can test everything immediately. This creates a fresh batch of Students, Supervisors, Admins, and Projects!
```bash
python manage.py seed_final_data
```
*(Psst! Check out `test_accounts.txt` after running this to see exactly who you can log in as!)*

**6. Start the Server!**
```bash
python manage.py runserver
```
Navigate to [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/) in your browser and enjoy the aesthetic! 🎉

---

## 🧐 Usability Testing

If you'd like your friends or supervisors to test the system out, simply share the `test_accounts.txt` file with them! It contains all the dummy credentials they need to explore the platform as any role.

<br>
<div align="center">
  <i>Built with 💜 for my Final Year Project at Aston University.</i>
</div>
