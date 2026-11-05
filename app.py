import os
import signal
import subprocess
import threading
import time
import shutil
import zipfile
import json
import psutil
import hashlib
import secrets
import urllib.request
import sys
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file, session, flash
from functools import wraps


# ===== EMBEDDED HTML TEMPLATES (single-file deployment) =====
TEMPLATE_LOGIN = '<!-- login.html - পাসওয়ার্ড হাইড করা -->\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{{ config.site_title }} - Login</title>\n    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">\n    <style>\n        :root {\n            --primary: #00ff00;\n            --secondary: #00cc00;\n            --accent: #00ff80;\n            --bg: #000000;\n            --card-bg: #0a0a0a;\n            --text: #00ff00;\n            --danger: #ff0000;\n        }\n        \n        body { \n            background-color: var(--bg); \n            color: var(--text); \n            font-family: \'Courier New\', monospace;\n            min-height: 100vh;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0;\n            padding: 20px;\n            position: relative;\n            overflow: hidden;\n            transition: background-color 0.3s ease;\n        }\n        \n        .matrix-bg {\n            position: fixed;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 100%;\n            pointer-events: none;\n            z-index: 0;\n            opacity: 0.3;\n            transition: opacity 0.3s ease;\n        }\n        \n        .matrix-column {\n            position: absolute;\n            top: -100%;\n            color: var(--primary);\n            font-size: 13px;\n            line-height: 1.2;\n            writing-mode: vertical-rl;\n            text-orientation: upright;\n            animation: matrix-fall linear infinite;\n            text-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary);\n            transition: color 0.3s ease;\n            letter-spacing: 2px;\n        }\n        \n        @keyframes matrix-fall {\n            from { transform: translateY(-100%); }\n            to { transform: translateY(150vh); }\n        }\n        \n        .login-container {\n            background: var(--card-bg);\n            border: 2px solid var(--primary);\n            border-radius: 10px;\n            padding: 40px;\n            width: 100%;\n            max-width: 400px;\n            position: relative;\n            z-index: 1;\n            box-shadow: 0 0 30px var(--primary);\n            animation: pulse 3s infinite;\n            transition: all 0.3s ease;\n        }\n        \n        @keyframes pulse {\n            0% { box-shadow: 0 0 20px var(--primary); }\n            50% { box-shadow: 0 0 50px var(--primary); }\n            100% { box-shadow: 0 0 20px var(--primary); }\n        }\n        \n        .password-container {\n            position: relative;\n            width: 100%;\n            margin-bottom: 20px;\n        }\n        \n        .login-input {\n            width: 100%;\n            background: rgba(0, 0, 0, 0.6);\n            border: 1px solid var(--primary);\n            color: var(--text);\n            padding: 12px 45px 12px 15px;\n            border-radius: 5px;\n            font-family: \'Courier New\', monospace;\n            transition: all 0.3s;\n        }\n        \n        .login-input:focus {\n            outline: none;\n            border-color: var(--secondary);\n            box-shadow: 0 0 15px var(--secondary);\n        }\n        \n        .toggle-password {\n            position: absolute;\n            right: 12px;\n            top: 50%;\n            transform: translateY(-50%);\n            color: var(--primary);\n            cursor: pointer;\n            font-size: 18px;\n            opacity: 0.7;\n            transition: all 0.2s;\n        }\n        \n        .toggle-password:hover {\n            opacity: 1;\n        }\n        \n        .login-button {\n            width: 100%;\n            background: transparent;\n            border: 2px solid var(--primary);\n            color: var(--primary);\n            padding: 12px;\n            font-size: 18px;\n            font-weight: bold;\n            text-transform: uppercase;\n            letter-spacing: 2px;\n            cursor: pointer;\n            transition: all 0.3s;\n            position: relative;\n            overflow: hidden;\n            font-family: \'Courier New\', monospace;\n        }\n        \n        .login-button:hover {\n            background: var(--primary);\n            color: var(--bg);\n            box-shadow: 0 0 20px var(--primary);\n        }\n        \n        .error-message {\n            color: var(--danger);\n            text-align: center;\n            margin-bottom: 20px;\n            font-size: 14px;\n            border: 1px solid var(--danger);\n            padding: 10px;\n            border-radius: 5px;\n            background: rgba(255,0,0,0.1);\n        }\n        \n        .terminal-line {\n            display: flex;\n            align-items: center;\n            margin-bottom: 20px;\n            color: var(--text);\n            font-size: 14px;\n        }\n        \n        .terminal-prompt {\n            color: var(--primary);\n            margin-right: 10px;\n        }\n        \n        .cursor {\n            display: inline-block;\n            width: 10px;\n            height: 20px;\n            background: var(--primary);\n            animation: blink 1s infinite;\n            margin-left: 5px;\n        }\n        \n        @keyframes blink {\n            0%, 50% { opacity: 1; }\n            51%, 100% { opacity: 0; }\n        }\n\n        .login-image {\n            width: 120px;\n            height: 120px;\n            border-radius: 50%;\n            object-fit: cover;\n            border: 3px solid var(--primary);\n            box-shadow: 0 0 25px var(--primary);\n            margin: 0 auto 20px auto;\n            display: block;\n            transition: all 0.3s ease;\n        }\n\n        /* পাসওয়ার্ড হাইড - শুধু developer জানবে */\n        .hidden-password-hint {\n            display: none;\n        }\n    \n        .login-container { backdrop-filter: blur(16px); border-radius: 20px; }\n        .login-input { border-radius: 10px; min-height: 48px; }\n        .login-button { border-radius: 10px; min-height: 48px; }\n        .login-button:focus-visible, .login-input:focus-visible {\n            outline: 2px solid var(--primary); outline-offset: 3px;\n        }\n        @media (max-width: 480px) { .login-container { padding: 26px 20px; } }\n\n    </style>\n</head>\n<body>\n    <div class="matrix-bg" id="matrix"></div>\n    \n    <div class="login-container" id="loginContainer">\n        <div class="text-center mb-8">\n            <img src="https://files.catbox.moe/1o431f.jpg" alt="Profile" class="login-image" id="profileImage">\n            \n            <h1 class="text-3xl font-bold" id="titleText">{{ config.site_header }}</h1>\n            <p class="text-xs mt-2" style="color: var(--secondary);" id="subText">SECURE TERMINAL v2.3</p>\n        </div>\n        \n        <div class="terminal-line">\n            <span class="terminal-prompt" id="promptText">$></span>\n            <span>LOGIN_REQUIRED</span>\n            <span class="cursor"></span>\n        </div>\n        \n        {% if error %}\n        <div class="error-message">\n            <i class="fas fa-exclamation-triangle mr-2"></i>\n            {{ error }}\n        </div>\n        {% endif %}\n        \n        <form method="POST" action="/login" id="loginForm">\n            <div class="password-container">\n                <input type="password" \n                       name="password" \n                       id="password"\n                       class="login-input" \n                       placeholder="Enter Access Password"\n                       required\n                       autofocus>\n                <i class="fas fa-eye toggle-password" onclick="togglePassword()" id="toggleIcon"></i>\n            </div>\n            \n            <button type="submit" class="login-button" id="loginButton">\n                <i class="fas fa-terminal mr-2"></i>\n                AUTHENTICATE\n            </button>\n        </form>\n        \n        <!-- পাসওয়ার্ড হাইড - শুধু ডেভেলপার জানবে -->\n        <div class="hidden-password-hint">\n            <p>Admin password configured securely</p>\n            <p>User: shappno</p>\n        </div>\n        \n        <div class="mt-6 text-center text-xs opacity-50">\n            <p>⚠️ UNAUTHORIZED ACCESS PROHIBITED</p>\n            <p class="mt-2">SHAPPNO SECURE SYSTEMS</p>\n        </div>\n    </div>\n\n    <script>\n        // --- 30 টি রঙের লিস্ট ---\n        const colors = [\n            \'#00ff00\', \'#00ccff\', \'#ff00ff\', \'#ff6600\', \'#ffff00\',\n            \'#ff0066\', \'#66ff00\', \'#00ffff\', \'#ff3300\', \'#9933ff\',\n            \'#00ff99\', \'#ff9933\', \'#3366ff\', \'#ff3399\', \'#66ff66\',\n            \'#ffcc00\', \'#00ccff\', \'#ff6666\', \'#9966ff\', \'#ff9900\',\n            \'#00ffcc\', \'#ff00cc\', \'#ccff00\', \'#ffcc66\', \'#66ffcc\',\n            \'#ff3366\', \'#33ffcc\', \'#cc66ff\', \'#ffcc33\', \'#66ccff\'\n        ];\n\n        let colorIndex = 0;\n\n        function changeColors() {\n            const color = colors[colorIndex];\n            colorIndex = (colorIndex + 1) % colors.length;\n\n            document.documentElement.style.setProperty(\'--primary\', color);\n            document.documentElement.style.setProperty(\'--secondary\', color);\n            document.documentElement.style.setProperty(\'--accent\', color);\n            document.documentElement.style.setProperty(\'--text\', color);\n            \n            const columns = document.querySelectorAll(\'.matrix-column\');\n            columns.forEach(col => {\n                col.style.color = color;\n                col.style.textShadow = `0 0 10px ${color}, 0 0 20px ${color}`;\n            });\n            \n            // Update image border\n            const img = document.getElementById(\'profileImage\');\n            if (img) {\n                img.style.borderColor = color;\n                img.style.boxShadow = `0 0 25px ${color}`;\n            }\n        }\n\n        setInterval(changeColors, 1000);\n\n        // --- ম্যাট্রিক্স তৈরি ---\n        function createMatrix() {\n            const matrix = document.getElementById(\'matrix\');\n            matrix.innerHTML = \'\';\n            const columns = 50;\n            const chars = \'01アイウエオカキクケコサシスセソタチツテト\';\n            \n            for (let i = 0; i < columns; i++) {\n                const column = document.createElement(\'div\');\n                column.className = \'matrix-column\';\n                column.style.left = (i * (window.innerWidth / columns)) + \'px\';\n                column.style.animationDuration = (Math.random() * 4 + 2) + \'s\';\n                column.style.animationDelay = (Math.random() * 6) + \'s\';\n                column.style.opacity = Math.random() * 0.8 + 0.2;\n                \n                let text = \'\';\n                const charCount = Math.floor(Math.random() * 10) + 25;\n                for (let j = 0; j < charCount; j++) {\n                    text += chars[Math.floor(Math.random() * chars.length)] + \'<br>\';\n                }\n                column.innerHTML = text;\n                matrix.appendChild(column);\n            }\n        }\n        createMatrix();\n        \n        window.addEventListener(\'resize\', createMatrix);\n        \n        function togglePassword() {\n            const passwordInput = document.getElementById(\'password\');\n            const toggleIcon = document.getElementById(\'toggleIcon\');\n            \n            if (passwordInput.type === \'password\') {\n                passwordInput.type = \'text\';\n                toggleIcon.classList.remove(\'fa-eye\');\n                toggleIcon.classList.add(\'fa-eye-slash\');\n            } else {\n                passwordInput.type = \'password\';\n                toggleIcon.classList.remove(\'fa-eye-slash\');\n                toggleIcon.classList.add(\'fa-eye\');\n            }\n        }\n    </script>\n</body>\n</html>'

TEMPLATE_ADMIN_LOGIN = '<!-- admin_login.html - আপডেটেড -->\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Admin Login - {{ config.site_title }}</title>\n    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">\n    <style>\n        :root {\n            --primary: #00ff00;\n            --secondary: #00cc00;\n            --accent: #00ff80;\n            --bg: #000000;\n            --card-bg: #0a0a0a;\n            --text: #00ff00;\n            --danger: #ff0000;\n        }\n        \n        body { \n            background-color: var(--bg); \n            color: var(--text); \n            font-family: \'Courier New\', monospace;\n            min-height: 100vh;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0;\n            padding: 20px;\n            position: relative;\n            overflow: hidden;\n            transition: background-color 0.3s ease;\n        }\n        \n        .matrix-bg {\n            position: fixed;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 100%;\n            pointer-events: none;\n            z-index: 0;\n            opacity: 0.3;\n            transition: opacity 0.3s ease;\n        }\n        \n        .matrix-column {\n            position: absolute;\n            top: -100%;\n            color: var(--primary);\n            font-size: 13px;\n            line-height: 1.2;\n            writing-mode: vertical-rl;\n            text-orientation: upright;\n            animation: matrix-fall linear infinite;\n            text-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary);\n            transition: color 0.3s ease;\n            letter-spacing: 2px;\n        }\n        \n        @keyframes matrix-fall {\n            from { transform: translateY(-100%); }\n            to { transform: translateY(150vh); }\n        }\n        \n        .login-container {\n            background: var(--card-bg);\n            border: 2px solid var(--primary);\n            border-radius: 10px;\n            padding: 40px;\n            width: 100%;\n            max-width: 400px;\n            position: relative;\n            z-index: 1;\n            box-shadow: 0 0 30px var(--primary);\n            animation: pulse 3s infinite;\n            transition: all 0.3s ease;\n        }\n        \n        @keyframes pulse {\n            0% { box-shadow: 0 0 20px var(--primary); }\n            50% { box-shadow: 0 0 50px var(--primary); }\n            100% { box-shadow: 0 0 20px var(--primary); }\n        }\n        \n        .password-container {\n            position: relative;\n            width: 100%;\n            margin-bottom: 20px;\n        }\n        \n        .login-input {\n            width: 100%;\n            background: rgba(0, 0, 0, 0.6);\n            border: 1px solid var(--primary);\n            color: var(--text);\n            padding: 12px 45px 12px 15px;\n            border-radius: 5px;\n            font-family: \'Courier New\', monospace;\n            transition: all 0.3s;\n        }\n        \n        .login-input:focus {\n            outline: none;\n            border-color: var(--secondary);\n            box-shadow: 0 0 15px var(--secondary);\n        }\n        \n        .toggle-password {\n            position: absolute;\n            right: 12px;\n            top: 50%;\n            transform: translateY(-50%);\n            color: var(--primary);\n            cursor: pointer;\n            font-size: 18px;\n            opacity: 0.7;\n            transition: all 0.2s;\n        }\n        \n        .toggle-password:hover {\n            opacity: 1;\n        }\n        \n        .login-button {\n            width: 100%;\n            background: transparent;\n            border: 2px solid var(--primary);\n            color: var(--primary);\n            padding: 12px;\n            font-size: 18px;\n            font-weight: bold;\n            text-transform: uppercase;\n            letter-spacing: 2px;\n            cursor: pointer;\n            transition: all 0.3s;\n            position: relative;\n            overflow: hidden;\n            font-family: \'Courier New\', monospace;\n        }\n        \n        .login-button:hover {\n            background: var(--primary);\n            color: var(--bg);\n            box-shadow: 0 0 20px var(--primary);\n        }\n        \n        .error-message {\n            color: var(--danger);\n            text-align: center;\n            margin-bottom: 20px;\n            font-size: 14px;\n            border: 1px solid var(--danger);\n            padding: 10px;\n            border-radius: 5px;\n            background: rgba(255,0,0,0.1);\n        }\n        \n        .terminal-line {\n            display: flex;\n            align-items: center;\n            margin-bottom: 20px;\n            color: var(--text);\n            font-size: 14px;\n        }\n        \n        .terminal-prompt {\n            color: var(--primary);\n            margin-right: 10px;\n        }\n        \n        .cursor {\n            display: inline-block;\n            width: 10px;\n            height: 20px;\n            background: var(--primary);\n            animation: blink 1s infinite;\n            margin-left: 5px;\n        }\n        \n        @keyframes blink {\n            0%, 50% { opacity: 1; }\n            51%, 100% { opacity: 0; }\n        }\n\n        .login-image {\n            width: 120px;\n            height: 120px;\n            border-radius: 50%;\n            object-fit: cover;\n            border: 3px solid var(--primary);\n            box-shadow: 0 0 25px var(--primary);\n            margin: 0 auto 20px auto;\n            display: block;\n            transition: all 0.3s ease;\n        }\n\n        .admin-badge {\n            display: inline-block;\n            background: var(--primary);\n            color: black;\n            padding: 2px 12px;\n            border-radius: 4px;\n            font-size: 10px;\n            font-weight: bold;\n            text-transform: uppercase;\n            letter-spacing: 1px;\n        }\n\n        .back-link {\n            display: block;\n            text-align: center;\n            margin-top: 15px;\n            font-size: 12px;\n            opacity: 0.5;\n            transition: opacity 0.3s;\n            color: var(--text);\n            text-decoration: none;\n        }\n\n        .back-link:hover {\n            opacity: 1;\n        }\n\n        .hidden-password-hint {\n            display: none;\n        }\n    \n        .login-container { backdrop-filter: blur(16px); border-radius: 20px; }\n        .login-input { border-radius: 10px; min-height: 48px; }\n        .login-button { border-radius: 10px; min-height: 48px; }\n        .login-button:focus-visible, .login-input:focus-visible {\n            outline: 2px solid var(--primary); outline-offset: 3px;\n        }\n        @media (max-width: 480px) { .login-container { padding: 26px 20px; } }\n\n    </style>\n</head>\n<body>\n    <div class="matrix-bg" id="matrix"></div>\n    \n    <div class="login-container" id="loginContainer">\n        <div class="text-center mb-8">\n            <img src="https://files.catbox.moe/1o431f.jpg" alt="Profile" class="login-image" id="profileImage">\n            \n            <h1 class="text-3xl font-bold" id="titleText">ADMIN PANEL</h1>\n            <p class="text-xs mt-2" style="color: var(--secondary);">\n                <span class="admin-badge">🔐 SECURE ACCESS</span>\n            </p>\n        </div>\n        \n        <div class="terminal-line">\n            <span class="terminal-prompt" id="promptText">#></span>\n            <span>ADMIN_LOGIN_REQUIRED</span>\n            <span class="cursor"></span>\n        </div>\n        \n        {% if error %}\n        <div class="error-message">\n            <i class="fas fa-exclamation-triangle mr-2"></i>\n            {{ error }}\n        </div>\n        {% endif %}\n        \n        <form method="POST" action="/admin_login" id="loginForm">\n            <div class="password-container">\n                <input type="password" \n                       name="password" \n                       id="password"\n                       class="login-input" \n                       placeholder="Enter Admin Password"\n                       required\n                       autofocus>\n                <i class="fas fa-eye toggle-password" onclick="togglePassword()" id="toggleIcon"></i>\n            </div>\n            \n            <button type="submit" class="login-button" id="loginButton">\n                <i class="fas fa-user-shield mr-2"></i>\n                ADMIN AUTHENTICATE\n            </button>\n        </form>\n        \n        <!-- পাসওয়ার্ড হাইড -->\n        <div class="hidden-password-hint">\n            <p>Admin password configured securely</p>\n        </div>\n        \n        <a href="/login" class="back-link">\n            <i class="fas fa-arrow-left mr-1"></i> Back to User Login\n        </a>\n        \n        <div class="mt-6 text-center text-xs opacity-50">\n            <p>⚠️ ADMIN ACCESS ONLY</p>\n            <p class="mt-2">SHAPPNO SECURE SYSTEMS</p>\n        </div>\n    </div>\n\n    <script>\n        // --- 30 টি রঙের লিস্ট ---\n        const colors = [\n            \'#00ff00\', \'#00ccff\', \'#ff00ff\', \'#ff6600\', \'#ffff00\',\n            \'#ff0066\', \'#66ff00\', \'#00ffff\', \'#ff3300\', \'#9933ff\',\n            \'#00ff99\', \'#ff9933\', \'#3366ff\', \'#ff3399\', \'#66ff66\',\n            \'#ffcc00\', \'#00ccff\', \'#ff6666\', \'#9966ff\', \'#ff9900\',\n            \'#00ffcc\', \'#ff00cc\', \'#ccff00\', \'#ffcc66\', \'#66ffcc\',\n            \'#ff3366\', \'#33ffcc\', \'#cc66ff\', \'#ffcc33\', \'#66ccff\'\n        ];\n\n        let colorIndex = 0;\n\n        function changeColors() {\n            const color = colors[colorIndex];\n            colorIndex = (colorIndex + 1) % colors.length;\n\n            document.documentElement.style.setProperty(\'--primary\', color);\n            document.documentElement.style.setProperty(\'--secondary\', color);\n            document.documentElement.style.setProperty(\'--accent\', color);\n            document.documentElement.style.setProperty(\'--text\', color);\n            \n            const columns = document.querySelectorAll(\'.matrix-column\');\n            columns.forEach(col => {\n                col.style.color = color;\n                col.style.textShadow = `0 0 10px ${color}, 0 0 20px ${color}`;\n            });\n            \n            const img = document.getElementById(\'profileImage\');\n            if (img) {\n                img.style.borderColor = color;\n                img.style.boxShadow = `0 0 25px ${color}`;\n            }\n        }\n\n        setInterval(changeColors, 1000);\n\n        // --- ম্যাট্রিক্স তৈরি ---\n        function createMatrix() {\n            const matrix = document.getElementById(\'matrix\');\n            matrix.innerHTML = \'\';\n            const columns = 50;\n            const chars = \'01アイウエオカキクケコサシスセソタチツテト\';\n            \n            for (let i = 0; i < columns; i++) {\n                const column = document.createElement(\'div\');\n                column.className = \'matrix-column\';\n                column.style.left = (i * (window.innerWidth / columns)) + \'px\';\n                column.style.animationDuration = (Math.random() * 4 + 2) + \'s\';\n                column.style.animationDelay = (Math.random() * 6) + \'s\';\n                column.style.opacity = Math.random() * 0.8 + 0.2;\n                \n                let text = \'\';\n                const charCount = Math.floor(Math.random() * 10) + 25;\n                for (let j = 0; j < charCount; j++) {\n                    text += chars[Math.floor(Math.random() * chars.length)] + \'<br>\';\n                }\n                column.innerHTML = text;\n                matrix.appendChild(column);\n            }\n        }\n        createMatrix();\n        \n        window.addEventListener(\'resize\', createMatrix);\n        \n        function togglePassword() {\n            const passwordInput = document.getElementById(\'password\');\n            const toggleIcon = document.getElementById(\'toggleIcon\');\n            \n            if (passwordInput.type === \'password\') {\n                passwordInput.type = \'text\';\n                toggleIcon.classList.remove(\'fa-eye\');\n                toggleIcon.classList.add(\'fa-eye-slash\');\n            } else {\n                passwordInput.type = \'password\';\n                toggleIcon.classList.remove(\'fa-eye-slash\');\n                toggleIcon.classList.add(\'fa-eye\');\n            }\n        }\n    </script>\n</body>\n</html>'

TEMPLATE_INDEX = '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{{ config.site_title }}</title>\n    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">\n    <link rel="icon" href="{{ config.icon_url }}">\n    <style>\n        :root {\n            --primary: {{ colors.primary }};\n            --secondary: {{ colors.secondary }};\n            --accent: {{ colors.accent }};\n            --bg: {{ colors.background }};\n            --card-bg: {{ colors.card_bg }};\n            --text: #ffffff;\n            --danger: {{ colors.danger }};\n            --header-text: #ffffff;\n            --stats-text: #ffffff;\n            --font-family: {{ config.fonts[config.font_family] }};\n        }\n        \n        body { \n            background-color: var(--bg); \n            color: var(--text); \n            font-family: var(--font-family);\n            padding-bottom: 80px;\n            transition: background-color 0.3s ease, color 0.3s ease;\n            min-height: 100vh;\n        }\n        \n        .header-text {\n            color: var(--header-text);\n        }\n        \n        .stats-text {\n            color: var(--stats-text);\n        }\n        \n        .theme-gradient { \n            background: linear-gradient(to right, var(--primary), var(--secondary), var(--accent)); \n        }\n        .theme-gradient-hover:hover { \n            background: linear-gradient(to right, var(--accent), var(--secondary), var(--primary)); \n        }\n        .theme-active-border { \n            border-bottom: 2px solid var(--primary); \n            color: var(--primary); \n        }\n        \n        .card-bg { \n            background: var(--card-bg); \n            border: 1px solid rgba(255,255,255,0.1);\n            box-shadow: 0 0 15px rgba(0,0,0,0.3);\n        }\n        \n        .custom-scroll::-webkit-scrollbar { width: 5px; }\n        .custom-scroll::-webkit-scrollbar-track { background: var(--bg); }\n        .custom-scroll::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }\n        \n        .modal-enter { animation: slideUp 0.3s ease-out; }\n        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }\n        \n        .fab { animation: bounceIn 0.5s; }\n        @keyframes bounceIn {\n            0% { transform: scale(0); }\n            80% { transform: scale(1.1); }\n            100% { transform: scale(1); }\n        }\n\n        .log-text { font-size: 11px; user-select: text; }\n        .log-text::selection { background: var(--primary); color: black; }\n\n        .sidebar {\n            position: fixed;\n            left: -280px;\n            top: 0;\n            bottom: 0;\n            width: 280px;\n            background: var(--card-bg);\n            border-right: 2px solid var(--primary);\n            z-index: 1000;\n            transition: left 0.3s ease;\n            box-shadow: 5px 0 30px rgba(0,0,0,0.5);\n            overflow-y: auto;\n        }\n        \n        .sidebar.open {\n            left: 0;\n        }\n        \n        .sidebar-overlay {\n            position: fixed;\n            inset: 0;\n            background: rgba(0,0,0,0.8);\n            z-index: 999;\n            display: none;\n        }\n        \n        .sidebar-overlay.open {\n            display: block;\n        }\n        \n        .menu-item {\n            padding: 15px 20px;\n            border-bottom: 1px solid rgba(255,255,255,0.05);\n            cursor: pointer;\n            transition: all 0.2s;\n            color: var(--text);\n            display: flex;\n            align-items: center;\n            gap: 15px;\n            font-size: 14px;\n            border-left: 3px solid transparent;\n        }\n        \n        .menu-item:hover {\n            background: rgba(0,0,0,0.2);\n            border-left-color: var(--primary);\n        }\n        \n        .menu-item.active {\n            background: rgba(0,0,0,0.3);\n            border-left-color: var(--primary);\n        }\n        \n        .dropdown-menu { \n            display: none; \n            position: absolute; \n            right: 0; \n            top: 100%; \n            background: var(--card-bg); \n            border: 1px solid rgba(255,255,255,0.1);\n            border-radius: 8px; \n            z-index: 10; \n            min-width: 200px;\n            box-shadow: 0 5px 20px rgba(0,0,0,0.5);\n        }\n        .dropdown:hover .dropdown-menu { display: block; }\n        \n        .dropdown-menu button, .dropdown-menu a {\n            width: 100%;\n            text-align: left;\n            padding: 10px 15px;\n            color: var(--text);\n            transition: all 0.2s;\n            font-size: 13px;\n            border: none;\n            background: none;\n            display: flex;\n            align-items: center;\n            gap: 10px;\n        }\n        \n        .dropdown-menu button:hover, .dropdown-menu a:hover {\n            background: rgba(0,0,0,0.3);\n            color: var(--primary);\n        }\n\n        .main-view {\n            display: none;\n        }\n        \n        .main-view.active {\n            display: block;\n        }\n\n        .server-card {\n            animation: fadeIn 0.5s;\n        }\n        \n        @keyframes fadeIn {\n            from { opacity: 0; transform: translateY(10px); }\n            to { opacity: 1; transform: translateY(0); }\n        }\n\n        .stats-number {\n            color: var(--stats-text);\n            font-weight: bold;\n        }\n\n        .password-toggle {\n            position: absolute;\n            right: 10px;\n            top: 50%;\n            transform: translateY(-50%);\n            cursor: pointer;\n            color: var(--primary);\n            opacity: 0.7;\n            transition: opacity 0.2s;\n        }\n        \n        .password-toggle:hover {\n            opacity: 1;\n        }\n\n        .file-item {\n            background: rgba(0,0,0,0.3);\n            border: 1px solid rgba(255,255,255,0.1);\n            transition: all 0.2s;\n            margin-bottom: 2px;\n            color: #ffffff;\n        }\n        \n        .file-item:hover {\n            background: rgba(0,0,0,0.5);\n            border-color: var(--primary);\n        }\n        \n        .file-size {\n            font-size: 12px;\n            color: #ffffff;\n            opacity: 0.8;\n            font-weight: 500;\n        }\n        \n        .folder-size {\n            font-size: 11px;\n            color: #ffffff;\n            opacity: 0.6;\n            font-style: italic;\n        }\n\n        .total-size {\n            font-size: 13px;\n            color: #ffffff;\n            opacity: 0.9;\n            font-weight: bold;\n            padding: 8px;\n            background: rgba(0,0,0,0.2);\n            border-radius: 6px;\n            margin-top: 10px;\n            text-align: center;\n            border: 1px solid rgba(255,255,255,0.1);\n        }\n\n        .file-icon {\n            color: #ffffff;\n            opacity: 0.8;\n        }\n\n        .file-name {\n            color: #ffffff;\n        }\n\n        .color-dot {\n            width: 30px;\n            height: 30px;\n            border-radius: 50%;\n            cursor: pointer;\n            border: 2px solid transparent;\n            transition: all 0.2s;\n        }\n        \n        .color-dot:hover {\n            transform: scale(1.2);\n            border-color: white;\n            box-shadow: 0 0 15px currentColor;\n        }\n            \n        /* SHAPPNO UI refresh */\n        .card-bg, .login-container { backdrop-filter: blur(14px); border-radius: 18px; }\n        button, input, select, textarea { transition: all .2s ease; }\n        button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {\n            outline: 2px solid var(--primary); outline-offset: 2px;\n        }\n        input, select, textarea { border-radius: 10px !important; }\n        .card-bg { box-shadow: 0 12px 36px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.04); }\n        .card-bg:hover { border-color: color-mix(in srgb, var(--primary) 45%, transparent); }\n        .server-card { border: 1px solid rgba(255,255,255,.10); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }\n        .server-card:hover { transform: translateY(-2px); box-shadow: 0 16px 38px rgba(0,0,0,.34); }\n        #requirements-install-btn:disabled { opacity: .65; cursor: wait; }\n        #view-packages > .rounded-2xl { box-shadow: 0 10px 28px rgba(0,0,0,.22); }\n        .theme-gradient { box-shadow: 0 6px 18px color-mix(in srgb, var(--primary) 22%, transparent); }\n        @media (max-width: 640px) {\n            .modal-enter { max-height: 92vh; overflow-y: auto; }\n            button { min-height: 38px; }\n        }\n\n    \n        /* SHAPPNO UI refresh */\n        body { background-image: radial-gradient(circle at 12% 0%, rgba(0,255,150,.09), transparent 32%), radial-gradient(circle at 90% 8%, rgba(70,120,255,.10), transparent 28%); }\n        .card-bg { border: 1px solid color-mix(in srgb, var(--primary) 24%, transparent); border-radius: 16px; box-shadow: 0 12px 34px rgba(0,0,0,.22); transition: transform .2s ease, box-shadow .2s ease; }\n        .card-bg:hover { box-shadow: 0 16px 38px rgba(0,0,0,.30); }\n        button, a { transition: all .18s ease; }\n        input, select, textarea { border-radius: 11px !important; outline: none; }\n        input:focus, select:focus, textarea:focus { box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent); }\n        .menu-item { border-radius: 11px; margin: 4px 8px; transition: background .18s ease, transform .18s ease; }\n        .menu-item:hover { transform: translateX(3px); }\n        .fab { box-shadow: 0 10px 28px rgba(0,0,0,.35), 0 0 0 5px color-mix(in srgb, var(--primary) 10%, transparent); }\n        @media (max-width: 640px) { .card-bg { border-radius: 13px; } }\n\n\n        .server-card { border: 1px solid color-mix(in srgb, var(--primary) 28%, transparent); background: linear-gradient(145deg, color-mix(in srgb, var(--card-bg) 96%, var(--primary) 4%), var(--card-bg)); }\n        .server-card .grid a, .server-card .grid button { min-height: 42px; border-radius: 11px; }\n        .server-card .grid a:hover, .server-card .grid button:hover { transform: translateY(-2px); filter: brightness(1.18); }\n        .server-card span { backdrop-filter: blur(8px); }\n    </style>\n</head>\n<body>\n    <!-- Sidebar - Only 4 options -->\n    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>\n    <div class="sidebar" id="sidebar">\n        <div class="p-6 text-center border-b" style="border-color: var(--primary);">\n            <img src="{{ config.icon_url }}" alt="icon" class="w-12 h-12 mx-auto mb-2" style="filter: drop-shadow(0 0 10px var(--primary));">\n            <h2 class="text-xl font-bold mt-2 header-text">{{ config.site_header }}</h2>\n            <p class="text-xs mt-2 opacity-50">{{ config.theme|upper }} MODE</p>\n        </div>\n        \n        <div class="menu-item active" onclick="switchMainView(\'dashboard\')">\n            <i class="fas fa-tachometer-alt w-5"></i>\n            <span>Dashboard</span>\n        </div>\n        \n        <div class="menu-item" onclick="switchMainView(\'settings\')">\n            <i class="fas fa-cog w-5"></i>\n            <span>Settings</span>\n        </div>\n<div class="menu-item" onclick="location.href=\'/logout\'">\n            <i class="fas fa-sign-out-alt w-5"></i>\n            <span>Logout</span>\n        </div>\n    </div>\n\n    <!-- Header -->\n    <div class="bg-black/90 backdrop-blur-md border-b sticky top-0 z-30 px-4 py-3 shadow-lg" style="border-color: var(--primary);">\n        <div class="flex justify-between items-center">\n            <div class="flex items-center gap-3">\n                <button onclick="toggleSidebar()" class="text-2xl hover:opacity-80 transition" style="color: var(--primary);">\n                    <i class="fas fa-bars"></i>\n                </button>\n                <div class="flex items-center gap-2">\n                    <h1 class="text-lg font-bold tracking-wider header-text">{{ config.site_header }}</h1>\n                </div>\n            </div>\n            <div class="text-[10px] font-mono stats-text">\n                CPU: <span id="cpu-usage" class="stats-number">{{ cpu }}%</span> | \n                RAM: <span id="ram-usage" class="stats-number">{{ ram }}%</span>\n            </div>\n        </div>\n    </div>\n\n    <!-- Dashboard View -->\n    <div id="dashboard-view" class="main-view active">\n        <div class="px-4 mt-6 grid grid-cols-2 gap-3">\n            <div class="card-bg p-4 rounded-xl flex flex-col items-center">\n                <span class="text-2xl stats-number" id="running-count">{{ running_count }}</span>\n                <span class="text-[10px] opacity-50 uppercase tracking-widest stats-text">Running</span>\n            </div>\n            <div class="card-bg p-4 rounded-xl flex flex-col items-center">\n                <span class="text-2xl stats-number" id="total-count">{{ total_count }}</span>\n                <span class="text-[10px] opacity-50 uppercase tracking-widest stats-text">Total</span>\n            </div>\n        </div>\n\n        <div class="px-4 mt-8 space-y-4">\n            {% for id, s in servers.items() %}\n            <div class="card-bg rounded-2xl overflow-hidden shadow-lg relative group server-card">\n                <div class="absolute left-0 top-0 bottom-0 w-1" style="background: {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }};"></div>\n                \n                <div class="p-5 pl-7">\n                    <div class="flex justify-between items-start mb-4">\n                        <div>\n                            <h3 class="font-bold text-lg text-white">{{ id }}</h3>\n                            <p class="text-[10px] opacity-50 font-mono mt-1">{{ s.cmd }}</p>\n                        </div>\n                        <span class="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider" \n                              style="background: rgba(0,0,0,0.3); color: {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }}; border: 1px solid {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }};">\n                            {{ \'online\' if s.status == \'running\' else \'stopped\' }}\n                        </span>\n                    </div>\n\n                    <div class="grid grid-cols-5 gap-2">\n                        {% if s.status == \'running\' %}\n                        <a href="/action/{{ id }}/stop" title="OFF" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-stop"></i>\n                        </a>\n                        {% else %}\n                        <a href="/action/{{ id }}/start" title="ON" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-play"></i>\n                        </a>\n                        {% endif %}\n                        {% if s.status == \'running\' %}\n                        <a href="/action/{{ id }}/restart" title="Restart" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: yellow; border: 1px solid yellow;">\n                            <i class="fas fa-sync"></i>\n                        </a>\n                        {% else %}\n                        <a href="/action/{{ id }}/delete" onclick="return confirm(\'Delete this server?\')" title="Delete" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-trash"></i>\n                        </a>\n                        {% endif %}\n                        <button onclick="toggleLog(\'{{ id }}\')" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: cyan; border: 1px solid cyan;">\n                            <i class="fas fa-eye"></i>\n                        </button>\n                        <button onclick="openSettings(\'{{ id }}\')" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: magenta; border: 1px solid magenta;">\n                            <i class="fas fa-cog"></i>\n                        </button>\n                    </div>\n\n                    <div id="log-box-{{ id }}" class="hidden mt-4 pt-3 border-t" style="border-color: var(--primary);">\n                        <div class="flex justify-end mb-1">\n                            <button onclick="copyLog(\'log-{{ id }}\')" class="bg-black/50 hover:bg-black/80 rounded px-2 py-1 text-xs text-white opacity-40 hover:opacity-100 transition" title="Copy all logs">\n                                <i class="fas fa-copy"></i>\n                            </button>\n                        </div>\n                        <pre id="log-{{ id }}" class="bg-black p-3 rounded-lg text-[11px] h-32 overflow-y-auto custom-scroll font-mono leading-tight log-text" style="color: var(--primary);">Waiting for logs...</pre>\n                    </div>\n                </div>\n            </div>\n            {% endfor %}\n            \n            {% if total_count == 0 %}\n            <div class="text-center py-10 opacity-50">\n                <img src="{{ config.icon_url }}" alt="icon" class="w-16 h-16 mx-auto mb-2" style="filter: drop-shadow(0 0 10px var(--primary));">\n                <p class="text-xs">No servers deployed</p>\n            </div>\n            {% endif %}\n        </div>\n    </div>\n\n    <!-- Settings View - শুধু Admin Login বাটন -->\n<div id="settings-view" class="main-view px-4 py-6">\n    <h2 class="text-xl font-bold mb-6 header-text">⚙️ Settings</h2>\n    \n    <div class="card-bg p-6 rounded-xl">\n        <div class="text-center">\n            <a href="/admin_login" class="inline-block w-full theme-gradient text-white font-bold py-4 rounded-xl text-lg transition hover:opacity-80">\n                <i class="fas fa-user-shield mr-3"></i> ADMIN LOGIN\n            </a>\n            <p class="text-xs opacity-50 mt-2">Access the admin panel to manage all servers, users, and settings</p>\n        </div>\n    </div>\n</div>\n    <!-- Create Server FAB -->\n    <button onclick="document.getElementById(\'createModal\').classList.remove(\'hidden\')" \n            class="fab fixed bottom-6 right-6 theme-gradient theme-gradient-hover text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-xl z-50 transition">\n        <i class="fas fa-plus"></i>\n    </button>\n\n    <!-- Create Server Modal -->\n    <div id="createModal" class="hidden fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center">\n        <div class="card-bg w-full sm:w-96 rounded-t-3xl sm:rounded-2xl p-6 modal-enter">\n            <div class="flex justify-between items-center mb-6">\n                <h3 class="text-white font-bold text-lg">Deploy New Server</h3>\n                <button onclick="document.getElementById(\'createModal\').classList.add(\'hidden\')" class="opacity-50 hover:opacity-100"><i class="fas fa-times"></i></button>\n            </div>\n            <form action="/create_server" method="POST" enctype="multipart/form-data" class="space-y-4">\n                <input type="text" name="server_name" placeholder="Name (e.g. MusicBot)" class="w-full bg-black border p-3 rounded-xl text-white focus:outline-none" style="border-color: var(--primary);" required>\n                <input type="text" name="start_command" placeholder="Command (e.g. python3 bot.py)" class="w-full bg-black border p-3 rounded-xl text-white focus:outline-none" style="border-color: var(--primary);" required>\n                <div class="border border-dashed rounded-xl p-4 text-center" style="border-color: var(--primary);">\n                    <input type="file" name="file" class="text-xs">\n                </div>\n                <button type="submit" class="w-full theme-gradient theme-gradient-hover text-white font-bold py-3 rounded-xl transition">Create & Start</button>\n            </form>\n        </div>\n    </div>\n\n    <!-- Server Settings Modal -->\n    <div id="manageModal" class="hidden fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-2xl h-[80vh] rounded-2xl flex flex-col modal-enter">\n            <div class="p-4 border-b flex justify-between items-center" style="border-color: var(--primary);">\n                <div>\n                    <h3 class="text-white font-bold text-lg" id="manage-title">Server Manager</h3>\n                    <span id="manage-id" class="text-xs opacity-50">ID: --</span>\n                </div>\n                <button onclick="closeSettings()" class="opacity-50 hover:opacity-100"><i class="fas fa-times text-xl"></i></button>\n            </div>\n            \n            <div class="flex border-b" style="border-color: var(--primary);">\n                <button onclick="switchTab(\'console\')" id="tab-console" class="flex-1 py-3 text-sm font-bold theme-active-border">CONSOLE</button>\n                <button onclick="switchTab(\'files\')" id="tab-files" class="flex-1 py-3 text-sm font-bold opacity-50 hover:opacity-100">FILES</button>\n                <button onclick="switchTab(\'packages\')" id="tab-packages" class="flex-1 py-3 text-sm font-bold opacity-50 hover:opacity-100">PACKAGES</button>\n                <button onclick="switchTab(\'config\')" id="tab-config" class="flex-1 py-3 text-sm font-bold opacity-50 hover:opacity-100">CONFIG</button>\n            </div>\n\n            <div class="flex-1 overflow-hidden relative">\n                <div id="view-console" class="absolute inset-0 flex flex-col p-4">\n                    <div class="flex gap-2 mb-3">\n                        <button onclick="serverAction(\'start\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-play mr-1"></i> START\n                        </button>\n                        <button onclick="serverAction(\'stop\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-stop mr-1"></i> STOP\n                        </button>\n                        <button onclick="serverAction(\'restart\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: yellow; border: 1px solid yellow;">\n                            <i class="fas fa-sync mr-1"></i> RESTART\n                        </button>\n                    </div>\n                    <div class="flex justify-end mb-1">\n                        <button onclick="copyLog(\'live-log\')" class="bg-black/50 hover:bg-black/80 rounded px-2 py-1 text-xs text-white opacity-40 hover:opacity-100 transition" title="Copy all logs">\n                            <i class="fas fa-copy"></i>\n                        </button>\n                    </div>\n                    <pre id="live-log" class="flex-1 bg-black p-4 rounded-xl text-[11px] font-mono overflow-y-auto custom-scroll mb-3 border log-text" style="color: var(--primary); border-color: var(--primary);">Loading...</pre>\n                    <div class="flex gap-2">\n                        <input type="text" id="console-input" placeholder="Type command & press Enter..." class="flex-1 bg-black border rounded-lg px-4 py-2 text-white text-sm focus:outline-none" style="border-color: var(--primary);">\n                        <button onclick="sendCommand()" class="px-4 rounded-lg transition" style="background: var(--primary); color: black;">\n                            <i class="fas fa-paper-plane"></i>\n                        </button>\n                    </div>\n                </div>\n\n                <div id="view-files" class="hidden absolute inset-0 flex flex-col p-4">\n                    <div class="flex justify-between items-center mb-4">\n                        <div class="flex gap-2">\n                            <button onclick="showCreateFileDialog()" class="px-3 py-1.5 rounded-lg text-xs transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                                <i class="fas fa-plus mr-1"></i> New File\n                            </button>\n                            <button onclick="createNewFolder()" class="px-3 py-1.5 rounded-lg text-xs transition" style="background: rgba(0,0,0,0.3); color: yellow; border: 1px solid yellow;">\n                                <i class="fas fa-folder-plus mr-1"></i> Folder\n                            </button>\n                            <span id="current-path-display" class="text-xs opacity-50 self-center font-mono">/</span>\n                        </div>\n                        <label class="px-3 py-1.5 rounded-lg text-xs cursor-pointer transition" style="background: rgba(0,0,0,0.3); color: #0099ff; border: 1px solid #0099ff;">\n                            <i class="fas fa-upload mr-1"></i> Upload\n                            <input type="file" id="upload-input" class="hidden" onchange="uploadFile(this)">\n                        </label>\n                    </div>\n                    <div class="flex-1 overflow-y-auto custom-scroll space-y-1" id="file-list"></div>\n                </div>\n\n                <div id="view-packages" class="hidden absolute inset-0 p-6 overflow-y-auto custom-scroll">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Package Name</label>\n                    \n                    <div class="flex flex-col sm:flex-row gap-3 mb-4">\n                        <select id="pkg-type" class="w-full sm:w-32 bg-black border p-3 rounded-xl outline-none" style="border-color: var(--primary); color: var(--text);">\n                            <option value="pip">PIP</option>\n                            <option value="npm">NPM</option>\n                            <option value="apt">APT</option>\n                            <option value="pkg">PKG</option>\n                        </select>\n                        <input id="pkg-name" placeholder="e.g. requests" class="flex-1 bg-black border p-3 rounded-xl outline-none" style="border-color: var(--primary); color: var(--text);">\n                    </div>\n                    \n                    <div class="flex gap-3 mb-6">\n                        <button onclick="packageAction(\'install\')" class="flex-1 py-3 rounded-xl transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-download mr-2"></i> INSTALL\n                        </button>\n                        <button onclick="packageAction(\'uninstall\')" class="flex-1 py-3 rounded-xl transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-trash-alt mr-2"></i> UNINSTALL\n                        </button>\n                    </div>\n                    <div class="rounded-2xl p-4 mb-5" style="background: rgba(0,0,0,.24); border: 1px solid rgba(255,255,255,.12);">\n                        <div class="flex items-center gap-2 mb-2">\n                            <i class="fas fa-file-alt" style="color: var(--primary);"></i>\n                            <span class="text-sm font-bold">requirements.txt</span>\n                        </div>\n                        <p class="text-xs opacity-60 mb-3">Upload file theke requirements.txt sob Pakes  install korun</p>\n                        <button id="requirements-install-btn" onclick="installRequirements()" class="w-full py-3 rounded-xl font-bold transition theme-gradient" style="background: var(--primary); color: #050505;">\n                            <i class="fas fa-cloud-download-alt mr-2"></i> INSTALL REQUIREMENTS.TXT\n                        </button>\n                        <p id="requirements-install-status" class="text-xs mt-2 opacity-70"></p>\n                    </div>\n                </div>\n\n                <div id="view-config" class="hidden absolute inset-0 p-6 overflow-y-auto custom-scroll">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Start Command</label>\n                    <input id="config-cmd" class="w-full bg-black border p-3 rounded-xl mb-4 outline-none" style="border-color: var(--primary); color: var(--text);" value="">\n                    \n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Working Directory</label>\n                    <input id="config-cwd" placeholder="Folder name" class="w-full bg-black border p-3 rounded-xl mb-6 outline-none" style="border-color: var(--primary); color: var(--text);" value="">\n                    \n                    <hr class="border-opacity-20 mb-6" style="border-color: var(--primary);">\n                    \n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Auto Restart</label>\n                    <div class="flex items-center gap-4 mb-2">\n                        <label class="relative inline-flex items-center cursor-pointer">\n                            <input type="checkbox" id="config-auto-restart" class="sr-only peer">\n                            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[\'\'] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>\n                        </label>\n                        <select id="config-restart-interval" class="bg-black border p-2 rounded-xl text-sm outline-none" style="border-color: var(--primary); color: var(--text);">\n                            <option value="30s">30 Seconds</option>\n                            <option value="1m">1 Minute</option>\n                            <option value="5m">5 Minutes</option>\n                            <option value="10m">10 Minutes</option>\n                            <option value="30m">30 Minutes</option>\n                            <option value="1h">1 Hour</option>\n                            <option value="2h">2 Hours</option>\n                            <option value="3h">3 Hours</option>\n                            <option value="6h">6 Hours</option>\n                            <option value="12h">12 Hours</option>\n                            <option value="24h">24 Hours</option>\n                        </select>\n                    </div>\n                    \n                    <div id="restart-countdown" class="text-xs mb-6 font-mono opacity-70 stats-text"></div>\n\n                    <button onclick="saveConfig()" class="w-full theme-gradient theme-gradient-hover text-white font-bold py-3 rounded-xl transition">SAVE CHANGES</button>\n                </div>\n            </div>\n        </div>\n    </div>\n\n    <!-- Create File Modal -->\n    <div id="createFileModal" class="hidden fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-lg rounded-2xl p-6 modal-enter">\n            <h3 class="text-white font-bold text-lg mb-4">Create New File</h3>\n            <input type="text" id="new-filename" placeholder="filename.py" class="w-full bg-black border p-3 rounded-lg mb-4" style="border-color: var(--primary); color: var(--text);">\n            <textarea id="new-file-content" rows="8" placeholder="File content..." class="w-full bg-black border p-3 rounded-lg mb-4 font-mono text-sm" style="border-color: var(--primary); color: var(--text);"></textarea>\n            <div class="flex gap-3">\n                <button onclick="createNewFile()" class="flex-1 py-2 rounded-lg transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                    CREATE\n                </button>\n                <button onclick="closeCreateFileModal()" class="flex-1 py-2 rounded-lg transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                    CANCEL\n                </button>\n            </div>\n        </div>\n    </div>\n\n    <!-- Edit File Modal -->\n    <div id="editModal" class="hidden fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-3xl h-[80vh] rounded-2xl flex flex-col modal-enter">\n            <div class="p-4 border-b flex justify-between items-center" style="border-color: var(--primary);">\n                <h3 class="text-white font-bold text-lg" id="edit-title">Edit File</h3>\n                <button onclick="closeEditModal()" class="opacity-50 hover:opacity-100"><i class="fas fa-times text-xl"></i></button>\n            </div>\n            <textarea id="edit-content" class="flex-1 bg-black p-4 text-[13px] font-mono border-0 outline-none resize-none custom-scroll log-text" style="color: var(--primary);"></textarea>\n            <div class="p-4 border-t flex justify-end gap-3" style="border-color: var(--primary);">\n                <button onclick="closeEditModal()" class="px-6 py-2 rounded-lg transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">Cancel</button>\n                <button onclick="saveEditedFile()" class="px-6 py-2 theme-gradient theme-gradient-hover text-white rounded-lg transition">Save</button>\n            </div>\n        </div>\n    </div>\n\n    <script>\n        // --- Variables ---\n        let currentServer = null;\n        let logInterval = null;\n        let countdownInterval = null;\n        let currentPath = \'\';\n        let currentEditFile = { name: \'\', path: \'\' };\n\n        // --- Sidebar ---\n        function toggleSidebar() {\n            document.getElementById(\'sidebar\').classList.toggle(\'open\');\n            document.getElementById(\'sidebarOverlay\').classList.toggle(\'open\');\n        }\n\n        function switchMainView(view) {\n            document.querySelectorAll(\'.main-view\').forEach(v => v.classList.remove(\'active\'));\n            document.getElementById(view + \'-view\').classList.add(\'active\');\n            \n            document.querySelectorAll(\'.menu-item\').forEach(i => i.classList.remove(\'active\'));\n            if (event && event.currentTarget) {\n                event.currentTarget.classList.add(\'active\');\n            }\n            \n            toggleSidebar();\n        }\n\n        // --- Copy Log ---\n        function copyLog(elementId) {\n            const pre = document.getElementById(elementId);\n            if (pre) {\n                const text = pre.textContent || pre.innerText;\n                navigator.clipboard.writeText(text).catch(() => {});\n            }\n        }\n\n        // --- Server Actions ---\n        function serverAction(action) {\n            if (!currentServer) return;\n            fetch(\'/action/\' + currentServer + \'/\' + action).then(() => {\n                setTimeout(() => location.reload(), 500);\n            });\n        }\n\n        function sendCommand() {\n            const input = document.getElementById(\'console-input\');\n            const cmd = input.value;\n            if (!cmd || !currentServer) return;\n            const fd = new FormData();\n            fd.append(\'command\', cmd);\n            fetch(\'/send_input/\' + currentServer, { method: \'POST\', body: fd })\n                .then(() => {\n                    input.value = \'\';\n                    setTimeout(() => location.reload(), 500);\n                });\n        }\n\n        document.getElementById(\'console-input\')?.addEventListener("keypress", function(e) {\n            if (e.key === "Enter") sendCommand();\n        });\n\n        // --- Logs ---\n        function toggleLog(id) {\n            const box = document.getElementById(\'log-box-\' + id);\n            if (box) box.classList.toggle(\'hidden\');\n            if (!box.classList.contains(\'hidden\')) {\n                forceRefreshLog(id);\n            }\n        }\n\n        function forceRefreshLog(id) {\n            fetch(\'/get_logs/\' + id).then(r => r.json()).then(d => {\n                const el = document.getElementById(\'log-\' + id);\n                if (el && d.logs) {\n                    el.textContent = d.logs;\n                    el.scrollTop = el.scrollHeight;\n                }\n            });\n        }\n\n        setInterval(() => {\n            {% for id in servers %}\n            (function() {\n                const box = document.getElementById(\'log-box-{{ id }}\');\n                if (box && !box.classList.contains(\'hidden\')) {\n                    forceRefreshLog(\'{{ id }}\');\n                }\n            })();\n            {% endfor %}\n        }, 2000);\n\n        // --- Server Settings Modal ---\n        function openSettings(id) {\n            currentServer = id;\n            currentPath = \'\';\n            document.getElementById(\'manage-title\').innerText = id;\n            document.getElementById(\'manage-id\').innerText = "ID: " + id;\n            document.getElementById(\'manageModal\').classList.remove(\'hidden\');\n            document.getElementById(\'manageModal\').classList.add(\'flex\');\n            switchTab(\'console\');\n            startCountdown();\n        }\n\n        function closeSettings() {\n            document.getElementById(\'manageModal\').classList.add(\'hidden\');\n            document.getElementById(\'manageModal\').classList.remove(\'flex\');\n            currentServer = null;\n            if (logInterval) clearInterval(logInterval);\n            if (countdownInterval) clearInterval(countdownInterval);\n        }\n\n        function switchTab(tab) {\n            [\'console\', \'files\', \'packages\', \'config\'].forEach(t => {\n                document.getElementById(\'view-\' + t).classList.add(\'hidden\');\n                document.getElementById(\'tab-\' + t).classList.remove(\'theme-active-border\');\n                document.getElementById(\'tab-\' + t).classList.add(\'opacity-50\');\n            });\n            document.getElementById(\'view-\' + tab).classList.remove(\'hidden\');\n            document.getElementById(\'tab-\' + tab).classList.add(\'theme-active-border\');\n            document.getElementById(\'tab-\' + tab).classList.remove(\'opacity-50\');\n\n            if (tab === \'console\') {\n                refreshLiveLog();\n                if (logInterval) clearInterval(logInterval);\n                logInterval = setInterval(refreshLiveLog, 1500);\n            } else {\n                if (logInterval) clearInterval(logInterval);\n            }\n            if (tab === \'files\') {\n                loadFiles();\n            }\n            if (tab === \'config\') {\n                loadServerConfig();\n            }\n        }\n\n        function refreshLiveLog() {\n            if (!currentServer) return;\n            fetch(\'/get_logs/\' + currentServer).then(r => r.json()).then(d => {\n                const el = document.getElementById(\'live-log\');\n                if (d.logs) {\n                    el.textContent = d.logs;\n                    el.scrollTop = el.scrollHeight;\n                }\n            });\n        }\n\n        function loadServerConfig() {\n            if (!currentServer) return;\n            fetch(\'/files/\' + currentServer + \'?path=\').then(r => r.json()).then(d => {\n                document.getElementById(\'config-cmd\').value = d.cmd || \'\';\n                document.getElementById(\'config-cwd\').value = d.cwd || \'\';\n                document.getElementById(\'config-auto-restart\').checked = d.auto_restart || false;\n                document.getElementById(\'config-restart-interval\').value = d.restart_interval || \'1h\';\n            });\n        }\n\n        function saveConfig() {\n            const cmd = document.getElementById(\'config-cmd\').value;\n            const cwd = document.getElementById(\'config-cwd\').value;\n            const autoRestart = document.getElementById(\'config-auto-restart\').checked;\n            const restartInterval = document.getElementById(\'config-restart-interval\').value;\n            const fd = new FormData();\n            fd.append(\'cmd\', cmd);\n            fd.append(\'cwd\', cwd);\n            fd.append(\'auto_restart\', autoRestart);\n            fd.append(\'restart_interval\', restartInterval);\n            fetch(\'/update_settings/\' + currentServer, { method: \'POST\', body: fd })\n                .then(() => alert(\'Settings Saved!\'));\n        }\n\n        function startCountdown() {\n            if (countdownInterval) clearInterval(countdownInterval);\n            countdownInterval = setInterval(updateCountdown, 1000);\n        }\n\n        function updateCountdown() {\n            if (!currentServer) return;\n            fetch(\'/server_info/\' + currentServer)\n                .then(res => res.json())\n                .then(data => {\n                    const el = document.getElementById(\'restart-countdown\');\n                    if (!data.auto_restart || data.status !== \'running\') {\n                        el.innerText = \'\';\n                        return;\n                    }\n                    const intervalMap = {\n                        \'30s\': 30, \'1m\': 60, \'5m\': 300, \'10m\': 600, \'30m\': 1800,\n                        \'1h\': 3600, \'2h\': 7200, \'3h\': 10800, \'6h\': 21600,\n                        \'12h\': 43200, \'24h\': 86400\n                    };\n                    const dueAt = Number(data.next_restart_at || 0);\n                    const intervalSec = intervalMap[data.restart_interval] || 3600;\n                    const remaining = dueAt > 0\n                        ? Math.max(0, Math.ceil(dueAt - Date.now() / 1000))\n                        : Math.max(0, intervalSec - (Math.floor(Date.now() / 1000) - data.last_start_time));\n                    const hours = Math.floor(remaining / 3600);\n                    const mins = Math.floor((remaining % 3600) / 60);\n                    const secs = remaining % 60;\n                    el.innerText = `Auto restart in: ${String(hours).padStart(2, \'0\')}h ${String(mins).padStart(2, \'0\')}m ${String(secs).padStart(2, \'0\')}s`;\n                })\n                .catch(() => {});\n        }\n\n        // --- File Management ---\n        function loadFiles(subpath = null) {\n            if (!currentServer) return;\n            if (subpath !== null) currentPath = subpath;\n            \n            fetch(`/files/${currentServer}?path=${currentPath}`).then(r => r.json()).then(d => {\n                document.getElementById(\'current-path-display\').innerText = "/" + currentPath;\n                const list = document.getElementById(\'file-list\');\n                list.innerHTML = \'\';\n                \n                if (currentPath) {\n                    const parent = currentPath.split(\'/\').slice(0, -1).join(\'/\');\n                    list.innerHTML += `\n                        <div onclick="loadFiles(\'${parent}\')" class="flex items-center p-3 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-800/50 transition file-item" style="border: 1px solid rgba(255,255,255,0.1);">\n                            <i class="fas fa-level-up-alt mr-3 file-icon"></i> \n                            <span class="text-sm file-name">..</span>\n                        </div>`;\n                }\n                \n                if (d.files && d.files.length === 0) {\n                    list.innerHTML += \'<div class="text-center mt-10 opacity-30">Empty directory</div>\';\n                }\n\n                let totalFolderSize = 0;\n                d.files.forEach(f => {\n                    if (f.type === \'file\') {\n                        totalFolderSize += f.raw_size || 0;\n                    }\n                });\n\n                d.files.forEach(f => {\n                    const clickAction = f.type === \'dir\' ? `onclick="loadFiles(\'${currentPath ? currentPath + \'/\' + f.name : f.name}\')"` : \'\';\n                    \n                    list.innerHTML += `\n                        <div class="flex justify-between items-center p-3 bg-black/30 rounded-lg hover:bg-black/50 transition group file-item" style="border: 1px solid rgba(255,255,255,0.1);">\n                            <div class="${f.type === \'dir\' ? \'cursor-pointer\' : \'\'} flex items-center gap-3 overflow-hidden flex-1" ${clickAction}>\n                                <i class="fas ${f.type === \'dir\' ? \'fa-folder\' : \'fa-file-code\'} file-icon" style="opacity: 0.8;"></i>\n                                <span class="text-sm truncate file-name">${f.name}</span>\n                                <span class="file-size ml-2">${f.size}</span>\n                            </div>\n                            <div class="relative dropdown">\n                                <button class="p-1 rounded-full transition hover:opacity-100 opacity-50">\n                                    <i class="fas fa-ellipsis-v file-icon"></i>\n                                </button>\n                                <div class="dropdown-menu">\n                                    ${f.type === \'file\' ? `\n                                    <button onclick="editFile(\'${f.name}\')"><i class="fas fa-edit"></i>Edit</button>\n                                    <button onclick="useAsStartCommand(\'${f.name}\')"><i class="fas fa-terminal"></i>Use as Command</button>\n                                    <a href="/download/${currentServer}/${f.name}?path=${currentPath}"><i class="fas fa-download"></i>Download</a>\n                                    ` : \'\'}\n                                    <button onclick="deleteFile(\'${f.name}\')" style="color: var(--danger);"><i class="fas fa-trash"></i>Delete</button>\n                                </div>\n                            </div>\n                        </div>\n                    `;\n                });\n\n                if (currentPath && d.files && d.files.length > 0) {\n                    let totalSizeText = \'0 B\';\n                    if (totalFolderSize < 1024) {\n                        totalSizeText = totalFolderSize + \' B\';\n                    } else if (totalFolderSize < 1024 * 1024) {\n                        totalSizeText = (totalFolderSize / 1024).toFixed(1) + \' KB\';\n                    } else {\n                        totalSizeText = (totalFolderSize / (1024 * 1024)).toFixed(1) + \' MB\';\n                    }\n                    \n                    const folderTotal = document.createElement(\'div\');\n                    folderTotal.className = \'total-size\';\n                    folderTotal.innerHTML = `📊 Total Size: ${totalSizeText}`;\n                    list.appendChild(folderTotal);\n                }\n            });\n        }\n\n        function showCreateFileDialog() {\n            document.getElementById(\'createFileModal\').classList.remove(\'hidden\');\n            document.getElementById(\'createFileModal\').classList.add(\'flex\');\n        }\n\n        function closeCreateFileModal() {\n            document.getElementById(\'createFileModal\').classList.add(\'hidden\');\n            document.getElementById(\'createFileModal\').classList.remove(\'flex\');\n            document.getElementById(\'new-filename\').value = \'\';\n            document.getElementById(\'new-file-content\').value = \'\';\n        }\n\n        function createNewFile() {\n            const filename = document.getElementById(\'new-filename\').value;\n            const content = document.getElementById(\'new-file-content\').value;\n            if (!filename || !currentServer) return;\n            const fd = new FormData();\n            fd.append(\'filename\', filename);\n            fd.append(\'path\', currentPath);\n            fd.append(\'content\', content);\n            fetch(\'/create_file/\' + currentServer, { method: \'POST\', body: fd })\n                .then(res => res.json())\n                .then(data => {\n                    if (data.status === \'ok\') {\n                        closeCreateFileModal();\n                        loadFiles();\n                    } else {\n                        alert(\'Error: \' + data.error);\n                    }\n                });\n        }\n\n        function createNewFolder() {\n            const name = prompt("Folder Name:");\n            if (name) {\n                const fd = new FormData();\n                fd.append(\'name\', name);\n                fd.append(\'path\', currentPath);\n                fetch(\'/create_folder/\' + currentServer, { method: \'POST\', body: fd })\n                    .then(() => loadFiles());\n            }\n        }\n\n        function uploadFile(input) {\n            if (!input.files[0] || !currentServer) return;\n            const fd = new FormData();\n            fd.append(\'file\', input.files[0]);\n            fd.append(\'path\', currentPath);\n            const btn = input.parentElement;\n            btn.innerHTML = \'<i class="fas fa-spinner fa-spin"></i>\';\n            fetch(\'/upload/\' + currentServer, { method: \'POST\', body: fd })\n                .then(() => {\n                    loadFiles();\n                    btn.innerHTML = \'<i class="fas fa-upload mr-1"></i> Upload <input type="file" id="upload-input" class="hidden" onchange="uploadFile(this)">\';\n                });\n        }\n\n        function deleteFile(name) {\n            if (!confirm(\'Delete \' + name + \'?\')) return;\n            fetch(`/delete_file/${currentServer}/${name}?path=${currentPath}`)\n                .then(() => loadFiles());\n        }\n\n        function editFile(filename) {\n            currentEditFile = { name: filename, path: currentPath };\n            fetch(`/file_content/${currentServer}?filename=${filename}&path=${currentPath}`)\n                .then(r => r.json())\n                .then(data => {\n                    if (data.content !== undefined) {\n                        document.getElementById(\'edit-title\').innerText = \'Editing: \' + filename;\n                        document.getElementById(\'edit-content\').value = data.content;\n                        document.getElementById(\'editModal\').classList.remove(\'hidden\');\n                        document.getElementById(\'editModal\').classList.add(\'flex\');\n                    } else {\n                        alert(\'Error loading file\');\n                    }\n                });\n        }\n\n        function closeEditModal() {\n            document.getElementById(\'editModal\').classList.add(\'hidden\');\n            document.getElementById(\'editModal\').classList.remove(\'flex\');\n        }\n\n        function saveEditedFile() {\n            const content = document.getElementById(\'edit-content\').value;\n            const fd = new FormData();\n            fd.append(\'filename\', currentEditFile.name);\n            fd.append(\'path\', currentEditFile.path);\n            fd.append(\'content\', content);\n            fetch(\'/save_file/\' + currentServer, { method: \'POST\', body: fd })\n                .then(res => res.json())\n                .then(data => {\n                    if (data.status === \'ok\') {\n                        closeEditModal();\n                        loadFiles();\n                    } else {\n                        alert(\'Save failed: \' + data.error);\n                    }\n                });\n        }\n\n        function useAsStartCommand(filename) {\n            let cmd = \'\';\n            if (filename.endsWith(\'.py\')) cmd = \'python \' + filename;\n            else if (filename.endsWith(\'.js\')) cmd = \'node \' + filename;\n            else if (filename.endsWith(\'.sh\')) cmd = \'bash \' + filename;\n            else cmd = \'./\' + filename;\n            document.getElementById(\'config-cmd\').value = cmd;\n            document.getElementById(\'config-cwd\').value = currentPath;\n            switchTab(\'config\');\n        }\n\n        // --- Package Management ---\n        function packageAction(action) {\n            const type = document.getElementById(\'pkg-type\').value;\n            const name = document.getElementById(\'pkg-name\').value;\n            if (!name) {\n                alert("Enter package name!");\n                return;\n            }\n            const fd = new FormData();\n            fd.append(\'type\', type);\n            fd.append(\'name\', name);\n            const endpoint = action === \'install\' ? \'/install_pkg/\' : \'/uninstall_pkg/\';\n            fetch(endpoint + currentServer, { method: \'POST\', body: fd })\n                .then(() => {\n                    document.getElementById(\'pkg-name\').value = \'\';\n                    switchTab(\'console\');\n                });\n        }\n\n        // --- Install all packages listed in requirements.txt ---\n        function installRequirements() {\n            if (!currentServer) return;\n            const btn = document.getElementById(\'requirements-install-btn\');\n            const status = document.getElementById(\'requirements-install-status\');\n            btn.disabled = true;\n            btn.innerHTML = \'<i class="fas fa-spinner fa-spin mr-2"></i> CHECKING FILE...\';\n            status.textContent = \'Checking uploaded requirements.txt...\';\n            fetch(\'/install_requirements/\' + encodeURIComponent(currentServer), { method: \'POST\' })\n                .then(async response => ({ response, data: await response.json() }))\n                .then(({response, data}) => {\n                    if (!response.ok || data.status !== \'ok\') {\n                        status.textContent = data.error || \'Installation could not be started.\';\n                        btn.innerHTML = \'<i class="fas fa-cloud-download-alt mr-2"></i> INSTALL REQUIREMENTS.TXT\';\n                        btn.disabled = false;\n                        return;\n                    }\n                    status.textContent = `Started: ${data.count} package(s). See Console logs.`;\n                    btn.innerHTML = \'<i class="fas fa-check mr-2"></i> INSTALLATION STARTED\';\n                    switchTab(\'console\');\n                    if (logInterval) clearInterval(logInterval);\n                    logInterval = setInterval(refreshLiveLog, 1200);\n                    setTimeout(() => {\n                        btn.disabled = false;\n                        btn.innerHTML = \'<i class="fas fa-cloud-download-alt mr-2"></i> INSTALL REQUIREMENTS.TXT\';\n                    }, 2500);\n                })\n                .catch(error => {\n                    status.textContent = \'Error: \' + error.message;\n                    btn.disabled = false;\n                    btn.innerHTML = \'<i class="fas fa-cloud-download-alt mr-2"></i> INSTALL REQUIREMENTS.TXT\';\n                });\n        }\n        // --- Stats ---\n        function updateStats() {\n    fetch(\'/system_stats\')\n        .then(res => res.json())\n        .then(data => {\n            if (data && data.cpu !== undefined && data.ram !== undefined) {\n                document.getElementById(\'cpu-usage\').innerText = data.cpu + \'%\';\n                document.getElementById(\'ram-usage\').innerText = data.ram + \'%\';\n            }\n        })\n        .catch(() => {\n            // Error হলে কিছু করবেন না, পুরনো ভ্যালু দেখাবে\n            console.log(\'Stats fetch failed\');\n        });\n}\n        updateStats();\n        setInterval(updateStats, 60000);\n    </script>\n</body>\n</html>'

TEMPLATE_ADMIN = '<!-- templates/admin.html -->\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Admin Panel - {{ config.site_title }}</title>\n    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">\n    <style>\n        :root {\n            --primary: {{ colors.primary }};\n            --secondary: {{ colors.secondary }};\n            --accent: {{ colors.accent }};\n            --bg: {{ colors.background }};\n            --card-bg: {{ colors.card_bg }};\n            --text: #ffffff;\n            --danger: {{ colors.danger }};\n            --header-text: #ffffff;\n            --stats-text: #ffffff;\n        }\n        body { \n            background-color: var(--bg); \n            color: var(--text); \n            padding-bottom: 80px;\n            min-height: 100vh;\n        }\n        .theme-gradient { \n            background: linear-gradient(to right, var(--primary), var(--secondary), var(--accent)); \n        }\n        .card-bg { \n            background: var(--card-bg); \n            border: 1px solid rgba(255,255,255,0.1);\n            box-shadow: 0 0 15px rgba(0,0,0,0.3);\n        }\n        .stats-number {\n            color: var(--stats-text);\n            font-weight: bold;\n        }\n        .stats-text {\n            color: var(--stats-text);\n        }\n        .header-text {\n            color: var(--header-text);\n        }\n        .menu-item {\n            padding: 12px 20px;\n            border-bottom: 1px solid rgba(255,255,255,0.05);\n            cursor: pointer;\n            transition: all 0.2s;\n            color: var(--text);\n            display: flex;\n            align-items: center;\n            gap: 15px;\n            font-size: 14px;\n            border-left: 3px solid transparent;\n        }\n        .menu-item:hover {\n            background: rgba(0,0,0,0.2);\n            border-left-color: var(--primary);\n        }\n        .menu-item.active {\n            background: rgba(0,0,0,0.3);\n            border-left-color: var(--primary);\n        }\n        .main-view {\n            display: none;\n        }\n        .main-view.active {\n            display: block;\n        }\n        .server-card {\n            animation: fadeIn 0.5s;\n        }\n        @keyframes fadeIn {\n            from { opacity: 0; transform: translateY(10px); }\n            to { opacity: 1; transform: translateY(0); }\n        }\n        .custom-scroll::-webkit-scrollbar { width: 5px; }\n        .custom-scroll::-webkit-scrollbar-track { background: var(--bg); }\n        .custom-scroll::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }\n        .log-text { font-size: 11px; user-select: text; }\n        \n        .color-dot {\n            width: 30px;\n            height: 30px;\n            border-radius: 50%;\n            cursor: pointer;\n            border: 2px solid transparent;\n            transition: all 0.2s;\n            display: inline-block;\n        }\n        .color-dot:hover {\n            transform: scale(1.2);\n            border-color: white;\n            box-shadow: 0 0 15px currentColor;\n        }\n        \n        .color-grid {\n            display: grid;\n            grid-template-columns: repeat(5, 1fr);\n            gap: 10px;\n            margin-top: 10px;\n        }\n        .color-item {\n            text-align: center;\n            padding: 8px;\n            border-radius: 8px;\n            background: rgba(0,0,0,0.3);\n            border: 1px solid rgba(255,255,255,0.1);\n            transition: all 0.2s;\n            cursor: pointer;\n        }\n        .color-item:hover {\n            transform: scale(1.05);\n            border-color: var(--primary);\n        }\n        .color-item .dot {\n            width: 30px;\n            height: 30px;\n            border-radius: 50%;\n            margin: 0 auto 5px;\n            border: 2px solid rgba(255,255,255,0.2);\n        }\n        .color-item .name {\n            font-size: 9px;\n            opacity: 0.7;\n        }\n        \n        .file-item {\n            background: rgba(0,0,0,0.3);\n            border: 1px solid rgba(255,255,255,0.1);\n            transition: all 0.2s;\n            margin-bottom: 2px;\n            color: #ffffff;\n        }\n        .file-item:hover {\n            background: rgba(0,0,0,0.5);\n            border-color: var(--primary);\n        }\n        .file-size {\n            font-size: 12px;\n            color: #ffffff;\n            opacity: 0.8;\n        }\n        .dropdown-menu { \n            display: none; \n            position: absolute; \n            right: 0; \n            top: 100%; \n            background: var(--card-bg); \n            border: 1px solid rgba(255,255,255,0.1);\n            border-radius: 8px; \n            z-index: 10; \n            min-width: 200px;\n            box-shadow: 0 5px 20px rgba(0,0,0,0.5);\n        }\n        .dropdown:hover .dropdown-menu { display: block; }\n        .dropdown-menu button, .dropdown-menu a {\n            width: 100%;\n            text-align: left;\n            padding: 10px 15px;\n            color: var(--text);\n            transition: all 0.2s;\n            font-size: 13px;\n            border: none;\n            background: none;\n            display: flex;\n            align-items: center;\n            gap: 10px;\n        }\n        .dropdown-menu button:hover, .dropdown-menu a:hover {\n            background: rgba(0,0,0,0.3);\n            color: var(--primary);\n        }\n        .sidebar {\n            position: fixed;\n            left: -280px;\n            top: 0;\n            bottom: 0;\n            width: 280px;\n            background: var(--card-bg);\n            border-right: 2px solid var(--primary);\n            z-index: 1002;\n            transition: left 0.3s ease;\n            box-shadow: 5px 0 30px rgba(0,0,0,0.5);\n            overflow-y: auto;\n        }\n        .sidebar.open { left: 0; }\n        .sidebar-overlay {\n            position: fixed;\n            inset: 0;\n            background: rgba(0,0,0,0.8);\n            z-index: 999;\n            display: none;\n        }\n        .sidebar-overlay.open { display: block; }\n        .modal-enter { animation: slideUp 0.3s ease-out; }\n        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }\n        .theme-active-border { \n            border-bottom: 2px solid var(--primary); \n            color: var(--primary); \n        }\n        \n        .toast {\n            position: fixed;\n            top: 20px;\n            right: 20px;\n            z-index: 9999;\n            padding: 15px 25px;\n            border-radius: 10px;\n            color: white;\n            font-weight: bold;\n            box-shadow: 0 5px 25px rgba(0,0,0,0.5);\n            animation: slideIn 0.5s ease-out;\n            display: none;\n        }\n        .toast.success { background: #00cc66; border-left: 5px solid #00ff80; }\n        .toast.error { background: #cc0033; border-left: 5px solid #ff0044; }\n        @keyframes slideIn {\n            from { transform: translateX(100px); opacity: 0; }\n            to { transform: translateX(0); opacity: 1; }\n        }\n            \n        /* SHAPPNO UI refresh */\n        .card-bg, .login-container { backdrop-filter: blur(14px); border-radius: 18px; }\n        button, input, select, textarea { transition: all .2s ease; }\n        button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {\n            outline: 2px solid var(--primary); outline-offset: 2px;\n        }\n        input, select, textarea { border-radius: 10px !important; }\n        .card-bg { box-shadow: 0 12px 36px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.04); }\n        .card-bg:hover { border-color: color-mix(in srgb, var(--primary) 45%, transparent); }\n        .theme-gradient { box-shadow: 0 6px 18px color-mix(in srgb, var(--primary) 22%, transparent); }\n        @media (max-width: 640px) {\n            .modal-enter { max-height: 92vh; overflow-y: auto; }\n            button { min-height: 38px; }\n        }\n\n\n        .server-card { border: 1px solid color-mix(in srgb, var(--primary) 28%, transparent); background: linear-gradient(145deg, color-mix(in srgb, var(--card-bg) 96%, var(--primary) 4%), var(--card-bg)); }\n        .server-card .grid a, .server-card .grid button { min-height: 42px; border-radius: 11px; }\n        .server-card .grid a:hover, .server-card .grid button:hover { transform: translateY(-2px); filter: brightness(1.18); }\n        .server-card span { backdrop-filter: blur(8px); }\n    </style>\n</head>\n<body>\n    <!-- Toast -->\n    <div id="toast" class="toast"></div>\n\n    <!-- Sidebar -->\n    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>\n    <div class="sidebar" id="sidebar">\n        <div class="p-6 text-center border-b" style="border-color: var(--primary);">\n            <img src="{{ config.icon_url }}" alt="icon" class="w-12 h-12 mx-auto mb-2" style="filter: drop-shadow(0 0 10px var(--primary));">\n            <h2 class="text-xl font-bold mt-2 header-text">Admin Panel</h2>\n            <p class="text-xs mt-2 opacity-50">🔐 SECURE ACCESS</p>\n        </div>\n        <div class="menu-item active" onclick="switchView(\'dashboard\', this)">\n            <i class="fas fa-tachometer-alt w-5"></i> Dashboard\n        </div>\n        <div class="menu-item" onclick="switchView(\'servers\', this)">\n            <i class="fas fa-server w-5"></i> Servers\n        </div>\n        <div class="menu-item" onclick="switchView(\'settings\', this)">\n            <i class="fas fa-cog w-5"></i> Settings\n        </div>\n        <div class="menu-item" onclick="location.href=\'/logout\'">\n            <i class="fas fa-sign-out-alt w-5"></i> Logout\n        </div>\n    </div>\n\n    <!-- Header -->\n    <div class="bg-black/90 backdrop-blur-md border-b sticky top-0 z-30 px-4 py-3 shadow-lg" style="border-color: var(--primary); z-index: 1003;">\n        <div class="flex justify-between items-center">\n            <div class="flex items-center gap-3">\n                <button type="button" id="admin-menu-toggle" aria-label="Toggle admin menu" aria-expanded="false" onclick="toggleSidebar()" class="text-2xl hover:opacity-80 transition" style="color: var(--primary);">\n                    <i class="fas fa-bars"></i>\n                </button>\n                <div class="flex items-center gap-2">\n                    <img src="{{ config.icon_url }}" alt="icon" class="w-6 h-6" style="filter: drop-shadow(0 0 5px var(--primary));">\n                    <h1 class="text-lg font-bold tracking-wider header-text">ADMIN PANEL</h1>\n                </div>\n            </div>\n            <div class="text-[10px] font-mono stats-text">\n                CPU: <span id="cpu-usage" class="stats-number">{{ cpu }}%</span> | \n                RAM: <span id="ram-usage" class="stats-number">{{ ram }}%</span>\n            </div>\n        </div>\n    </div>\n\n    <!-- Dashboard -->\n    <div id="view-dashboard" class="main-view active px-4 py-6">\n        <h2 class="text-xl font-bold mb-6 header-text">📊 Dashboard</h2>\n        <div class="grid grid-cols-3 gap-4">\n            <div class="card-bg p-6 rounded-xl text-center">\n                <div class="text-3xl stats-number">{{ total_count }}</div>\n                <div class="text-xs opacity-50 stats-text">Total Servers</div>\n            </div>\n            <div class="card-bg p-6 rounded-xl text-center">\n                <div class="text-3xl stats-number" style="color: var(--primary);">{{ running_count }}</div>\n                <div class="text-xs opacity-50 stats-text">Running</div>\n            </div>\n            <div class="card-bg p-6 rounded-xl text-center">\n                <div class="text-3xl stats-number" style="color: var(--danger);">{{ total_count - running_count }}</div>\n                <div class="text-xs opacity-50 stats-text">Stopped</div>\n            </div>\n        </div>\n        <div class="card-bg p-6 rounded-xl mt-4">\n            <div class="flex justify-between items-center text-sm">\n                <span>🛡️ Restart Protection: <span style="color: var(--primary);">ACTIVE</span></span>\n                <span>📝 Max Log Lines: <span style="color: var(--primary);">200</span></span>\n                <span>⏱️ Uptime: <span id="uptime-display" style="color: var(--primary);">--</span></span>\n            </div>\n        </div>\n    </div>\n\n    <!-- Servers -->\n    <div id="view-servers" class="main-view px-4 py-6">\n        <div class="flex justify-between items-center mb-6">\n            <h2 class="text-xl font-bold header-text">🖥️ Servers</h2>\n            <button onclick="document.getElementById(\'createModal\').classList.remove(\'hidden\')" \n                    class="theme-gradient text-white px-4 py-2 rounded-lg text-sm font-bold">+ Create</button>\n        </div>\n        \n        <div class="space-y-4">\n            {% for id, s in servers.items() %}\n            <div class="card-bg rounded-2xl overflow-hidden shadow-lg relative server-card">\n                <div class="absolute left-0 top-0 bottom-0 w-1" style="background: {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }};"></div>\n                <div class="p-5 pl-7">\n                    <div class="flex justify-between items-start mb-4">\n                        <div>\n                            <h3 class="font-bold text-lg text-white">{{ id }}</h3>\n                            <p class="text-[10px] opacity-50 font-mono mt-1">{{ s.cmd }}</p>\n                            <p class="text-[9px] opacity-30 mt-1">Owner: {{ s.owner }}</p>\n                        </div>\n                        <span class="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider" \n                              style="background: rgba(0,0,0,0.3); color: {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }}; border: 1px solid {{ \'var(--primary)\' if s.status == \'running\' else \'var(--danger)\' }};">\n                            {{ \'online\' if s.status == \'running\' else \'stopped\' }}\n                        </span>\n                    </div>\n                    <div class="grid grid-cols-5 gap-2">\n                        {% if s.status == \'running\' %}\n                        <a href="/admin/action/{{ id }}/stop" title="OFF" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-stop"></i>\n                        </a>\n                        {% else %}\n                        <a href="/admin/action/{{ id }}/start" title="ON" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-play"></i>\n                        </a>\n                        {% endif %}\n                        {% if s.status == \'running\' %}\n                        <a href="/admin/action/{{ id }}/restart" title="Restart" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: yellow; border: 1px solid yellow;">\n                            <i class="fas fa-sync"></i>\n                        </a>\n                        {% else %}\n                        <a href="/admin/action/{{ id }}/delete" onclick="return confirm(\'Delete this server?\')" title="Delete" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-trash"></i>\n                        </a>\n                        {% endif %}\n                        <button onclick="openSettings(\'{{ id }}\')" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: magenta; border: 1px solid magenta;">\n                            <i class="fas fa-cog"></i>\n                        </button>\n                        <button onclick="toggleLog(\'{{ id }}\')" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: cyan; border: 1px solid cyan;">\n                            <i class="fas fa-eye"></i>\n                        </button>\n                        <button onclick="openFileManager(\'{{ id }}\')" class="hover:bg-opacity-20 rounded-lg py-2 flex justify-center transition" style="background: rgba(0,0,0,0.3); color: #ff9933; border: 1px solid #ff9933;">\n                            <i class="fas fa-folder"></i>\n                        </button>\n                    </div>\n                    <div id="log-box-{{ id }}" class="hidden mt-4 pt-3 border-t" style="border-color: var(--primary);">\n                        <div class="flex justify-end mb-1">\n                            <button onclick="copyLog(\'log-{{ id }}\')" class="bg-black/50 hover:bg-black/80 rounded px-2 py-1 text-xs text-white opacity-40 hover:opacity-100 transition" title="Copy all logs">\n                                <i class="fas fa-copy"></i>\n                            </button>\n                        </div>\n                        <pre id="log-{{ id }}" class="bg-black p-3 rounded-lg text-[11px] h-32 overflow-y-auto custom-scroll font-mono leading-tight log-text" style="color: var(--primary);">Loading...</pre>\n                    </div>\n                </div>\n            </div>\n            {% endfor %}\n            \n            {% if total_count == 0 %}\n            <div class="text-center py-10 opacity-50">\n                <i class="fas fa-server text-4xl mb-3" style="color: var(--primary);"></i>\n                <p class="text-xs">No servers deployed</p>\n            </div>\n            {% endif %}\n        </div>\n    </div>\n\n    <!-- Settings - পাসওয়ার্ড চেঞ্জ + ২০ টি রং -->\n    <div id="view-settings" class="main-view px-4 py-6">\n        <h2 class="text-xl font-bold mb-6 header-text">⚙️ Settings</h2>\n        \n        <div class="card-bg p-6 rounded-xl space-y-6">\n            <!-- Site Settings -->\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Site Title</label>\n                <input type="text" id="site-title" value="{{ config.site_title }}" \n                       class="w-full bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n            </div>\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Site Header</label>\n                <input type="text" id="site-header" value="{{ config.site_header }}" \n                       class="w-full bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n            </div>\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Icon URL</label>\n                <input type="text" id="icon-url" value="{{ config.icon_url }}" \n                       class="w-full bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n            </div>\n            \n            <!-- Theme Select - ২০ টি রং -->\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Color Theme</label>\n                <select id="theme-mode" class="w-full bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n                    <option value="matrix" {% if config.theme == \'matrix\' %}selected{% endif %}>🌿 Matrix Green</option>\n                    <option value="night" {% if config.theme == \'night\' %}selected{% endif %}>🌙 Night Blue</option>\n                    <option value="ocean" {% if config.theme == \'ocean\' %}selected{% endif %}>🌊 Ocean Blue</option>\n                    <option value="sunset" {% if config.theme == \'sunset\' %}selected{% endif %}>🌅 Sunset Orange</option>\n                    <option value="blood" {% if config.theme == \'blood\' %}selected{% endif %}>🔴 Blood Red</option>\n                    <option value="neon" {% if config.theme == \'neon\' %}selected{% endif %}>💜 Neon Purple</option>\n                    <option value="cyber" {% if config.theme == \'cyber\' %}selected{% endif %}>💠 Cyber Cyan</option>\n                    <option value="vapor" {% if config.theme == \'vapor\' %}selected{% endif %}>🌸 Vapor Pink</option>\n                    <option value="gold" {% if config.theme == \'gold\' %}selected{% endif %}>👑 Royal Gold</option>\n                    <option value="silver" {% if config.theme == \'silver\' %}selected{% endif %}>⚙️ Silver Grey</option>\n                    <!-- নতুন ১০ টি রং -->\n                    <option value="crimson" {% if config.theme == \'crimson\' %}selected{% endif %}>❤️ Crimson Red</option>\n                    <option value="emerald" {% if config.theme == \'emerald\' %}selected{% endif %}>💚 Emerald Green</option>\n                    <option value="sapphire" {% if config.theme == \'sapphire\' %}selected{% endif %}>💙 Sapphire Blue</option>\n                    <option value="ruby" {% if config.theme == \'ruby\' %}selected{% endif %}>❤️ Ruby Red</option>\n                    <option value="topaz" {% if config.theme == \'topaz\' %}selected{% endif %}>💛 Topaz Yellow</option>\n                    <option value="amethyst" {% if config.theme == \'amethyst\' %}selected{% endif %}>💜 Amethyst Purple</option>\n                    <option value="jade" {% if config.theme == \'jade\' %}selected{% endif %}>💚 Jade Green</option>\n                    <option value="coral" {% if config.theme == \'coral\' %}selected{% endif %}>🧡 Coral Pink</option>\n                    <option value="indigo" {% if config.theme == \'indigo\' %}selected{% endif %}>💜 Indigo Blue</option>\n                    <option value="rose" {% if config.theme == \'rose\' %}selected{% endif %}>🌹 Rose Gold</option>\n                </select>\n            </div>\n            \n            <!-- Font Select -->\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Font Style</label>\n                <select id="font-family" class="w-full bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n                    <option value="default" {% if config.font_family == \'default\' %}selected{% endif %}>📝 Default</option>\n                    <option value="hacker" {% if config.font_family == \'hacker\' %}selected{% endif %}>💻 Hacker</option>\n                    <option value="terminal" {% if config.font_family == \'terminal\' %}selected{% endif %}>🖥️ Terminal</option>\n                    <option value="code" {% if config.font_family == \'code\' %}selected{% endif %}>⌨️ Code</option>\n                    <option value="retro" {% if config.font_family == \'retro\' %}selected{% endif %}>📟 Retro</option>\n                </select>\n            </div>\n            \n            <!-- Color Grid - ২০ টি রং -->\n            <div>\n                <label class="block text-sm mb-2 opacity-70 stats-text">Quick Theme Preview</label>\n                <div class="color-grid">\n                    <div class="color-item" onclick="previewTheme(\'matrix\')">\n                        <div class="dot" style="background:#00ff00;"></div>\n                        <span class="name">Matrix</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'night\')">\n                        <div class="dot" style="background:#4d88ff;"></div>\n                        <span class="name">Night</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'ocean\')">\n                        <div class="dot" style="background:#3399ff;"></div>\n                        <span class="name">Ocean</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'sunset\')">\n                        <div class="dot" style="background:#ff9933;"></div>\n                        <span class="name">Sunset</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'blood\')">\n                        <div class="dot" style="background:#ff4d4d;"></div>\n                        <span class="name">Blood</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'neon\')">\n                        <div class="dot" style="background:#ff66ff;"></div>\n                        <span class="name">Neon</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'cyber\')">\n                        <div class="dot" style="background:#33ffff;"></div>\n                        <span class="name">Cyber</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'vapor\')">\n                        <div class="dot" style="background:#ff99ff;"></div>\n                        <span class="name">Vapor</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'gold\')">\n                        <div class="dot" style="background:#ffcc66;"></div>\n                        <span class="name">Gold</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'silver\')">\n                        <div class="dot" style="background:#b3b3b3;"></div>\n                        <span class="name">Silver</span>\n                    </div>\n                    <!-- নতুন ১০ টি রং -->\n                    <div class="color-item" onclick="previewTheme(\'crimson\')">\n                        <div class="dot" style="background:#dc143c;"></div>\n                        <span class="name">Crimson</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'emerald\')">\n                        <div class="dot" style="background:#50c878;"></div>\n                        <span class="name">Emerald</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'sapphire\')">\n                        <div class="dot" style="background:#0f52ba;"></div>\n                        <span class="name">Sapphire</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'ruby\')">\n                        <div class="dot" style="background:#e0115f;"></div>\n                        <span class="name">Ruby</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'topaz\')">\n                        <div class="dot" style="background:#ffc87c;"></div>\n                        <span class="name">Topaz</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'amethyst\')">\n                        <div class="dot" style="background:#9966cc;"></div>\n                        <span class="name">Amethyst</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'jade\')">\n                        <div class="dot" style="background:#00a86b;"></div>\n                        <span class="name">Jade</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'coral\')">\n                        <div class="dot" style="background:#ff7f50;"></div>\n                        <span class="name">Coral</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'indigo\')">\n                        <div class="dot" style="background:#4b0082;"></div>\n                        <span class="name">Indigo</span>\n                    </div>\n                    <div class="color-item" onclick="previewTheme(\'rose\')">\n                        <div class="dot" style="background:#b76e79;"></div>\n                        <span class="name">Rose</span>\n                    </div>\n                </div>\n            </div>\n            \n            <!-- ====== USER PASSWORD CHANGE ====== -->\n            <div class="border-t pt-6" style="border-color: var(--primary);">\n                <h3 class="text-lg font-bold mb-4 header-text">🔑 Change User Password</h3>\n                <div class="flex gap-3">\n                    <input type="text" id="new-user-password" placeholder="New User Password (min 3 chars)" \n                           class="flex-1 bg-black border p-3 rounded-lg" style="border-color: var(--primary); color: var(--text);">\n                    <button onclick="changeUserPassword()" class="theme-gradient text-white px-6 py-3 rounded-lg font-bold transition hover:opacity-80">\n                        <i class="fas fa-save mr-2"></i> UPDATE\n                    </button>\n                </div>\n                <p class="text-xs opacity-50 mt-2">Current User Password: <span style="color: var(--primary);">{{ config.passwords.user }}</span></p>\n            </div>\n            \n            <!-- Save Button -->\n            <button onclick="saveSettings()" class="w-full theme-gradient text-white font-bold py-3 rounded-xl transition hover:opacity-80">\n                <i class="fas fa-save mr-2"></i> SAVE ALL SETTINGS\n            </button>\n        </div>\n    </div>\n\n    <!-- Create Server Modal -->\n    <div id="createModal" class="hidden fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center">\n        <div class="card-bg w-full sm:w-96 rounded-t-3xl sm:rounded-2xl p-6 modal-enter">\n            <div class="flex justify-between items-center mb-6">\n                <h3 class="text-white font-bold text-lg">Deploy New Server</h3>\n                <button onclick="document.getElementById(\'createModal\').classList.add(\'hidden\')" class="opacity-50 hover:opacity-100"><i class="fas fa-times"></i></button>\n            </div>\n            <form action="/create_server" method="POST" enctype="multipart/form-data" class="space-y-4">\n                <input type="text" name="server_name" placeholder="Name (e.g. MusicBot)" class="w-full bg-black border p-3 rounded-xl text-white focus:outline-none" style="border-color: var(--primary);" required>\n                <input type="text" name="start_command" placeholder="Command (e.g. python3 bot.py)" class="w-full bg-black border p-3 rounded-xl text-white focus:outline-none" style="border-color: var(--primary);" required>\n                <div class="border border-dashed rounded-xl p-4 text-center" style="border-color: var(--primary);">\n                    <input type="file" name="file" class="text-xs">\n                </div>\n                <button type="submit" class="w-full theme-gradient text-white font-bold py-3 rounded-xl transition hover:opacity-80">Create & Start</button>\n            </form>\n        </div>\n    </div>\n\n    <!-- Server Settings Modal -->\n    <div id="manageModal" class="hidden fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-2xl h-[80vh] rounded-2xl flex flex-col modal-enter">\n            <div class="p-4 border-b flex justify-between items-center" style="border-color: var(--primary);">\n                <div>\n                    <h3 class="text-white font-bold text-lg" id="manage-title">Server Manager</h3>\n                    <span id="manage-id" class="text-xs opacity-50">ID: --</span>\n                </div>\n                <button onclick="closeSettings()" class="opacity-50 hover:opacity-100"><i class="fas fa-times text-xl"></i></button>\n            </div>\n            <div class="flex border-b" style="border-color: var(--primary);">\n                <button onclick="switchTab(\'console\')" id="tab-console" class="flex-1 py-3 text-sm font-bold theme-active-border">CONSOLE</button>\n                <button onclick="switchTab(\'config\')" id="tab-config" class="flex-1 py-3 text-sm font-bold opacity-50 hover:opacity-100">CONFIG</button>\n                <button onclick="switchTab(\'packages\')" id="tab-packages" class="flex-1 py-3 text-sm font-bold opacity-50 hover:opacity-100">PACKAGES</button>\n            </div>\n            <div class="flex-1 overflow-hidden relative">\n                <div id="view-console" class="absolute inset-0 flex flex-col p-4">\n                    <div class="flex gap-2 mb-3">\n                        <button onclick="adminServerAction(\'start\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-play mr-1"></i> START\n                        </button>\n                        <button onclick="adminServerAction(\'stop\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-stop mr-1"></i> STOP\n                        </button>\n                        <button onclick="adminServerAction(\'restart\')" class="flex-1 py-2 rounded-lg text-sm font-bold transition" style="background: rgba(0,0,0,0.3); color: yellow; border: 1px solid yellow;">\n                            <i class="fas fa-sync mr-1"></i> RESTART\n                        </button>\n                    </div>\n                    <div class="flex justify-between items-center mb-1">\n                        <span class="text-[10px] opacity-50">📝 Last 200 lines</span>\n                        <button onclick="copyLog(\'live-log\')" class="bg-black/50 hover:bg-black/80 rounded px-2 py-1 text-xs text-white opacity-40 hover:opacity-100 transition">\n                            <i class="fas fa-copy"></i> Copy\n                        </button>\n                    </div>\n                    <pre id="live-log" class="flex-1 bg-black p-4 rounded-xl text-[11px] font-mono overflow-y-auto custom-scroll mb-3 border log-text" style="color: var(--primary); border-color: var(--primary);">Loading...</pre>\n                    <div class="flex gap-2">\n                        <input type="text" id="console-input" placeholder="Type command & press Enter..." class="flex-1 bg-black border rounded-lg px-4 py-2 text-white text-sm focus:outline-none" style="border-color: var(--primary);">\n                        <button onclick="adminSendCommand()" class="px-4 rounded-lg transition" style="background: var(--primary); color: black;">\n                            <i class="fas fa-paper-plane"></i>\n                        </button>\n                    </div>\n                </div>\n                <div id="view-config" class="hidden absolute inset-0 p-6 overflow-y-auto custom-scroll">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Start Command</label>\n                    <input id="config-cmd" class="w-full bg-black border p-3 rounded-xl mb-4 outline-none" style="border-color: var(--primary); color: var(--text);" value="">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Working Directory</label>\n                    <input id="config-cwd" placeholder="Folder name" class="w-full bg-black border p-3 rounded-xl mb-6 outline-none" style="border-color: var(--primary); color: var(--text);" value="">\n                    <hr class="border-opacity-20 mb-6" style="border-color: var(--primary);">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Auto Restart</label>\n                    <div class="flex items-center gap-4 mb-2">\n                        <label class="relative inline-flex items-center cursor-pointer">\n                            <input type="checkbox" id="config-auto-restart" class="sr-only peer">\n                            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[\'\'] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>\n                        </label>\n                        <select id="config-restart-interval" class="bg-black border p-2 rounded-xl text-sm outline-none" style="border-color: var(--primary); color: var(--text);">\n                            <option value="30s">30 Seconds</option>\n                            <option value="1m">1 Minute</option>\n                            <option value="5m">5 Minutes</option>\n                            <option value="10m">10 Minutes</option>\n                            <option value="30m">30 Minutes</option>\n                            <option value="1h">1 Hour</option>\n                            <option value="2h">2 Hours</option>\n                            <option value="3h">3 Hours</option>\n                            <option value="6h">6 Hours</option>\n                            <option value="12h">12 Hours</option>\n                            <option value="24h">24 Hours</option>\n                        </select>\n                    </div>\n                    <div id="restart-countdown" class="text-xs mb-6 font-mono opacity-70 stats-text"></div>\n                    <button onclick="adminSaveConfig()" class="w-full theme-gradient text-white font-bold py-3 rounded-xl transition hover:opacity-80">SAVE CHANGES</button>\n                </div>\n                <div id="view-packages" class="hidden absolute inset-0 p-6 overflow-y-auto custom-scroll">\n                    <label class="block text-xs uppercase tracking-widest mb-2 opacity-70 stats-text">Package Name</label>\n                    <div class="flex flex-col sm:flex-row gap-3 mb-4">\n                        <select id="pkg-type" class="w-full sm:w-32 bg-black border p-3 rounded-xl outline-none" style="border-color: var(--primary); color: var(--text);">\n                            <option value="pip">PIP</option>\n                            <option value="npm">NPM</option>\n                            <option value="apt">APT</option>\n                            <option value="pkg">PKG</option>\n                        </select>\n                        <input id="pkg-name" placeholder="e.g. requests" class="flex-1 bg-black border p-3 rounded-xl outline-none" style="border-color: var(--primary); color: var(--text);">\n                    </div>\n                    <div class="flex gap-3 mb-6">\n                        <button onclick="adminPackageAction(\'install\')" class="flex-1 py-3 rounded-xl transition" style="background: rgba(0,0,0,0.3); color: var(--primary); border: 1px solid var(--primary);">\n                            <i class="fas fa-download mr-2"></i> INSTALL\n                        </button>\n                        <button onclick="adminPackageAction(\'uninstall\')" class="flex-1 py-3 rounded-xl transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">\n                            <i class="fas fa-trash-alt mr-2"></i> UNINSTALL\n                        </button>\n                    </div>\n                </div>\n            </div>\n        </div>\n    </div>\n\n    <!-- File Manager Modal -->\n    <div id="fileModal" class="hidden fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-3xl h-[80vh] rounded-2xl flex flex-col modal-enter">\n            <div class="p-4 border-b flex justify-between items-center" style="border-color: var(--primary);">\n                <div>\n                    <h3 class="text-white font-bold text-lg" id="file-title">File Manager</h3>\n                    <span id="file-path" class="text-xs opacity-50">/</span>\n                </div>\n                <button onclick="closeFileManager()" class="opacity-50 hover:opacity-100"><i class="fas fa-times text-xl"></i></button>\n            </div>\n            <div class="flex-1 overflow-y-auto p-4 custom-scroll" id="file-list">\n                <div class="text-center opacity-50">Loading...</div>\n            </div>\n        </div>\n    </div>\n\n    <!-- Edit File Modal -->\n    <div id="editModal" class="hidden fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">\n        <div class="card-bg w-full max-w-3xl h-[80vh] rounded-2xl flex flex-col modal-enter">\n            <div class="p-4 border-b flex justify-between items-center" style="border-color: var(--primary);">\n                <h3 class="text-white font-bold text-lg" id="edit-title">Edit File</h3>\n                <button onclick="closeEditModal()" class="opacity-50 hover:opacity-100"><i class="fas fa-times text-xl"></i></button>\n            </div>\n            <textarea id="edit-content" class="flex-1 bg-black p-4 text-[13px] font-mono border-0 outline-none resize-none custom-scroll log-text" style="color: var(--primary);"></textarea>\n            <div class="p-4 border-t flex justify-end gap-3" style="border-color: var(--primary);">\n                <button onclick="closeEditModal()" class="px-6 py-2 rounded-lg transition" style="background: rgba(0,0,0,0.3); color: var(--danger); border: 1px solid var(--danger);">Cancel</button>\n                <button onclick="saveEditedFile()" class="px-6 py-2 theme-gradient text-white rounded-lg transition hover:opacity-80">Save</button>\n            </div>\n        </div>\n    </div>\n\n    <script>\n        // --- Variables ---\n        let currentServer = null;\n        let currentPath = \'\';\n        let logInterval = null;\n        let countdownInterval = null;\n        let fileServer = null;\n        let filePath = \'\';\n        let currentEditFile = { name: \'\', path: \'\', server: \'\' };\n\n        // --- Toast ---\n        function showToast(message, type = \'success\') {\n            const toast = document.getElementById(\'toast\');\n            toast.textContent = message;\n            toast.className = \'toast \' + type;\n            toast.style.display = \'block\';\n            setTimeout(() => { toast.style.display = \'none\'; }, 3000);\n        }\n\n        // --- Sidebar ---\n        function toggleSidebar(forceOpen) {\n            const sidebar = document.getElementById(\'sidebar\');\n            const overlay = document.getElementById(\'sidebarOverlay\');\n            const button = document.getElementById(\'admin-menu-toggle\');\n            const shouldOpen = typeof forceOpen === \'boolean\'\n                ? forceOpen\n                : !sidebar.classList.contains(\'open\');\n            sidebar.classList.toggle(\'open\', shouldOpen);\n            overlay.classList.toggle(\'open\', shouldOpen);\n            if (button) button.setAttribute(\'aria-expanded\', String(shouldOpen));\n            document.body.style.overflow = shouldOpen ? \'hidden\' : \'\';\n        }\n\n        function switchView(view, menuItem) {\n            const target = document.getElementById(\'view-\' + view);\n            if (!target) return;\n            document.querySelectorAll(\'.main-view\').forEach(v => v.classList.remove(\'active\'));\n            target.classList.add(\'active\');\n            document.querySelectorAll(\'.menu-item\').forEach(i => i.classList.remove(\'active\'));\n            if (menuItem) menuItem.classList.add(\'active\');\n            toggleSidebar(false);\n        }\n\n        // --- Copy Log ---\n        function copyLog(elementId) {\n            const pre = document.getElementById(elementId);\n            if (pre) {\n                const text = pre.textContent || pre.innerText;\n                navigator.clipboard.writeText(text).catch(() => {});\n                showToast(\'📋 Logs copied!\', \'success\');\n            }\n        }\n\n        // ===== PREVIEW THEME - ২০ টি রং (সবগুলো যোগ করা হয়েছে) =====\n        function previewTheme(theme) {\n            document.getElementById(\'theme-mode\').value = theme;\n            const colors = {\n                matrix: { primary: \'#00ff00\', secondary: \'#00cc00\', accent: \'#00ff80\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff0000\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                night: { primary: \'#4d88ff\', secondary: \'#3366cc\', accent: \'#aa88ff\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                ocean: { primary: \'#3399ff\', secondary: \'#0066cc\', accent: \'#ff99cc\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                sunset: { primary: \'#ff9933\', secondary: \'#cc6600\', accent: \'#ff66b3\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                blood: { primary: \'#ff4d4d\', secondary: \'#cc0000\', accent: \'#ff80bf\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff0000\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                neon: { primary: \'#ff66ff\', secondary: \'#cc33cc\', accent: \'#ffff80\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                cyber: { primary: \'#33ffff\', secondary: \'#00cccc\', accent: \'#ff80ff\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                vapor: { primary: \'#ff99ff\', secondary: \'#cc66cc\', accent: \'#80ffff\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                gold: { primary: \'#ffcc66\', secondary: \'#cc9933\', accent: \'#ffb380\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                silver: { primary: \'#b3b3b3\', secondary: \'#808080\', accent: \'#cccccc\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                // ===== নতুন ১০ টি রং যোগ করা হয়েছে =====\n                crimson: { primary: \'#dc143c\', secondary: \'#8b0000\', accent: \'#ff6b6b\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff0000\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                emerald: { primary: \'#50c878\', secondary: \'#2e8b57\', accent: \'#98fb98\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                sapphire: { primary: \'#0f52ba\', secondary: \'#003366\', accent: \'#6699ff\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                ruby: { primary: \'#e0115f\', secondary: \'#9b111e\', accent: \'#ff69b4\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff0000\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                topaz: { primary: \'#ffc87c\', secondary: \'#e8a317\', accent: \'#ffdb58\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                amethyst: { primary: \'#9966cc\', secondary: \'#6a0dad\', accent: \'#d8b4fe\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                jade: { primary: \'#00a86b\', secondary: \'#006a4e\', accent: \'#7ddfb3\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                coral: { primary: \'#ff7f50\', secondary: \'#cd5c5c\', accent: \'#ffa07a\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                indigo: { primary: \'#4b0082\', secondary: \'#2c0066\', accent: \'#8b5cf6\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' },\n                rose: { primary: \'#b76e79\', secondary: \'#8a5a64\', accent: \'#e8a2b0\', background: \'#000000\', card_bg: \'#0a0a0a\', text: \'#ffffff\', danger: \'#ff4d4d\', header_text: \'#ffffff\', stats_text: \'#ffffff\' }\n            };\n            if (colors[theme]) {\n                const c = colors[theme];\n                document.documentElement.style.setProperty(\'--primary\', c.primary);\n                document.documentElement.style.setProperty(\'--secondary\', c.secondary);\n                document.documentElement.style.setProperty(\'--accent\', c.accent);\n                document.documentElement.style.setProperty(\'--bg\', c.background);\n                document.documentElement.style.setProperty(\'--card-bg\', c.card_bg);\n                document.documentElement.style.setProperty(\'--text\', c.text);\n                document.documentElement.style.setProperty(\'--danger\', c.danger);\n                document.documentElement.style.setProperty(\'--header-text\', c.header_text);\n                document.documentElement.style.setProperty(\'--stats-text\', c.stats_text);\n            }\n        }\n\n        function saveSettings() {\n            const fd = new FormData();\n            fd.append(\'site_title\', document.getElementById(\'site-title\').value);\n            fd.append(\'site_header\', document.getElementById(\'site-header\').value);\n            fd.append(\'icon_url\', document.getElementById(\'icon-url\').value);\n            fd.append(\'theme\', document.getElementById(\'theme-mode\').value);\n            fd.append(\'font_family\', document.getElementById(\'font-family\').value);\n            \n            fetch(\'/admin/update_config\', { method: \'POST\', body: fd })\n                .then(res => res.json())\n                .then(data => {\n                    if (data.status === \'ok\') {\n                        showToast(\'✅ Settings saved! Refreshing...\', \'success\');\n                        setTimeout(() => location.reload(), 1000);\n                    } else {\n                        showToast(\'❌ Error: \' + (data.error || \'Unknown error\'), \'error\');\n                    }\n                });\n        }\n\n        // ===== CHANGE USER PASSWORD =====\n        function changeUserPassword() {\n            const newPass = document.getElementById(\'new-user-password\').value;\n            if (!newPass || newPass.length < 3) {\n                showToast(\'Password must be at least 3 characters!\', \'error\');\n                return;\n            }\n            if (newPass.length > 20) {\n                showToast(\'Password too long (max 20 chars)!\', \'error\');\n                return;\n            }\n            const fd = new FormData();\n            fd.append(\'new_password\', newPass);\n            fetch(\'/admin/change_password\', { method: \'POST\', body: fd })\n                .then(res => res.json())\n                .then(data => {\n                    if (data.status === \'ok\') {\n                        showToast(\'✅ User password updated successfully!\', \'success\');\n                        document.getElementById(\'new-user-password\').value = \'\';\n                        setTimeout(() => location.reload(), 1000);\n                    } else {\n                        showToast(\'❌ Error: \' + data.error, \'error\');\n                    }\n                })\n                .catch(() => showToast(\'❌ Network error\', \'error\'));\n        }\n\n        // --- Logs ---\n        function toggleLog(id) {\n            const box = document.getElementById(\'log-box-\' + id);\n            if (box) box.classList.toggle(\'hidden\');\n            if (!box.classList.contains(\'hidden\')) {\n                refreshLog(id);\n            }\n        }\n\n        function refreshLog(id) {\n            fetch(\'/admin/get_logs/\' + id).then(r => r.json()).then(d => {\n                const el = document.getElementById(\'log-\' + id);\n                if (el && d.logs) {\n                    el.textContent = d.logs;\n                    el.scrollTop = el.scrollHeight;\n                }\n            });\n        }\n\n        setInterval(() => {\n            {% for id in servers %}\n            (function() {\n                const box = document.getElementById(\'log-box-{{ id }}\');\n                if (box && !box.classList.contains(\'hidden\')) {\n                    refreshLog(\'{{ id }}\');\n                }\n            })();\n            {% endfor %}\n        }, 2000);\n\n        // --- Server Settings Modal ---\n        function openSettings(id) {\n            currentServer = id;\n            document.getElementById(\'manage-title\').innerText = id;\n            document.getElementById(\'manage-id\').innerText = "ID: " + id;\n            document.getElementById(\'manageModal\').classList.remove(\'hidden\');\n            document.getElementById(\'manageModal\').classList.add(\'flex\');\n            switchTab(\'console\');\n            startCountdown();\n        }\n\n        function closeSettings() {\n            document.getElementById(\'manageModal\').classList.add(\'hidden\');\n            document.getElementById(\'manageModal\').classList.remove(\'flex\');\n            currentServer = null;\n            if (logInterval) clearInterval(logInterval);\n            if (countdownInterval) clearInterval(countdownInterval);\n        }\n\n        function switchTab(tab) {\n            [\'console\', \'config\', \'packages\'].forEach(t => {\n                document.getElementById(\'view-\' + t).classList.add(\'hidden\');\n                document.getElementById(\'tab-\' + t).classList.remove(\'theme-active-border\');\n                document.getElementById(\'tab-\' + t).classList.add(\'opacity-50\');\n            });\n            document.getElementById(\'view-\' + tab).classList.remove(\'hidden\');\n            document.getElementById(\'tab-\' + tab).classList.add(\'theme-active-border\');\n            document.getElementById(\'tab-\' + tab).classList.remove(\'opacity-50\');\n\n            if (tab === \'console\') {\n                refreshLiveLog();\n                if (logInterval) clearInterval(logInterval);\n                logInterval = setInterval(refreshLiveLog, 1500);\n                loadServerConfig();\n            } else if (tab === \'config\') {\n                loadServerConfig();\n            } else {\n                if (logInterval) clearInterval(logInterval);\n            }\n        }\n\n        function refreshLiveLog() {\n            if (!currentServer) return;\n            fetch(\'/admin/get_logs/\' + currentServer).then(r => r.json()).then(d => {\n                const el = document.getElementById(\'live-log\');\n                if (d.logs) {\n                    el.textContent = d.logs;\n                    el.scrollTop = el.scrollHeight;\n                }\n            });\n        }\n\n        function loadServerConfig() {\n            if (!currentServer) return;\n            fetch(\'/admin/files/\' + currentServer + \'?path=\').then(r => r.json()).then(d => {\n                document.getElementById(\'config-cmd\').value = d.cmd || \'\';\n                document.getElementById(\'config-cwd\').value = d.cwd || \'\';\n                document.getElementById(\'config-auto-restart\').checked = d.auto_restart || false;\n                document.getElementById(\'config-restart-interval\').value = d.restart_interval || \'1h\';\n            });\n        }\n\n        function adminServerAction(action) {\n            if (!currentServer) return;\n            fetch(\'/admin/action/\' + currentServer + \'/\' + action).then(() => {\n                showToast(\'🔄 Action: \' + action + \' triggered\', \'success\');\n                setTimeout(() => location.reload(), 500);\n            });\n        }\n\n        function adminSendCommand() {\n            const input = document.getElementById(\'console-input\');\n            const cmd = input.value;\n            if (!cmd || !currentServer) return;\n            const fd = new FormData();\n            fd.append(\'command\', cmd);\n            fetch(\'/send_input/\' + currentServer, { method: \'POST\', body: fd })\n                .then(() => {\n                    input.value = \'\';\n                    showToast(\'📝 Command sent\', \'success\');\n                    setTimeout(() => location.reload(), 500);\n                });\n        }\n\n        document.getElementById(\'console-input\')?.addEventListener("keypress", function(e) {\n            if (e.key === "Enter") adminSendCommand();\n        });\n\n        function adminPackageAction(action) {\n            const type = document.getElementById(\'pkg-type\').value;\n            const name = document.getElementById(\'pkg-name\').value;\n            if (!name) {\n                showToast(\'❌ Enter package name!\', \'error\');\n                return;\n            }\n            const fd = new FormData();\n            fd.append(\'type\', type);\n            fd.append(\'name\', name);\n            const endpoint = action === \'install\' ? \'/admin/install_pkg/\' : \'/admin/uninstall_pkg/\';\n            fetch(endpoint + currentServer, { method: \'POST\', body: fd })\n                .then(() => {\n                    document.getElementById(\'pkg-name\').value = \'\';\n                    showToast(\'📦 Package \' + action + \' started\', \'success\');\n                    switchTab(\'console\');\n                });\n        }\n\n        function adminSaveConfig() {\n            const cmd = document.getElementById(\'config-cmd\').value;\n            const cwd = document.getElementById(\'config-cwd\').value;\n            const autoRestart = document.getElementById(\'config-auto-restart\').checked;\n            const restartInterval = document.getElementById(\'config-restart-interval\').value;\n            const fd = new FormData();\n            fd.append(\'cmd\', cmd);\n            fd.append(\'cwd\', cwd);\n            fd.append(\'auto_restart\', autoRestart);\n            fd.append(\'restart_interval\', restartInterval);\n            fetch(\'/admin/update_settings/\' + currentServer, { method: \'POST\', body: fd })\n                .then(() => showToast(\'✅ Settings Saved!\', \'success\'));\n        }\n\n        function startCountdown() {\n            if (countdownInterval) clearInterval(countdownInterval);\n            countdownInterval = setInterval(updateCountdown, 1000);\n        }\n\n        function updateCountdown() {\n            if (!currentServer) return;\n            fetch(\'/server_info/\' + currentServer)\n                .then(res => res.json())\n                .then(data => {\n                    const el = document.getElementById(\'restart-countdown\');\n                    if (!data.auto_restart || data.status !== \'running\') {\n                        el.innerText = \'\';\n                        return;\n                    }\n                    const intervalMap = {\n                        \'30s\': 30, \'1m\': 60, \'5m\': 300, \'10m\': 600, \'30m\': 1800,\n                        \'1h\': 3600, \'2h\': 7200, \'3h\': 10800, \'6h\': 21600,\n                        \'12h\': 43200, \'24h\': 86400\n                    };\n                    const dueAt = Number(data.next_restart_at || 0);\n                    const intervalSec = intervalMap[data.restart_interval] || 3600;\n                    const remaining = dueAt > 0\n                        ? Math.max(0, Math.ceil(dueAt - Date.now() / 1000))\n                        : Math.max(0, intervalSec - (Math.floor(Date.now() / 1000) - data.last_start_time));\n                    const hours = Math.floor(remaining / 3600);\n                    const mins = Math.floor((remaining % 3600) / 60);\n                    const secs = remaining % 60;\n                    el.innerText = `🔄 Auto restart in: ${String(hours).padStart(2, \'0\')}h ${String(mins).padStart(2, \'0\')}m ${String(secs).padStart(2, \'0\')}s`;\n                })\n                .catch(() => {});\n        }\n\n        // --- File Manager ---\n        function openFileManager(serverId) {\n            fileServer = serverId;\n            filePath = \'\';\n            document.getElementById(\'file-title\').innerText = \'File Manager - \' + serverId;\n            document.getElementById(\'file-path\').innerText = \'/\';\n            document.getElementById(\'fileModal\').classList.remove(\'hidden\');\n            document.getElementById(\'fileModal\').classList.add(\'flex\');\n            loadAdminFiles();\n        }\n\n        function closeFileManager() {\n            document.getElementById(\'fileModal\').classList.add(\'hidden\');\n            document.getElementById(\'fileModal\').classList.remove(\'flex\');\n            fileServer = null;\n        }\n\n        function loadAdminFiles(subpath = null) {\n            if (subpath !== null) filePath = subpath;\n            if (!fileServer) return;\n            \n            fetch(`/admin/files/${fileServer}?path=${filePath}`).then(r => r.json()).then(d => {\n                const list = document.getElementById(\'file-list\');\n                list.innerHTML = \'\';\n                document.getElementById(\'file-path\').innerText = \'/\' + filePath;\n                \n                if (filePath) {\n                    const parent = filePath.split(\'/\').slice(0, -1).join(\'/\');\n                    list.innerHTML += `\n                        <div onclick="loadAdminFiles(\'${parent}\')" class="flex items-center p-3 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-800/50 transition file-item">\n                            <i class="fas fa-level-up-alt mr-3 file-icon"></i> \n                            <span class="text-sm file-name">..</span>\n                        </div>`;\n                }\n                \n                if (d.files && d.files.length === 0) {\n                    list.innerHTML += \'<div class="text-center mt-10 opacity-30">Empty directory</div>\';\n                }\n                \n                d.files.forEach(f => {\n                    const clickAction = f.type === \'dir\' ? `onclick="loadAdminFiles(\'${filePath ? filePath + \'/\' + f.name : f.name}\')"` : \'\';\n                    list.innerHTML += `\n                        <div class="flex justify-between items-center p-3 bg-black/30 rounded-lg hover:bg-black/50 transition group file-item">\n                            <div class="${f.type === \'dir\' ? \'cursor-pointer\' : \'\'} flex items-center gap-3 overflow-hidden flex-1" ${clickAction}>\n                                <i class="fas ${f.type === \'dir\' ? \'fa-folder\' : \'fa-file-code\'} file-icon" style="opacity: 0.8;"></i>\n                                <span class="text-sm truncate file-name">${f.name}</span>\n                                <span class="file-size ml-2">${f.size}</span>\n                            </div>\n                            <div class="relative dropdown">\n                                <button class="p-1 rounded-full transition hover:opacity-100 opacity-50">\n                                    <i class="fas fa-ellipsis-v file-icon"></i>\n                                </button>\n                                <div class="dropdown-menu">\n                                    ${f.type === \'file\' ? `\n                                    <button onclick="adminEditFile(\'${f.name}\')"><i class="fas fa-edit"></i>Edit</button>\n                                    <a href="/admin/download/${fileServer}/${f.name}?path=${filePath}"><i class="fas fa-download"></i>Download</a>\n                                    ` : \'\'}\n                                    <button onclick="adminDeleteFile(\'${f.name}\')" style="color: var(--danger);"><i class="fas fa-trash"></i>Delete</button>\n                                </div>\n                            </div>\n                        </div>\n                    `;\n                });\n            });\n        }\n\n        function adminEditFile(filename) {\n            currentEditFile = { name: filename, path: filePath, server: fileServer };\n            fetch(`/admin/file_content/${fileServer}?filename=${filename}&path=${filePath}`)\n                .then(r => r.json())\n                .then(data => {\n                    if (data.content !== undefined) {\n                        document.getElementById(\'edit-title\').innerText = \'Editing: \' + filename;\n                        document.getElementById(\'edit-content\').value = data.content;\n                        document.getElementById(\'editModal\').classList.remove(\'hidden\');\n                        document.getElementById(\'editModal\').classList.add(\'flex\');\n                    } else {\n                        showToast(\'❌ Error loading file\', \'error\');\n                    }\n                });\n        }\n\n        function closeEditModal() {\n            document.getElementById(\'editModal\').classList.add(\'hidden\');\n            document.getElementById(\'editModal\').classList.remove(\'flex\');\n        }\n\n        function saveEditedFile() {\n            const content = document.getElementById(\'edit-content\').value;\n            const fd = new FormData();\n            fd.append(\'filename\', currentEditFile.name);\n            fd.append(\'path\', currentEditFile.path);\n            fd.append(\'content\', content);\n            fetch(\'/save_file/\' + currentEditFile.server, { method: \'POST\', body: fd })\n                .then(res => res.json())\n                .then(data => {\n                    if (data.status === \'ok\') {\n                        showToast(\'✅ File saved!\', \'success\');\n                        closeEditModal();\n                        loadAdminFiles();\n                    } else {\n                        showToast(\'❌ Save failed: \' + data.error, \'error\');\n                    }\n                });\n        }\n\n        function adminDeleteFile(filename) {\n            if (!confirm(\'Delete \' + filename + \'?\')) return;\n            fetch(`/admin/delete_file/${fileServer}/${filename}?path=${filePath}`)\n                .then(() => loadAdminFiles());\n        }\n\n        // --- Stats ---\n        function updateStats() {\n            fetch(\'/system_stats\')\n                .then(res => {\n                    if (!res.ok) throw new Error(\'Network error\');\n                    return res.json();\n                })\n                .then(data => {\n                    if (data && data.cpu !== undefined && data.ram !== undefined) {\n                        document.getElementById(\'cpu-usage\').innerText = data.cpu + \'%\';\n                        document.getElementById(\'ram-usage\').innerText = data.ram + \'%\';\n                    }\n                })\n                .catch(() => {\n                    // Error হলে কিছু করবেন না, পুরনো ভ্যালু দেখাবে\n                    console.log(\'Stats fetch failed\');\n                });\n        }\n        updateStats();\\n        setInterval(updateStats, 60000);\n\n        // --- Uptime ---\n        function updateUptime() {\n            fetch(\'/health\')\n                .then(res => res.json())\n                .then(data => {\n                    const uptime = data.uptime || 0;\n                    const hours = Math.floor(uptime / 3600);\n                    const mins = Math.floor((uptime % 3600) / 60);\n                    const el = document.getElementById(\'uptime-display\');\n                    if (el) el.innerText = hours + \'h \' + mins + \'m\';\n                })\n                .catch(() => {});\n        }\n        setInterval(updateUptime, 10000);\n        updateUptime();\n    </script>\n</body>\n</html>'

APP_STARTED_AT = time.time()
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'user_files')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
DB_FILE = 'servers_db.json'
BLOCKED_FILE = 'blocked_users.json'

if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ===== PROCESS / SCHEDULER STATE =====
RESTART_DATA = {"last_restart": time.time()}

def restart_interval_seconds(value):
    """Convert UI interval values to seconds; safe default is one hour."""
    allowed = {
        "30s": 30, "1m": 60, "5m": 300, "10m": 600,
        "30m": 1800, "1h": 3600, "2h": 7200, "3h": 10800,
        "6h": 21600, "12h": 43200, "24h": 86400
    }
    return allowed.get(str(value), 3600)

# ===== LOG MANAGEMENT (শুধু শেষ 50 লাইন) =====
MAX_LOG_LINES = 200

def append_log(server_id, line):
    server = SERVERS.get(server_id)
    if not server:
        return
    logs = server.get('logs', [])
    logs.append(f"[{time.strftime('%H:%M:%S')}] {line}")
    if len(logs) > MAX_LOG_LINES:
        logs = logs[-MAX_LOG_LINES:]
    server['logs'] = logs

def get_recent_logs(server_id):
    server = SERVERS.get(server_id)
    if not server:
        return []
    return server.get('logs', [])[-MAX_LOG_LINES:]

def is_server_running(server):
    """Use the actual subprocess state instead of a stale saved status flag."""
    proc = server.get('process')
    running = proc is not None and proc.poll() is None
    server['status'] = 'running' if running else 'stopped'
    if not running and proc is not None:
        server['process'] = None
    return running

# --- DEFAULT CONFIG ---
DEFAULT_ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='%2300ff00'%3E%3Cpath d='M20 9V7c0-1.1-.9-2-2-2h-4c0-1.1-.9-2-2-2H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-2h-2v2H6V5h4v2h8v2h2z'/%3E%3C/svg%3E"

DEFAULT_CONFIG = {
    "site_title": "SHAPPNO X VPS",
    "site_header": "SHAPPNO VPS",
    "icon_url": DEFAULT_ICON,
    "theme": "matrix",
    "font_family": "default",
    "colors": {
        "matrix": {"name": "Matrix Green", "primary": "#00ff00", "secondary": "#00cc00", "accent": "#00ff80", "background": "#000000", "card_bg": "#0a0a0a", "text": "#00ff00", "danger": "#ff0000", "header_text": "#00ff00", "stats_text": "#00ff00"},
        "night": {"name": "Night Blue", "primary": "#4d88ff", "secondary": "#3366cc", "accent": "#aa88ff", "background": "#000000", "card_bg": "#0a0a0a", "text": "#4d88ff", "danger": "#ff4d4d", "header_text": "#4d88ff", "stats_text": "#4d88ff"},
        "ocean": {"name": "Ocean Blue", "primary": "#3399ff", "secondary": "#0066cc", "accent": "#ff99cc", "background": "#000000", "card_bg": "#0a0a0a", "text": "#3399ff", "danger": "#ff4d4d", "header_text": "#3399ff", "stats_text": "#3399ff"},
        "sunset": {"name": "Sunset Orange", "primary": "#ff9933", "secondary": "#cc6600", "accent": "#ff66b3", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ff9933", "danger": "#ff4d4d", "header_text": "#ff9933", "stats_text": "#ff9933"},
        "blood": {"name": "Blood Red", "primary": "#ff4d4d", "secondary": "#cc0000", "accent": "#ff80bf", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ff4d4d", "danger": "#ff0000", "header_text": "#ff4d4d", "stats_text": "#ff4d4d"},
        "neon": {"name": "Neon Purple", "primary": "#ff66ff", "secondary": "#cc33cc", "accent": "#ffff80", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ff66ff", "danger": "#ff4d4d", "header_text": "#ff66ff", "stats_text": "#ff66ff"},
        "cyber": {"name": "Cyber Cyan", "primary": "#33ffff", "secondary": "#00cccc", "accent": "#ff80ff", "background": "#000000", "card_bg": "#0a0a0a", "text": "#33ffff", "danger": "#ff4d4d", "header_text": "#33ffff", "stats_text": "#33ffff"},
        "vapor": {"name": "Vapor Pink", "primary": "#ff99ff", "secondary": "#cc66cc", "accent": "#80ffff", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ff99ff", "danger": "#ff4d4d", "header_text": "#ff99ff", "stats_text": "#ff99ff"},
        "gold": {"name": "Royal Gold", "primary": "#ffcc66", "secondary": "#cc9933", "accent": "#ffb380", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ffcc66", "danger": "#ff4d4d", "header_text": "#ffcc66", "stats_text": "#ffcc66"},
        "silver": {"name": "Silver Grey", "primary": "#b3b3b3", "secondary": "#808080", "accent": "#cccccc", "background": "#000000", "card_bg": "#0a0a0a", "text": "#b3b3b3", "danger": "#ff4d4d", "header_text": "#b3b3b3", "stats_text": "#b3b3b3"},
        # নতুন 10 টি রং
        "crimson": {"name": "Crimson Red", "primary": "#dc143c", "secondary": "#8b0000", "accent": "#ff6b6b", "background": "#000000", "card_bg": "#0a0a0a", "text": "#dc143c", "danger": "#ff0000", "header_text": "#dc143c", "stats_text": "#dc143c"},
        "emerald": {"name": "Emerald Green", "primary": "#50c878", "secondary": "#2e8b57", "accent": "#98fb98", "background": "#000000", "card_bg": "#0a0a0a", "text": "#50c878", "danger": "#ff4d4d", "header_text": "#50c878", "stats_text": "#50c878"},
        "sapphire": {"name": "Sapphire Blue", "primary": "#0f52ba", "secondary": "#003366", "accent": "#6699ff", "background": "#000000", "card_bg": "#0a0a0a", "text": "#0f52ba", "danger": "#ff4d4d", "header_text": "#0f52ba", "stats_text": "#0f52ba"},
        "ruby": {"name": "Ruby Red", "primary": "#e0115f", "secondary": "#9b111e", "accent": "#ff69b4", "background": "#000000", "card_bg": "#0a0a0a", "text": "#e0115f", "danger": "#ff0000", "header_text": "#e0115f", "stats_text": "#e0115f"},
        "topaz": {"name": "Topaz Yellow", "primary": "#ffc87c", "secondary": "#e8a317", "accent": "#ffdb58", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ffc87c", "danger": "#ff4d4d", "header_text": "#ffc87c", "stats_text": "#ffc87c"},
        "amethyst": {"name": "Amethyst Purple", "primary": "#9966cc", "secondary": "#6a0dad", "accent": "#d8b4fe", "background": "#000000", "card_bg": "#0a0a0a", "text": "#9966cc", "danger": "#ff4d4d", "header_text": "#9966cc", "stats_text": "#9966cc"},
        "jade": {"name": "Jade Green", "primary": "#00a86b", "secondary": "#006a4e", "accent": "#7ddfb3", "background": "#000000", "card_bg": "#0a0a0a", "text": "#00a86b", "danger": "#ff4d4d", "header_text": "#00a86b", "stats_text": "#00a86b"},
        "coral": {"name": "Coral Pink", "primary": "#ff7f50", "secondary": "#cd5c5c", "accent": "#ffa07a", "background": "#000000", "card_bg": "#0a0a0a", "text": "#ff7f50", "danger": "#ff4d4d", "header_text": "#ff7f50", "stats_text": "#ff7f50"},
        "indigo": {"name": "Indigo Blue", "primary": "#4b0082", "secondary": "#2c0066", "accent": "#8b5cf6", "background": "#000000", "card_bg": "#0a0a0a", "text": "#4b0082", "danger": "#ff4d4d", "header_text": "#4b0082", "stats_text": "#4b0082"},
        "rose": {"name": "Rose Gold", "primary": "#b76e79", "secondary": "#8a5a64", "accent": "#e8a2b0", "background": "#000000", "card_bg": "#0a0a0a", "text": "#b76e79", "danger": "#ff4d4d", "header_text": "#b76e79", "stats_text": "#b76e79"}
    },
    "fonts": {
        "default": "'Segoe UI', sans-serif",
        "hacker": "'Courier New', monospace",
        "terminal": "'Consolas', monospace",
        "code": "'Fira Code', monospace",
        "retro": "'VT323', monospace"
    },
    "passwords": {
        "secret": "14444446555",
        "user": "shappno"
    }
}

def load_config():
    """Load the built-in configuration embedded in this app.py file."""
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config):
    """Keep configuration changes in memory without a separate config file."""
    return None


CONFIG = load_config()

def load_blocked_users():
    if os.path.exists(BLOCKED_FILE):
        try:
            with open(BLOCKED_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_blocked_users(blocked):
    try:
        with open(BLOCKED_FILE, 'w') as f:
            json.dump(blocked, f, indent=2)
    except:
        pass

BLOCKED_USERS = load_blocked_users()
SERVERS = {}
SERVER_OPERATION_LOCKS = {}
SERVER_OPERATION_LOCKS_GUARD = threading.Lock()

def server_operation_lock(server_id):
    with SERVER_OPERATION_LOCKS_GUARD:
        if server_id not in SERVER_OPERATION_LOCKS:
            SERVER_OPERATION_LOCKS[server_id] = threading.RLock()
        return SERVER_OPERATION_LOCKS[server_id]

def save_servers():
    try:
        data = {}
        for sid, s in SERVERS.items():
            data[sid] = {
                'cmd': s.get('cmd', ''),
                'cwd': s.get('cwd', ''),
                'path': s.get('path', ''),
                'auto_restart': s.get('auto_restart', False),
                'restart_interval': s.get('restart_interval', '1h'),
                'status': s.get('status', 'stopped'),
                'last_start_time': s.get('last_start_time', 0),
                'next_restart_at': s.get('next_restart_at', 0),
                'manual_stop': s.get('manual_stop', False),
                'owner': s.get('owner', 'user'),
                'logs': s.get('logs', [])[-MAX_LOG_LINES:]
            }
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def load_servers():
    global SERVERS
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                saved = json.load(f)
                for sid, s in saved.items():
                    SERVERS[sid] = {
                        'process': None,
                        'cmd': s.get('cmd', ''),
                        'cwd': s.get('cwd', ''),
                        'auto_restart': s.get('auto_restart', False),
                        'restart_interval': s.get('restart_interval', '1h'),
                        'logs': s.get('logs', ["Restored from previous session..."])[-MAX_LOG_LINES:],
                        'status': 'stopped',
                        'path': s.get('path', ''),
                        'last_start_time': s.get('last_start_time', 0),
                        'next_restart_at': s.get('next_restart_at', 0),
                        'manual_stop': s.get('manual_stop', False),
                        'owner': s.get('owner', 'user')
                    }
        except:
            pass

load_servers()

# --- LOGIN DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('is_secret'):
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def check_blocked(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') in BLOCKED_USERS:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- HELPER FUNCTIONS ---
def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        return cpu, ram
    except Exception as e:
        print(f"Stats error: {e}")
        return 0, 0

def log_monitor(server_id, proc_obj):
    server = SERVERS.get(server_id)
    if not server:
        return
    try:
        for line in iter(proc_obj.stdout.readline, ''):
            if server_id not in SERVERS or SERVERS[server_id].get('process') != proc_obj:
                break
            if line:
                append_log(server_id, line.strip())
    except:
        pass
    finally:
        try:
            proc_obj.stdout.close()
        except:
            pass
    if server_id in SERVERS and SERVERS[server_id].get('process') == proc_obj:
        # A closed output stream alone must not be treated as a stopped process.
        if proc_obj.poll() is not None:
            SERVERS[server_id]['status'] = 'stopped'
            SERVERS[server_id]['process'] = None
            if SERVERS[server_id].get('auto_restart', False) and not SERVERS[server_id].get('manual_stop', False):
                SERVERS[server_id]['next_restart_at'] = time.time()
            save_servers()
        else:
            SERVERS[server_id]['status'] = 'running'

def kill_process_completely(proc):
    try:
        if proc is None:
            return
        import psutil
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except:
                pass
        gone, alive = psutil.wait_procs(children, timeout=3)
        for child in alive:
            try:
                child.kill()
            except:
                pass
        try:
            parent.terminate()
            parent.wait(timeout=3)
        except:
            try:
                parent.kill()
            except:
                pass
    except:
        pass

def _start_server_locked(server_id, server):
    """Start one server. Caller must hold that server's operation lock."""
    if is_server_running(server):
        return True
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    work_dir = os.path.join(server['path'], server.get('cwd', ''))
    if not os.path.exists(work_dir):
        work_dir = server['path']
    try:
        if not server['cmd'] or server['cmd'].strip() == '':
            append_log(server_id, "❌ Error: No start command specified")
            return False
        if not os.path.exists(work_dir):
            append_log(server_id, f"❌ Error: Working directory does not exist: {work_dir}")
            return False
        proc = subprocess.Popen(
            server['cmd'], shell=True, cwd=work_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE, text=True, bufsize=1,
            universal_newlines=True, env=env,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        server['process'] = proc
        server['manual_stop'] = False
        server['status'] = 'running'
        server['last_start_time'] = time.time()
        server['next_restart_at'] = (
            server['last_start_time'] + restart_interval_seconds(server.get('restart_interval', '1h'))
            if server.get('auto_restart', False) else 0
        )
        append_log(server_id, "🚀 Server started successfully!")
        if server.get('auto_restart', False):
            append_log(server_id, f"⏱️ Next auto restart scheduled in {server.get('restart_interval', '1h')}")
        threading.Thread(target=log_monitor, args=(server_id, proc), daemon=True).start()
        save_servers()
        return True
    except Exception as e:
        server['status'] = 'stopped'
        server['process'] = None
        append_log(server_id, f"❌ Failed to start: {str(e)}")
        save_servers()
        return False


def start_server_internal(server_id, server):
    with server_operation_lock(server_id):
        return _start_server_locked(server_id, server)


def stop_server_internal(server_id, server, source='user'):
    """Stop a server and mark the stop as intentional so auto-restart stays idle."""
    with server_operation_lock(server_id):
        if server_id not in SERVERS:
            return False
        server = SERVERS[server_id]
        proc = server.get('process')
        server['process'] = None
        server['status'] = 'stopped'
        server['manual_stop'] = True
        server['next_restart_at'] = 0
        if proc is not None:
            kill_process_completely(proc)
        append_log(server_id, f"⏹️ Stopped by {source}")
        save_servers()
        return True


def restart_server_internal(server_id, server, reason='Manual restart'):
    """Perform the exact stop-then-start operation used by the dashboard Restart button."""
    with server_operation_lock(server_id):
        if server_id not in SERVERS:
            return False
        server = SERVERS[server_id]
        proc = server.get('process')
        append_log(server_id, f"🔄 {reason} triggered; restarting process...")
        # Detach the old process before terminating it so its log thread cannot
        # overwrite the state/timer belonging to the newly started process.
        server['process'] = None
        server['status'] = 'stopped'
        if proc is not None:
            kill_process_completely(proc)
        server['manual_stop'] = False
        save_servers()
        started = _start_server_locked(server_id, server)
        if started:
            append_log(server_id, f"✅ {reason} completed successfully; countdown reset")
        else:
            # Avoid a tight retry loop; scheduler will try again after 30 seconds.
            if server.get('auto_restart', False):
                server['next_restart_at'] = time.time() + 30
            append_log(server_id, f"❌ {reason} failed; retry scheduled when applicable")
        save_servers()
        return started


# ===== RELIABLE PER-SERVER AUTO RESTART =====
def auto_restart_scheduler():
    """Run each enabled server's dashboard-equivalent restart at its due time."""
    while True:
        time.sleep(1)
        now = time.time()
        for server_id in list(SERVERS.keys()):
            lock = server_operation_lock(server_id)
            try:
                with lock:
                    server = SERVERS.get(server_id)
                    if not server or not server.get('auto_restart', False) or server.get('manual_stop', False):
                        continue

                    running = is_server_running(server)
                    if not running:
                        # Recover an unexpectedly exited process, but never override
                        # an explicit dashboard STOP (manual_stop).
                        if server.get('last_start_time', 0):
                            append_log(server_id, "♻️ Auto recovery: process stopped unexpectedly; starting again...")
                            _start_server_locked(server_id, server)
                        continue

                    due = float(server.get('next_restart_at') or 0)
                    if due <= 0:
                        due = float(server.get('last_start_time') or now) + restart_interval_seconds(server.get('restart_interval'))
                        server['next_restart_at'] = due
                        save_servers()
                    if now >= due:
                        # RLock makes this safe while already holding the per-server lock.
                        restart_server_internal(server_id, server, reason='⏰ Auto restart')
            except Exception as exc:
                print(f"[AutoRestart] {server_id}: {exc}")


threading.Thread(target=auto_restart_scheduler, daemon=True, name='auto-restart-scheduler').start()

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            password = request.form.get('password')
            
            if password == CONFIG['passwords']['secret']:
                session['logged_in'] = True
                session['is_secret'] = True
                session['username'] = 'admin'
                return redirect(url_for('admin_panel'))
            
            elif password == CONFIG['passwords']['user']:
                if 'user' in BLOCKED_USERS:
                    return render_template_string(TEMPLATE_LOGIN, error="You have been blocked by admin", config=CONFIG)
                session['logged_in'] = True
                session['is_secret'] = False
                session['username'] = 'user'
                return redirect(url_for('index'))
            
            else:
                return render_template_string(TEMPLATE_LOGIN, error="Invalid password", config=CONFIG)
        
        return render_template_string(TEMPLATE_LOGIN, config=CONFIG)
    except Exception as e:
        return f"Login error: {e}", 500

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    try:
        if request.method == 'POST':
            password = request.form.get('password')
            
            if password == CONFIG['passwords']['secret']:
                session['logged_in'] = True
                session['is_secret'] = True
                session['username'] = 'admin'
                return redirect(url_for('admin_panel'))
            else:
                return render_template_string(TEMPLATE_ADMIN_LOGIN, error="Invalid admin password", config=CONFIG)
        
        return render_template_string(TEMPLATE_ADMIN_LOGIN, config=CONFIG)
    except Exception as e:
        return f"Login error: {e}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- USER DASHBOARD ---
@app.route('/')
@login_required
@check_blocked
def index():
    try:
        cpu, ram = get_system_stats()
        current_colors = CONFIG['colors'].get(CONFIG['theme'], CONFIG['colors']['matrix'])
        serializable_servers = {}
        for sid, s in SERVERS.items():
            if s.get('owner', 'user') == 'user':
                serializable_servers[sid] = {
                    'cmd': s.get('cmd', ''),
                    'cwd': s.get('cwd', ''),
                    'auto_restart': s.get('auto_restart', False),
                    'restart_interval': s.get('restart_interval', '1h'),
                    'status': 'running' if is_server_running(s) else 'stopped',
                    'path': s.get('path', ''),
                    'last_start_time': s.get('last_start_time', 0),
                'next_restart_at': s.get('next_restart_at', 0),
                'manual_stop': s.get('manual_stop', False),
                    'owner': s.get('owner', 'user')
                }
        return render_template_string(TEMPLATE_INDEX, 
                             servers=serializable_servers,
                             cpu=cpu, 
                             ram=ram,
                             total_count=len(serializable_servers),
                             running_count=sum(1 for s in serializable_servers.values() if s['status'] == 'running'),
                             config=CONFIG,
                             colors=current_colors,
                             is_secret=session.get('is_secret', False))
    except Exception as e:
        return f"Error: {e}", 500

# --- ADMIN PANEL ---
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    try:
        cpu, ram = get_system_stats()
        current_colors = CONFIG['colors'].get(CONFIG['theme'], CONFIG['colors']['matrix'])
        serializable_servers = {}
        for sid, s in SERVERS.items():
            if s.get('owner', 'user') == 'admin':
                serializable_servers[sid] = {
                    'cmd': s.get('cmd', ''),
                    'cwd': s.get('cwd', ''),
                    'auto_restart': s.get('auto_restart', False),
                    'restart_interval': s.get('restart_interval', '1h'),
                    'status': 'running' if is_server_running(s) else 'stopped',
                    'path': s.get('path', ''),
                    'last_start_time': s.get('last_start_time', 0),
                'next_restart_at': s.get('next_restart_at', 0),
                'manual_stop': s.get('manual_stop', False),
                    'owner': s.get('owner', 'user')
                }
        return render_template_string(TEMPLATE_ADMIN, 
                             servers=serializable_servers,
                             cpu=cpu, 
                             ram=ram,
                             total_count=len(serializable_servers),
                             running_count=sum(1 for s in serializable_servers.values() if s['status'] == 'running'),
                             config=CONFIG,
                             colors=current_colors,
                             blocked_users=BLOCKED_USERS)
    except Exception as e:
        return f"Error: {e}", 500

# --- CHANGE USER PASSWORD (Admin) ---
@app.route('/admin/change_password', methods=['POST'])
@admin_required
def change_user_password():
    try:
        new_password = request.form.get('new_password')
        if not new_password or len(new_password) < 3:
            return jsonify({'error': 'Password must be at least 3 characters'}), 400
        if len(new_password) > 20:
            return jsonify({'error': 'Password too long (max 20 chars)'}), 400
        
        CONFIG['passwords']['user'] = new_password
        save_config(CONFIG)  # শুধু এটুকুই যথেষ্ট
        return jsonify({'status': 'ok', 'message': 'User password updated successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Admin: User Management ---
@app.route('/admin/block_user/<username>')
@admin_required
def block_user(username):
    if username not in BLOCKED_USERS:
        BLOCKED_USERS.append(username)
        save_blocked_users(BLOCKED_USERS)
    return redirect(url_for('admin_panel'))

@app.route('/admin/unblock_user/<username>')
@admin_required
def unblock_user(username):
    if username in BLOCKED_USERS:
        BLOCKED_USERS.remove(username)
        save_blocked_users(BLOCKED_USERS)
    return redirect(url_for('admin_panel'))

# --- Admin: Server Actions ---
@app.route('/admin/action/<server_id>/<action>')
@admin_required
def admin_server_action(server_id, action):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        server = SERVERS[server_id]
        if action == 'start':
            start_server_internal(server_id, server)
        elif action == 'stop':
            stop_server_internal(server_id, server, source='admin')
        elif action == 'restart':
            restart_server_internal(server_id, server, reason='Manual restart by admin')
        elif action == 'delete':
            if server['process']:
                kill_process_completely(server['process'])
                server['process'] = None
            if os.path.exists(server['path']):
                shutil.rmtree(server['path'], ignore_errors=True)
            del SERVERS[server_id]
            save_servers()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return redirect(url_for('admin_panel'))

# --- Admin: File Management ---
@app.route('/admin/files/<server_id>')
@admin_required
def admin_list_files(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        subpath = request.args.get('path', '')
        if '..' in subpath:
            subpath = ''
        base_path = SERVERS[server_id]['path']
        full_path = os.path.join(base_path, subpath)
        if not os.path.realpath(full_path).startswith(os.path.realpath(base_path)):
            full_path = base_path
            subpath = ''
        if not os.path.exists(full_path):
            full_path = base_path
            subpath = ''
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            is_file = os.path.isfile(item_path)
            size = 0
            if is_file:
                size = os.path.getsize(item_path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            files.append({
                'name': item,
                'size': size_str,
                'raw_size': size,
                'type': 'file' if is_file else 'dir'
            })
        files.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
        return jsonify({
            'files': files,
            'cmd': SERVERS[server_id]['cmd'],
            'cwd': SERVERS[server_id].get('cwd', ''),
            'auto_restart': SERVERS[server_id].get('auto_restart', False),
            'restart_interval': SERVERS[server_id].get('restart_interval', '1h'),
            'current_path': subpath
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/download/<server_id>/<filename>')
@admin_required
def admin_download_file(server_id, filename):
    try:
        if server_id not in SERVERS:
            return "Server not found", 404
        subpath = request.args.get('path', '')
        if '..' in subpath or '..' in filename:
            return "Invalid path", 400
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return "Invalid path", 400
        if not os.path.exists(file_path):
            return "File not found", 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return str(e), 500

@app.route('/admin/delete_file/<server_id>/<filename>')
@admin_required
def admin_delete_file(server_id, filename):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        subpath = request.args.get('path', '')
        if '..' in subpath or '..' in filename:
            return jsonify({'error': 'Invalid path'}), 400
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/file_content/<server_id>')
@admin_required
def admin_file_content(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        filename = request.args.get('filename')
        subpath = request.args.get('path', '')
        if not filename:
            return jsonify({'error': 'No filename'}), 400
        subpath = subpath.replace('..', '')
        filename = filename.replace('..', '')
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/get_logs/<server_id>')
@admin_required
def admin_get_logs(server_id):
    try:
        if server_id in SERVERS:
            return jsonify({'logs': "\n".join(get_recent_logs(server_id))})
        return jsonify({'logs': ''})
    except:
        return jsonify({'logs': ''})

@app.route('/admin/update_settings/<server_id>', methods=['POST'])
@admin_required
def admin_update_settings(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        cmd = request.form.get('cmd', '').strip()
        cwd = request.form.get('cwd', '').strip()
        auto_restart = request.form.get('auto_restart') == 'true'
        restart_interval = request.form.get('restart_interval', '1h')
        SERVERS[server_id]['cmd'] = cmd
        SERVERS[server_id]['cwd'] = cwd
        SERVERS[server_id]['auto_restart'] = auto_restart
        SERVERS[server_id]['restart_interval'] = restart_interval
        SERVERS[server_id]['manual_stop'] = False
        SERVERS[server_id]['next_restart_at'] = (time.time() + restart_interval_seconds(restart_interval)) if auto_restart and is_server_running(SERVERS[server_id]) else 0
        append_log(server_id, "⚙️ Settings updated by admin")
        if auto_restart and SERVERS[server_id]['next_restart_at']:
            append_log(server_id, f"⏱️ Auto restart enabled: every {restart_interval}")
        save_servers()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Admin: Package Management ---
@app.route('/admin/install_pkg/<server_id>', methods=['POST'])
@admin_required
def admin_install_pkg(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        pkg_type = request.form.get('type')
        pkg_name = request.form.get('name')
        if not pkg_name:
            return jsonify({'error': 'Package name required'}), 400
        cmd = ""
        if pkg_type == 'pip':
            cmd = f"pip install {pkg_name}"
        elif pkg_type == 'pkg':
            cmd = f"pkg install -y {pkg_name}"
        elif pkg_type == 'apt':
            cmd = f"apt-get install -y {pkg_name}"
        elif pkg_type == 'npm':
            cmd = f"npm install -g {pkg_name}"
        else:
            return jsonify({'error': 'Invalid package type'}), 400
        threading.Thread(target=lambda: run_install_command(server_id, cmd), daemon=True).start()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/uninstall_pkg/<server_id>', methods=['POST'])
@admin_required
def admin_uninstall_pkg(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        pkg_type = request.form.get('type')
        pkg_name = request.form.get('name')
        if not pkg_name:
            return jsonify({'error': 'Package name required'}), 400
        cmd = ""
        if pkg_type == 'pip':
            cmd = f"pip uninstall -y {pkg_name}"
        elif pkg_type == 'pkg':
            cmd = f"pkg uninstall -y {pkg_name}"
        elif pkg_type == 'apt':
            cmd = f"apt-get remove -y {pkg_name}"
        elif pkg_type == 'npm':
            cmd = f"npm uninstall -g {pkg_name}"
        else:
            return jsonify({'error': 'Invalid package type'}), 400
        threading.Thread(target=lambda: run_install_command(server_id, cmd), daemon=True).start()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_install_command(server_id, command):
    if server_id in SERVERS:
        append_log(server_id, f"📦 {command}")
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                if line:
                    append_log(server_id, line.strip())
            append_log(server_id, "✅ Installation finished.")
        except Exception as e:
            append_log(server_id, f"❌ Error: {str(e)}")

# --- Admin: Theme & Config ---
@app.route('/admin/update_config', methods=['POST'])
@admin_required
def admin_update_config():
    try:
        site_title = request.form.get('site_title')
        site_header = request.form.get('site_header')
        icon_url = request.form.get('icon_url')
        theme = request.form.get('theme')
        font_family = request.form.get('font_family')
        if site_title:
            CONFIG['site_title'] = site_title
        if site_header:
            CONFIG['site_header'] = site_header
        if icon_url:
            CONFIG['icon_url'] = icon_url
        if theme and theme in CONFIG['colors']:
            CONFIG['theme'] = theme
        if font_family and font_family in CONFIG['fonts']:
            CONFIG['font_family'] = font_family
        save_config(CONFIG)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- USER SERVER ACTIONS ---
@app.route('/action/<server_id>/<action>')
@login_required
@check_blocked
def user_server_action(server_id, action):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        server = SERVERS[server_id]
        if action == 'start':
            server['manual_stop'] = False
            start_server_internal(server_id, server)
        elif action == 'stop':
            stop_server_internal(server_id, server, source='user')
        elif action == 'restart':
            restart_server_internal(server_id, server, reason='Manual restart by user')
        elif action == 'delete':
            if server['process']:
                kill_process_completely(server['process'])
                server['process'] = None
            if os.path.exists(server['path']):
                shutil.rmtree(server['path'], ignore_errors=True)
            del SERVERS[server_id]
            save_servers()
        return redirect(url_for('index'))
    except Exception as e:
        return redirect(url_for('index'))

# --- USER FILE MANAGEMENT ---
@app.route('/files/<server_id>')
@login_required
@check_blocked
def user_list_files(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        subpath = request.args.get('path', '')
        if '..' in subpath:
            subpath = ''
        base_path = SERVERS[server_id]['path']
        full_path = os.path.join(base_path, subpath)
        if not os.path.realpath(full_path).startswith(os.path.realpath(base_path)):
            full_path = base_path
            subpath = ''
        if not os.path.exists(full_path):
            full_path = base_path
            subpath = ''
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            is_file = os.path.isfile(item_path)
            size = 0
            if is_file:
                size = os.path.getsize(item_path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            files.append({
                'name': item,
                'size': size_str,
                'raw_size': size,
                'type': 'file' if is_file else 'dir'
            })
        files.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
        return jsonify({
            'files': files,
            'cmd': SERVERS[server_id]['cmd'],
            'cwd': SERVERS[server_id].get('cwd', ''),
            'auto_restart': SERVERS[server_id].get('auto_restart', False),
            'restart_interval': SERVERS[server_id].get('restart_interval', '1h'),
            'current_path': subpath
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<server_id>/<filename>')
@login_required
@check_blocked
def user_download_file(server_id, filename):
    try:
        if server_id not in SERVERS:
            return "Server not found", 404
        subpath = request.args.get('path', '')
        if '..' in subpath or '..' in filename:
            return "Invalid path", 400
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return "Invalid path", 400
        if not os.path.exists(file_path):
            return "File not found", 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return str(e), 500

@app.route('/delete_file/<server_id>/<filename>')
@login_required
@check_blocked
def user_delete_file(server_id, filename):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        subpath = request.args.get('path', '')
        if '..' in subpath or '..' in filename:
            return jsonify({'error': 'Invalid path'}), 400
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/file_content/<server_id>')
@login_required
@check_blocked
def user_file_content(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        filename = request.args.get('filename')
        subpath = request.args.get('path', '')
        if not filename:
            return jsonify({'error': 'No filename'}), 400
        subpath = subpath.replace('..', '')
        filename = filename.replace('..', '')
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_file/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_save_file(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        filename = request.form.get('filename')
        subpath = request.form.get('path', '')
        content = request.form.get('content')
        if not filename or content is None:
            return jsonify({'error': 'Missing data'}), 400
        subpath = subpath.replace('..', '')
        filename = filename.replace('..', '')
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_file/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_create_file(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        filename = request.form.get('filename')
        subpath = request.form.get('path', '')
        content = request.form.get('content', '')
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        subpath = subpath.replace('..', '')
        filename = filename.replace('..', '')
        file_path = os.path.join(SERVERS[server_id]['path'], subpath, filename)
        if not os.path.realpath(file_path).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        if os.path.exists(file_path):
            return jsonify({'error': 'File already exists'}), 400
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_upload_file(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        file = request.files.get('file')
        subpath = request.form.get('path', '')
        if '..' in subpath:
            subpath = ''
        if not file or not file.filename:
            return jsonify({'error': 'No file provided'}), 400
        target_dir = os.path.join(SERVERS[server_id]['path'], subpath)
        if not os.path.realpath(target_dir).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, file.filename)
        file.save(file_path)
        return jsonify({'status': 'ok', 'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_folder/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_create_folder(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        folder_name = request.form.get('name')
        subpath = request.form.get('path', '')
        if '..' in subpath:
            subpath = ''
        if not folder_name:
            return jsonify({'error': 'Folder name required'}), 400
        folder_name = folder_name.replace('..', '')
        target = os.path.join(SERVERS[server_id]['path'], subpath, folder_name)
        if not os.path.realpath(target).startswith(os.path.realpath(SERVERS[server_id]['path'])):
            return jsonify({'error': 'Invalid path'}), 400
        os.makedirs(target, exist_ok=True)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_settings/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_update_settings(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        cmd = request.form.get('cmd', '').strip()
        cwd = request.form.get('cwd', '').strip()
        auto_restart = request.form.get('auto_restart') == 'true'
        restart_interval = request.form.get('restart_interval', '1h')
        SERVERS[server_id]['cmd'] = cmd
        SERVERS[server_id]['cwd'] = cwd
        SERVERS[server_id]['auto_restart'] = auto_restart
        SERVERS[server_id]['restart_interval'] = restart_interval
        SERVERS[server_id]['manual_stop'] = False
        SERVERS[server_id]['next_restart_at'] = (time.time() + restart_interval_seconds(restart_interval)) if auto_restart and is_server_running(SERVERS[server_id]) else 0
        append_log(server_id, "⚙️ Settings updated")
        if auto_restart and SERVERS[server_id]['next_restart_at']:
            append_log(server_id, f"⏱️ Auto restart enabled: every {restart_interval}")
        save_servers()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/install_pkg/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_install_pkg(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        pkg_type = request.form.get('type')
        pkg_name = request.form.get('name')
        if not pkg_name:
            return jsonify({'error': 'Package name required'}), 400
        cmd = ""
        if pkg_type == 'pip':
            cmd = f"pip install {pkg_name}"
        elif pkg_type == 'pkg':
            cmd = f"pkg install -y {pkg_name}"
        elif pkg_type == 'apt':
            cmd = f"apt-get install -y {pkg_name}"
        elif pkg_type == 'npm':
            cmd = f"npm install -g {pkg_name}"
        else:
            return jsonify({'error': 'Invalid package type'}), 400
        threading.Thread(target=lambda: run_install_command(server_id, cmd), daemon=True).start()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/install_requirements/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_install_requirements(server_id):
    """Install each entry from the uploaded project's requirements.txt."""
    try:
        if server_id not in SERVERS:
            return jsonify({'status': 'error', 'error': 'Server not found'}), 404

        server = SERVERS[server_id]
        root = os.path.realpath(server.get('path', ''))
        cwd = os.path.realpath(os.path.join(root, server.get('cwd', '')))
        candidates = []
        for base in (cwd, root):
            try:
                inside_root = os.path.commonpath([root, base]) == root
            except ValueError:
                inside_root = False
            if inside_root and base and base not in candidates and os.path.isdir(base):
                candidates.append(base)

        requirements_path = next(
            (os.path.join(base, 'requirements.txt') for base in candidates
             if os.path.isfile(os.path.join(base, 'requirements.txt'))),
            None
        )
        if not requirements_path:
            append_log(server_id, "❌ requirements.txt file নাই")
            return jsonify({'status': 'error', 'error': 'requirements.txt ফাইল নাই'}), 404

        with open(requirements_path, 'r', encoding='utf-8-sig') as f:
            entries = [
                line.strip() for line in f
                if line.strip() and not line.lstrip().startswith('#')
            ]
        if not entries:
            append_log(server_id, "⚠️ requirements.txt is empty; nothing to install.")
            return jsonify({'status': 'error', 'error': 'requirements.txt ফাইল খালি'}), 400

        def install_requirements():
            append_log(server_id, f"📦 requirements.txt install শুরু: {len(entries)} package(s)")
            for number, requirement in enumerate(entries, 1):
                # Requirements files may contain pip-wide option directives.
                if requirement.startswith(('--index-url', '--extra-index-url', '--trusted-host',
                                           '--find-links', '--no-index', '--pre')):
                    append_log(server_id, f"ℹ️ Pip option skipped in per-package mode: {requirement}")
                    continue
                append_log(server_id, f"⬇️ [{number}/{len(entries)}] Installing/upgrading: {requirement}")
                try:
                    proc = subprocess.Popen(
                        [sys.executable, '-m', 'pip', 'install', '--upgrade',
                         '--disable-pip-version-check', requirement],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1
                    )
                    for output_line in iter(proc.stdout.readline, ''):
                        if output_line:
                            append_log(server_id, output_line.rstrip())
                    return_code = proc.wait()
                    if return_code == 0:
                        append_log(server_id, f"✅ [{number}/{len(entries)}] Installed: {requirement}")
                    else:
                        append_log(server_id, f"❌ [{number}/{len(entries)}] Failed ({return_code}): {requirement}")
                except Exception as install_error:
                    append_log(server_id, f"❌ Install error for {requirement}: {install_error}")
            append_log(server_id, "🏁 requirements.txt processing completed.")

        threading.Thread(target=install_requirements, daemon=True,
                         name=f"requirements-{server_id}").start()
        return jsonify({'status': 'ok', 'message': 'Requirements installation started',
                        'count': len(entries)})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/uninstall_pkg/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_uninstall_pkg(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Server not found'}), 404
        pkg_type = request.form.get('type')
        pkg_name = request.form.get('name')
        if not pkg_name:
            return jsonify({'error': 'Package name required'}), 400
        cmd = ""
        if pkg_type == 'pip':
            cmd = f"pip uninstall -y {pkg_name}"
        elif pkg_type == 'pkg':
            cmd = f"pkg uninstall -y {pkg_name}"
        elif pkg_type == 'apt':
            cmd = f"apt-get remove -y {pkg_name}"
        elif pkg_type == 'npm':
            cmd = f"npm uninstall -g {pkg_name}"
        else:
            return jsonify({'error': 'Invalid package type'}), 400
        threading.Thread(target=lambda: run_install_command(server_id, cmd), daemon=True).start()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_logs/<server_id>')
@login_required
@check_blocked
def user_get_logs(server_id):
    try:
        if server_id in SERVERS:
            return jsonify({'logs': "\n".join(get_recent_logs(server_id))})
        return jsonify({'logs': ''})
    except:
        return jsonify({'logs': ''})

@app.route('/send_input/<server_id>', methods=['POST'])
@login_required
@check_blocked
def user_send_input(server_id):
    try:
        cmd = request.form.get('command')
        if not cmd:
            return jsonify({'status': 'error', 'message': 'No command provided'})
        if server_id not in SERVERS:
            return jsonify({'status': 'error', 'message': 'Server not found'})
        server = SERVERS[server_id]
        if not server['process']:
            return jsonify({'status': 'error', 'message': 'Process not running'})
        proc = server['process']
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
            append_log(server_id, f"📝 Input: {cmd}")
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error', 'message': 'stdin closed'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/server_info/<server_id>')
@login_required
def server_info(server_id):
    try:
        if server_id not in SERVERS:
            return jsonify({'error': 'Not found'}), 404
        s = SERVERS[server_id]
        uptime = 0
        if is_server_running(s) and s['last_start_time'] > 0:
            uptime = int(time.time() - s['last_start_time'])
        running = is_server_running(s)
        return jsonify({
            'status': 'running' if running else 'stopped',
            'auto_restart': s.get('auto_restart', False),
            'restart_interval': s.get('restart_interval', '1h'),
            'last_start_time': s.get('last_start_time', 0),
                'next_restart_at': s.get('next_restart_at', 0),
                'manual_stop': s.get('manual_stop', False),
            'uptime': uptime
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system_stats')
@login_required
def system_stats():
    try:
        cpu, ram = get_system_stats()
        return jsonify({'cpu': cpu, 'ram': ram})
    except:
        return jsonify({'cpu': 0, 'ram': 0})

@app.route('/create_server', methods=['POST'])
@login_required
@check_blocked
def create_server():
    try:
        server_name = request.form.get('server_name').strip().replace(" ", "_")
        start_command = request.form.get('start_command').strip()
        if not server_name:
            return "Server name required", 400
        if server_name in SERVERS:
            return "Server name already exists", 400
        file = request.files.get('file')
        server_path = os.path.join(UPLOAD_FOLDER, server_name)
        os.makedirs(server_path, exist_ok=True)
        if file and file.filename:
            file_path = os.path.join(server_path, file.filename)
            file.save(file_path)
            if file.filename.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(server_path)
                except:
                    pass
        # Keep servers in the dashboard belonging to the account that created them.
        owner = 'admin' if session.get('is_secret') else 'user'
        SERVERS[server_name] = {
            'process': None,
            'cmd': start_command,
            'cwd': '',
            'logs': [f"🚀 Server '{server_name}' created at {time.strftime('%H:%M:%S')}"],
            'auto_restart': False,  # Auto restart is opt-in
            'restart_interval': '1h',
            'last_start_time': 0,
            'status': 'stopped',
            'path': server_path,
            'owner': owner
        }
        save_servers()
        return redirect(url_for('admin_panel' if owner == 'admin' else 'index'))
    except Exception as e:
        return f"Error: {e}", 500

# --- Keep Alive Ping Endpoint ---
@app.route("/api/ping")
def ping():
    """Keep Alive পিং এন্ডপয়েন্ট - Render-কে সক্রিয় রাখে"""
    return jsonify({
        "status": "alive", 
        "time": time.time(),
        "servers": len(SERVERS),
        "running": sum(1 for s in SERVERS.values() if s.get('status') == 'running')
    })

@app.route("/ping")
def ping_simple():
    return "alive"

@app.route("/json")
def json_alive():
    return jsonify({"status": "alive", "time": time.time()})

# --- Health Check (Render Restart Prevent) ---
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "servers": len(SERVERS),
        "running": sum(1 for s in SERVERS.values() if s.get('status') == 'running'),
        "uptime": time.time() - APP_STARTED_AT
    })

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# --- RUN SERVER ---
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    port = os.environ.get('PORT', 8080)
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print("=" * 50)
    print("SHAPPNO PREMIUM VPS - Starting...")
    print("=" * 50)
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 50)
    print("Admin authentication: configured")
    print("Auto Restart Scheduler: ACTIVE")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
