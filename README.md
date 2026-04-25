<div align="center">
  <img src="https://raw.githubusercontent.com/oyin59/Project-match/main/static/images/logo.png" alt="ProjectMatch Logo" width="120" style="margin-bottom: 20px;">
  
  <h1>✨ ProjectMatch ✨</h1>
  <p><b>A Premium Student-Project Allocation Platform for Academic Excellence</b></p>
  
  <p><i>Effortless. Fair. Satisfyingly Aesthetic.</i></p>

  [![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
  [![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
  [![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
  [![Licence](https://img.shields.io/badge/Academic-Project-purple?style=flat-square)](LICENSE)

  <br>

  <p align="center" style="max-width: 600px;">
    Say goodbye to administrative friction. <b>ProjectMatch</b> is a sophisticated, full-stack platform designed to automate university project matching. Combining a merit-based allocation engine with a premium 3D user experience, it ensures every student finds their perfect match. 💜
  </p>
</div>

---

## 🎨 Professional & Aesthetic UX

ProjectMatch isn't just a utility; it's a statement. Designed with the **Aston University** identity in mind, it features:

*   📱 **Responsive Elegance:** A fluid interface that looks stunning on desktops, tablets, and phones.
*   🖱️ **Tactile Interactions:** 3D-styled "push-buttons" that physically depress, providing satisfying user feedback.
*   🌈 **Color Harmony:** A sophisticated palette of Deep Amethyst, Slate Gray, and Pearl White.
*   ⚡ **Fluid Transitions:** Real-time data persistence via AJAX—no clunky page reloads.

---

## 🚀 Key Functional Modules

*   👩‍🎓 **Smart Student Portal:** Intuitive **Drag-and-Drop** preference ranking (powered by SortableJS) and academic profile management.
*   ⚖️ **The Fairness Engine:** A hybrid scoring algorithm that calculates the optimal cohort-wide allocation based on **Preferences** x **Academic Merit** x **Quotas**.
*   🎚️ **Dynamic Weighting:** Administrators can tune the allocation ratio at runtime using a live slider to prioritize either technical suitability or student happiness.
*   📊 **Supervisor Dashboard:** Real-time suitability checks comparing student skillsets against project prerequisites via dynamic match indicators.
*   🔔 **Real-Time Notifications:** A global notification engine ensuring no stakeholder misses a critical deadline.
*   🛡️ **RBAC & Auditability:** Role-Based Access Control and a comprehensive **System Audit Trail** for total administrative transparency.

---

## 💻 Tech Stack & Architecture

- **Core Engine:** Python 3.12 + Django 5.x (MVT Architecture)
- **Data Persistence:** Relational SQLite Database
- **Frontend Layer:** Vanilla CSS3 + Bootstrap 5 + SweetAlert2
- **Dynamic Logic:** AJAX (Fetch API) + Chart.js Visualization
- **Security:** CSRF Protection + PBKDF2 Password Hashing

---

## 🛠️ Developer Quick-Start

Get ProjectMatch running on your machine in under **60 seconds**.

### 1. Environment Setup
We use `pipenv` for robust dependency management.
```bash
git clone https://github.com/oyin59/Project-match.git && cd Project-match
pipenv install
pipenv shell
```

### 2. Database Initialization
```bash
python manage.py migrate
```

### 3. Synthetic Data Seeding (Required for Demo) 🧪
This generates a realistic cohort of 15 students, 5 supervisors, and 15 projects.
```bash
python manage.py seed_final_data
```

### 4. Lift-Off! 🚀
```bash
python manage.py runserver
```
🔗 Visit [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/)

---

<div align="center">
  <br>
  <sub><b>ProjectMatch</b> • Final Year Project • Aston University</sub>
  <br>
  <sub>Developed with 💜 by your favorite developer</sub>
</div>
