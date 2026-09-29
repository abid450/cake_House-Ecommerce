# 🍰 Cake House — Django ERP & E-Commerce Platform

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.14-A30000?style=for-the-badge&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A complete, production-ready ERP & E-Commerce platform for bakeries and dessert shops, built with Django, DRF, Celery, Redis, and SSLCommerz.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Docs](#-api-documentation) • [Screenshots](#-screenshots) • [Contributing](#-contributing)

</div>

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Background Tasks](#-background-tasks)
- [Payment Integration](#-payment-integration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 About the Project

**Cake House** is a full-featured **ERP (Enterprise Resource Planning)** and **E-Commerce platform** designed specifically for bakeries, cake shops, and dessert businesses. It combines the power of a modern e-commerce system with comprehensive business management tools including inventory, orders, payments, and analytics.

### 🌟 What Makes This Project Special?

- 🏗️ **Production-Ready Architecture** — Built with scalability and security in mind
- ⚡ **Asynchronous Task Processing** — Celery + RabbitMQ for background jobs
- 🚀 **High-Performance Caching** — Redis for fast data retrieval
- 💳 **Real Payment Gateway** — SSLCommerz integration (bKash, Nagad, Card, Bank)
- 🐳 **Dockerized Deployment** — Easy setup with Docker Compose
- 📊 **Admin Dashboard** — Real-time analytics and business insights
- 🔐 **JWT Authentication** — Secure API access with token-based auth
- 📧 **Automated Notifications** — Email alerts for orders, low stock, and more

---

## ✨ Features

### 🛒 E-Commerce Features

| Feature | Description |
|---------|-------------|
| 🍰 **Product Management** | Multiple categories, dessert types, images, and specifications |
| 🛒 **Shopping Cart** | Add, update, remove items with persistent cart storage |
| 📦 **Order Management** | Complete order lifecycle with status tracking |
| 💳 **Payment Gateway** | SSLCommerz, bKash, Nagad, Card, COD support |
| 👤 **User Authentication** | JWT-based registration, login, password reset |
| 📧 **Email Verification** | Secure account verification with token expiry |
| ⭐ **Product Reviews** | Customer ratings and feedback system |
| 🔍 **Advanced Search** | Filter by category, price, availability |
| 🎨 **Custom Cakes** | Customization options for personalized orders |
| 📱 **Responsive Design** | Mobile-first, fully responsive UI |

### 🏢 ERP Features

| Feature | Description |
|---------|-------------|
| 📊 **Admin Dashboard** | Real-time sales, orders, revenue analytics |
| 📦 **Inventory Management** | Stock tracking with low-stock alerts |
| 📈 **Sales Reports** | Daily, weekly, monthly reports |
| 💰 **Payment Tracking** | Transaction history and refund management |
| 📧 **Notification System** | Email alerts for orders, stock, and updates |
| 🔄 **Order Automation** | Celery-powered order processing |
| 📁 **Data Backup** | Automated database backups |
| 🗑️ **Cleanup Tasks** | Expired tokens, abandoned carts cleanup |
| 📱 **Customer Management** | Customer profiles, order history, analytics |

---

## 🛠 Tech Stack

### Backend
- **Framework:** Django 4.2.7, Django REST Framework 3.14
- **Database:** PostgreSQL 15 (Production), SQLite 3 (Development)
- **Task Queue:** Celery 5.3, RabbitMQ 3.12
- **Cache:** Redis 7.0
- **Authentication:** JWT (SimpleJWT)

### DevOps
- **Containerization:** Docker 24.0, Docker Compose 2.20
- **Web Server:** Gunicorn, Nginx
- **CI/CD:** GitHub Actions
- **Monitoring:** Flower (Celery)

### Payment
- **Gateway:** SSLCommerz (bKash, Nagad, Card, Bank, COD)

### Frontend
- **Templates:** Django Templates
- **Styling:** Custom CSS (Bengali Typography)
- **Icons:** Font Awesome 6.5
- **Fonts:** Noto Serif Bengali, Hind Siliguri, JetBrains Mono

---

## 🏗 Architecture
