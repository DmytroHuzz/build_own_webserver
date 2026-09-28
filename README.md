# 🧠 Building Your Own Web Server — Educational Repository

This project is part of **Software Foundations**, the first-principles systems work behind [Software in the Grid](https://www.softwareinthegrid.com/).

Welcome to the companion repository for the **“Building Your Own Web Server”** article series — a practical and educational journey through the low-level foundations of web server development.

This repository contains fully working, educational Python implementations of:
- ✅ HTTP message parser
- ⚙️ NGINX-inspired configuration parser
- 🔁 Blocking server with keep-alive support
- 🧵 Multithreaded server with route-based config support

Each part is implemented to match the step-by-step explanations in the articles below.

---

## 📚 Articles Series

1. [**Building Your Own Web Server: Part 1 — Theory and Foundations**](https://dev.to/dmytro_huz/building-your-own-web-server-part-1-theory-and-foundations-3kgo)  
   Learn the core concepts behind web servers, HTTP, and sockets.

2. [**Building Your Own Web Server: Part 2 — Plan and Implementation of HTTP and Configuration Parser**](https://dev.to/dmytro_huz/building-your-own-web-server-part-2-plan-and-implementation-of-http-and-configuration-parser-3lk1)  
   Dive into building reusable, tested components: an HTTP request parser and a configuration loader inspired by NGINX.

3. [**Building Your Own Web Server — Part 3: Blocking Single and Multithreaded Server**](https://dev.to/dmytro_huz/building-your-own-web-server-part-3-blocking-single-and-multithreaded-server-3h7i)  
   Implement, benchmark, and analyze multiple versions of TCP servers — including a multithreaded server with NGINX-style route matching.
   
4. [**Building Your Own Web Server — Part 4: Single-threaded non-blocking server**](https://dev.to/dmytro_huz/building-your-own-web-server-part-4-single-threaded-non-blocking-server-3h5n)
   Implement, benchmark, and analyze server with using non-blocking I/O and event-driven architecture.



## ✨ Educational Focus

This is not production-ready code — and that's intentional.  
The goal is **understanding**, not abstraction. You’ll find:
- 🧱 Modular building blocks
- 🧪 Clear testable units
- 💬 Well-commented Python code
- 📈 Real-world benchmarking with ApacheBench

---

## 💬 Contributions

Feel free to open issues or discussions if you'd like to share thoughts or ask questions.  
And if you're building your own server after this — I’d love to hear about it!

---

## 📩 Author

Created by [Dmytro Huz](https://www.linkedin.com/in/dmitriyhuz/)

Current publication: [Software in the Grid](https://www.softwareinthegrid.com/)

Original web-server article series: [dev.to](https://dev.to/dmytro_huz)
