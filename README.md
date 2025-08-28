<h1 align="center">Morse Code Tool 📻</h1>

<p align="center">
  <strong>A feature-rich, cross-platform desktop application for creating, reading, and translating Morse code.</strong>
  <br><br>
  Developed as a hobby project, this tool provides a complete suite of functionalities for Morse code enthusiasts. It allows you to convert text to audible Morse code, translate Morse from various sources (text, manual input, audio files), and even decode it in real-time.
</p>

<br>

## 📸 Screenshots

<p align="center">
  <img src="https://github.com/KulalMithun/MorseCode-Python-Mini-Project/blob/main/4.png" width="48%">
  <img src="https://github.com/KulalMithun/MorseCode-Python-Mini-Project/blob/main/5.png" width="48%">
  <img src="https://github.com/KulalMithun/MorseCode-Python-Mini-Project/blob/main/6.png" width="48%">
  <br>
  <em>Left: The main menu. Right: The real-time microphone reader with audio visualization.</em>
</p>

<hr>

## ✨ Core Features

<ul>
  <li><strong>Morse Code Creator:</strong>
    <ul>
      <li>Convert plain text into its Morse code representation.</li>
      <li>Play the generated Morse code as audible beeps.</li>
      <li>Save the audio output as a <strong>WAV file</strong> for sharing.</li>
    </ul>
  </li>
  <br>
  <li><strong>Versatile Morse Reader:</strong>
    <ul>
      <li><strong>From Text:</strong> Translate a string of Morse code directly into text.</li>
      <li><strong>Manual Input:</strong> Use "Dot" and "Dash" buttons to manually key in Morse code.</li>
      <li><strong>From Audio File:</strong> Import a <code>.wav</code> file containing Morse code and decode it back into text.</li>
      <li><strong>From Microphone (Advanced):</strong> Listen to a microphone in real-time and decode Morse code as it's being played. Includes a live audio waveform visualization.</li>
    </ul>
  </li>
  <br>
  <li><strong>User-Friendly Interface:</strong>
    <ul>
      <li>Clean, intuitive GUI built with <strong>Tkinter</strong>.</li>
      <li>Multi-window design that guides the user through different functions.</li>
      <li>Non-blocking operations (audio playback, mic listening) using Python's <code>threading</code> to keep the UI responsive.</li>
    </ul>
  </li>
  <br>
  <li><strong>Smart Dependency Handling:</strong>
    <ul>
      <li>Core features work out-of-the-box with a standard Python installation.</li>
      <li>Advanced features (microphone/audio processing) are optional and the application runs smoothly without them, informing the user which libraries are missing.</li>
    </ul>
  </li>
</ul>

<hr>

## 🚀 Getting Started

### Prerequisites

The application is built with Python 3. It has different features depending on which libraries are installed.

1.  **Core Functionality (Required):**
    <ul>
        <li><strong>Python 3.x</strong></li>
    </ul>

2.  **Enhanced Audio Playback (Recommended):**
    <ul>
        <li>The <code>pygame</code> library provides more reliable audio playback for beeps.</li>
    </ul>
    <pre><code>pip install pygame</code></pre>

3.  **Advanced Audio/Microphone Features (Optional):**
    <ul>
        <li>For decoding <code>.wav</code> files and using the live microphone reader, you'll need <code>pyaudio</code>, <code>numpy</code>, and <code>matplotlib</code>.</li>
    </ul>
    <pre><code>pip install pyaudio numpy matplotlib</code></pre>
    <em><strong>Note:</strong> Installing <code>pyaudio</code> may require additional system dependencies (like PortAudio). Please refer to its official installation guide if you encounter issues.</em>

### Installation & Usage

1.  **Download the File:**
    <br>
    Save the `main.py` file to your computer.

2.  **Install Dependencies:**
    <br>
    Open your terminal and install the desired optional libraries as listed above.

3.  **Run the Application:**
    <br>
    Navigate to the directory containing the file and run the script:
    <pre><code>python main.py</code></pre>

4.  **Explore:**
    <br>
    Use the main menu to navigate to the desired function: "Create Morse Code" or "Read Morse Code".

<hr>

## 🛠️ Technical Breakdown

This application demonstrates several key programming concepts using only Python and its rich ecosystem of libraries.

<h4>Key Components:</h4>
<ul>
    <li>
        <strong>GUI Management (<code>MorseCodeApp</code> Class):</strong> The core class that controls the Tkinter root window and manages navigation between different "pages" (Toplevel windows). It handles all UI events and application state.
    </li>
    <li>
        <strong>Audio Generation & Handling:</strong>
        <ul>
            <li>The <code>tone_samples</code> function generates raw audio data (sine waves) for dots and dashes.</li>
            <li>Audio playback is handled by <code>pygame.mixer</code> for low-latency sound, with a fallback to simple <code>time.sleep</code> if pygame is not available.</li>
            <li>The <code>wave</code> module is used for saving and loading <code>.wav</code> files.</li>
        </ul>
    </li>
    <li>
        <strong>Morse Detection Algorithm (<code>detect_morse_from_audio</code>):</strong>
        <ul>
            <li>This function processes raw audio data (from a file or microphone).</li>
            <li>It calculates the signal's energy envelope to distinguish between sound and silence.</li>
            <li>By analyzing the durations of the sounds (beeps) and silences, it determines whether each element is a dot, dash, intra-letter space, inter-letter space, or word space.</li>
        </ul>
    </li>
     <li>
        <strong>Multithreading:</strong> To ensure the GUI remains responsive, long-running tasks like playing a long Morse sequence or listening to the microphone are run in separate threads (using the <code>threading</code> module). A <code>queue</code> is used to safely pass data from the audio processing thread back to the main GUI thread for display.
    </li>
</ul>

<hr>

## 🎓 Project Context

##Todo are based on user feedback

This application was developed as a hobby project and free to use, and i'm open for any collaboration.
