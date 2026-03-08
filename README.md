# Inventory Dashboard

A Java-based desktop application that helps manage and visualize inventory data.
The dashboard connects to an API, retrieves inventory information, and presents it in an easy-to-understand interface.

## Features

* Retrieve inventory data from an API
* Display inventory information in a dashboard interface
* JSON data parsing using `org.json`
* Modular structure with API client and UI components

## Project Structure

```
InventoryDashboard
│
├── src
│   └── client
│       ├── ApiClient.java
│       └── InventoryDashboard.java
│
├── lib
│   └── json.jar
│
├── .gitignore
├── .classpath
└── .project
```

## Technologies Used

* Java
* JSON (`org.json` library)
* REST API integration
* Object-Oriented Programming

## Setup Instructions

1. Clone the repository:

```
git clone https://github.com/YOUR_USERNAME/InventoryDashboard.git
```

2. Open the project in your preferred Java IDE (Eclipse / IntelliJ / VS Code).

3. Make sure the JSON library is added to the project classpath.

4. Run:

```
InventoryDashboard.java
```

## Example Use Case

The application can be used by businesses or developers who want a simple way to monitor inventory levels and retrieve data from an external API.

## Future Improvements

* Add graphical charts for inventory analytics
* Integrate database storage
* Improve UI with JavaFX or Swing enhancements
* Add authentication for API access

## Author

Bhanu Teja Garlapati
