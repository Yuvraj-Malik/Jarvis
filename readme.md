# 🧠 Jarvis AI Assistant (Python)

![Jarvis Banner](https://img.shields.io/badge/AI-Powered-blue?style=for-the-badge&logo=python) ![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

Jarvis is a modular, voice-activated AI assistant designed to automate system tasks, browse the web, and assist with daily workflows. It leverages **Llama 3 (via Groq)** for high-speed intelligence, with **Gemini 2.0 Flash** for computer vision and fallback logic.

## 🚀 Features

* **🎙️ Fast Voice Interaction:** Uses `SpeechRecognition` for input and `Edge-TTS` for natural-sounding responses.
* **🧠 Triple-Brain Architecture:**
  * **Primary:** Groq (Llama 3.3 70B) for instant, sub-second responses.
  * **Vision:** Gemini 2.0 Flash for analyzing screen content.
  * **Backup:** Mistral AI / Gemini for fail-safe reliability.
* **💻 System Control:**
  * Change Volume & Brightness (Hardware Level).
  * Media Controls (Play/Pause/Next/Prev).
  * Launch Applications & Lock System.
* **🌐 Automation:**
  * **WhatsApp:** Send messages automatically.
  * **YouTube:** Search and play videos instantly.
  * **Web:** Google Search & Website Scraping.
* **📂 Memory & Utilities:**
  * Long-term memory (saves specific details).
  * Mathematical Calculations.
  * System Health Status (CPU/RAM/Battery).

## 🛠️ Architecture

The project is built on a modular "Brain-Body" separation to ensure stability:

* `main.py` - The entry point that listens for the "Jarvis" wake word.
* `brain.py` - The Logic Core. Parses natural language into JSON commands using Llama 3.
* `skills.py` - The Router. Directs commands to the correct tools.
* `toolbox.py` - The Engine. Executes the low-level hardware/web actions.

## 📦 Installation

1. **Clone the Repository**

    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Setup API Keys**
    Create a file named `.env` in the root directory and add your keys:

    ```ini
    GOOGLE_API_KEY=your_gemini_key
    GROQ_API_KEY=your_groq_key
    MISTRAL_API_KEY=your_mistral_key
    ```

    *(Note: The `.env` file is hidden by default and ignored by Git for security.)*

4. **Run Jarvis**

    ```bash
    python main.py
    ```

## 🎮 Usage Examples

* **System:** "Set volume to 50%" or "Set brightness to max".
* **Media:** "Play Blinding Lights on YouTube" or "Pause the music".
* **Web:** "Search Google for the latest tech news".
* **Vision:** "Look at my screen and tell me what this code does".
* **Memory:** "Remember that my meeting is at 5 PM".

## 🛡️ Requirements

* Python 3.10+
* Windows 10/11 (Required for some automation tools like `pycaw`)
* Internet Connection (For API calls)

## 🤝 Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

This project is open-source and available under the MIT License.
