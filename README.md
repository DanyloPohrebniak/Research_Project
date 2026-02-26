# Virtual Learning Environment with AI Assistant

Research project implementing a Virtual Learning Environment (VLE) based on Open edX with an integrated AI assistant.

![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)


## Overview

This project provides a fully functional Learning Management System using Open edX, extended with an AI-powered assistant designed to help students interact with course materials.

The system follows a microservice architecture and integrates modern AI technologies.

## Features

- Open edX Learning Management System
- Course creation and management
- Student enrollment
- Web-based learning interface
- Docker-based deployment
- AI assistant integration (in progress)
- Scalable architecture

## Architecture

System architecture:

User Browser
↓
Open edX LMS
↓
AI Assistant Service
↓
LLM API

## Technology Stack

- Open edX
- Docker
- Tutor
- Python
- FastAPI
- OpenAI API
- WSL2 (Windows)
- Ubuntu

## Requirements

- Docker Desktop
- WSL2
- Ubuntu 22.04
- Python 3.10+
- Tutor

## Installation Guide

### 1. Install Docker Desktop

Download and install Docker Desktop.

Enable WSL integration.

### 2. Install WSL and Ubuntu

In PowerShell:

    ```bash
    wsl --install
    ```

Install Ubuntu from Microsoft Store.

### 3. Install Tutor

In Ubuntu terminal:

    ```bash
    sudo apt update
    sudo apt install python3-venv python3-pip -y

    python3 -m venv venv
    source venv/bin/activate

    pip install "tutor[full]"
    ```

### 4. Initialize Open edX

    ```bash
    tutor config save
    tutor local launch
    ```

Wait until all services are initialized.

### 5. Configure hosts file

Edit:
    ```bash
    C:\Windows\System32\drivers\etc\hosts
    ```

In the end add:

    ```bash
    127.0.0.1 local.openedx.io
    127.0.0.1 studio.local.openedx.io
    ```

### 6. Access the platform

LMS:
    ```bash
    http://local.openedx.io
    ```

Studio:
    ```bash
    http://studio.local.openedx.io
    ```

## Creating Admin User

Run:
    ```bash
    tutor local do createuser --staff --superuser admin admin@example.com
    ```


## Running the Platform

Start:

```bash
tutor local start
```

Stop:
```bash
tutor local stop
```


Restart:

```bash
tutor local restart
```
